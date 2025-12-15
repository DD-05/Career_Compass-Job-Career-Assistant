import streamlit as st
import asyncio
import edge_tts
import speech_recognition as sr
from pathlib import Path
from services.InterviewModel import start_interview_langchain, continue_interview, get_interview_feedback
from chatbot_component import render_page_components
import time

st.set_page_config(page_title="AI Mock Interview", page_icon="🤖", layout="centered")

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Render back button
render_page_components()

# ============== ANIMATED TITLE ==============
st.markdown("""
<div style='text-align: center; padding: 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
        AI Mock Interview
    </h1>
    <p style='font-size: 1.2em; color: #666; margin-top: 15px;'>
        Practice with an AI interviewer and receive detailed feedback!
    </p>
</div>
""", unsafe_allow_html=True)

if "allow_mock" not in st.session_state or not st.session_state.allow_mock:
    st.error("⚠️ You must analyze a resume before entering the mock interview.")
    if st.button("← Go to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "interview_isOver" not in st.session_state:
    st.session_state.interview_isOver = False
if "audio_counter" not in st.session_state:
    st.session_state.audio_counter = 0
if "interview_feedback" not in st.session_state:
    st.session_state.interview_feedback = None

# TTS Function with rate limiting
_last_tts_call = 0

async def speak_async(text, filename="qn.mp3", voice="en-GB-RyanNeural", rate="+25%"):
    global _last_tts_call
    current_time = time.time()
    if current_time - _last_tts_call < 1:
        await asyncio.sleep(1 - (current_time - _last_tts_call))
    
    try:
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        await communicate.save(filename)
        _last_tts_call = time.time()
        return True
    except Exception as e:
        print(f"TTS Error: {e}")
        return False

def speak_sync(text, filename="qn.mp3"):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(speak_async(text, filename))
        loop.close()
        return success
    except:
        return False

# Speech Recognition
def get_audio_input():
    r = sr.Recognizer()
    r.energy_threshold = 4000
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.0
    
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak clearly and pause when done...")
            with st.spinner("Calibrating..."):
                r.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = r.listen(source, timeout=3, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                st.error("⚠️ No speech detected. Try again.")
                return ""
        
        st.info("Processing...")
        try:
            text = r.recognize_google(audio, language="en-US")
            st.success(f"✓ You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("⚠️ Could not understand. Speak more clearly.")
            return ""
        except sr.RequestError:
            st.error("⚠️ Recognition service error.")
            return ""
    except Exception as e:
        st.error(f"⚠️ Microphone error: {e}")
        return ""

# ============== START INTERVIEW ==============
if not st.session_state.interview_active and not st.session_state.interview_feedback:
    st.markdown("### 🎯 Interview Setup")
    
    role = st.text_input(
        "Enter the job role:",
        value=st.session_state.get('role', ''),
        placeholder="e.g., Software Engineer"
    )
    
    if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
        if role.strip():
            with st.spinner("Starting interview..."):
                try:
                    first_q = start_interview_langchain(role.strip(), st.session_state.resume.strip())
                    st.session_state.chat_history = [("Interviewer", first_q)]
                    st.session_state.interview_active = True
                    st.session_state.interview_isOver = False
                    st.session_state.interview_feedback = None
                    st.session_state.audio_counter += 1
                    
                    filename = f"qn_{st.session_state.audio_counter}.mp3"
                    speak_sync(first_q, filename)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {e}")
        else:
            st.warning("⚠️ Please enter a role first.")

# ============== INTERVIEW IN PROGRESS ==============
if st.session_state.interview_active and not st.session_state.interview_feedback:
    st.markdown("---")
    st.markdown("### 💬 Interview Conversation")

    # Display conversation
    for speaker, text in st.session_state.chat_history:
        if speaker == "Interviewer":
            with st.chat_message("assistant", avatar="🧑‍💼"):
                st.write(text)
        else:
            with st.chat_message("user", avatar="👤"):
                st.write(text)

    # Play audio
    if st.session_state.chat_history and st.session_state.chat_history[-1][0] == "Interviewer":
        audio_file = f"qn_{st.session_state.audio_counter}.mp3"
        try:
            st.audio(audio_file, autoplay=True)
        except:
            pass

    # Input Options
    if not st.session_state.interview_isOver:
        st.markdown("---")
        st.markdown("### 💭 Your Response")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🎤 Record Answer", use_container_width=True):
                candidate_answer = get_audio_input()
                if candidate_answer:
                    st.session_state.chat_history.append(("Candidate", candidate_answer))
                    with st.spinner("AI is thinking..."):
                        time.sleep(2)
                        reply = continue_interview(candidate_answer)
                    st.session_state.chat_history.append(("Interviewer", reply))
                    st.session_state.audio_counter += 1
                    filename = f"qn_{st.session_state.audio_counter}.mp3"
                    speak_sync(reply, filename)
                    
                    if any(phrase in reply.lower() for phrase in ["not selected", "selected", "moving forward", "we will not"]):
                        st.session_state.interview_isOver = True
                    st.rerun()
        
        with col2:
            manual_answer = st.text_input("Or type:", key="manual_input", label_visibility="collapsed", placeholder="Type your answer...")
            if st.button("📤 Send", use_container_width=True) and manual_answer:
                st.session_state.chat_history.append(("Candidate", manual_answer))
                with st.spinner("AI thinking..."):
                    time.sleep(2)
                    reply = continue_interview(manual_answer)
                st.session_state.chat_history.append(("Interviewer", reply))
                st.session_state.audio_counter += 1
                filename = f"qn_{st.session_state.audio_counter}.mp3"
                speak_sync(reply, filename)
                
                if any(phrase in reply.lower() for phrase in ["not selected", "selected", "moving forward", "we will not"]):
                    st.session_state.interview_isOver = True
                st.rerun()
        
        with col3:
            if st.button("🛑 Stop", use_container_width=True, type="secondary"):
                st.session_state.interview_isOver = True
                st.rerun()

    # Generate Feedback
    if st.session_state.interview_isOver and not st.session_state.interview_feedback:
        with st.spinner("📊 Generating detailed feedback..."):
            time.sleep(2)
            feedback = get_interview_feedback(
                st.session_state.chat_history,
                st.session_state.get('role', 'Unknown Role')
            )
            st.session_state.interview_feedback = feedback
        st.rerun()

# ============== DISPLAY FEEDBACK ==============
if st.session_state.interview_feedback:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h2 style='background: linear-gradient(135deg, #84FAB0 0%, #8FD3F4 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 2.5em; font-weight: 800; margin: 0;'>
            📊 Interview Feedback & Summary
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    feedback = st.session_state.interview_feedback
    
    # Overall Performance
    st.markdown("### 🎯 Overall Performance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        comm_score = feedback.get('communication_score', 'N/A')
        st.markdown(f"""
        <div style='padding: 30px 20px; background: linear-gradient(135deg, #A1C4FD 0%, #C2E9FB 100%);
                    border-radius: 25px; text-align: center; color: white;
                    box-shadow: 0 8px 30px rgba(161, 196, 253, 0.4);
                    animation: fadeInUp 0.6s ease;'>
            <h3 style='margin: 0; font-size: 16px;'>Communication</h3>
            <h1 style='margin: 15px 0 0 0; font-size: 48px; font-weight: 800;'>{comm_score}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tech_score = feedback.get('technical_score', 'N/A')
        st.markdown(f"""
        <div style='padding: 30px 20px; background: linear-gradient(135deg, #FF6B9D 0%, #FFC371 100%);
                    border-radius: 25px; text-align: center; color: white;
                    box-shadow: 0 8px 30px rgba(255, 107, 157, 0.4);
                    animation: fadeInUp 0.8s ease;'>
            <h3 style='margin: 0; font-size: 16px;'>Technical Skills</h3>
            <h1 style='margin: 15px 0 0 0; font-size: 48px; font-weight: 800;'>{tech_score}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        conf_score = feedback.get('confidence_score', 'N/A')
        st.markdown(f"""
        <div style='padding: 30px 20px; background: linear-gradient(135deg, #FFD89B 0%, #FF9A8B 100%);
                    border-radius: 25px; text-align: center; color: white;
                    box-shadow: 0 8px 30px rgba(255, 216, 155, 0.4);
                    animation: fadeInUp 1s ease;'>
            <h3 style='margin: 0; font-size: 16px;'>Confidence</h3>
            <h1 style='margin: 15px 0 0 0; font-size: 48px; font-weight: 800;'>{conf_score}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Strengths
    st.markdown("### ✅ Strengths")
    for strength in feedback.get('strengths', []):
        st.markdown(f'<div class="strength-item">✓ {strength}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Areas to Improve
    st.markdown("### ⚠️ Areas to Improve")
    for area in feedback.get('improvements', []):
        st.markdown(f'<div class="medium-item">→ {area}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Key Suggestions
    st.markdown("### 💡 Key Suggestions")
    for idx, suggestion in enumerate(feedback.get('suggestions', []), 1):
        st.markdown(f'<div class="suggestion-item"><strong>{idx}.</strong> {suggestion}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Overall Comment
    st.markdown("### 📝 Summary")
    st.info(feedback.get('overall_comment', 'Great effort! Keep practicing.'))
    
    # Reset Button
    st.markdown("---")
    if st.button("🔄 Start New Interview", use_container_width=True, type="primary"):
        st.session_state.chat_history = []
        st.session_state.interview_active = False
        st.session_state.interview_isOver = False
        st.session_state.interview_feedback = None
        st.session_state.audio_counter = 0
        st.rerun()

# ============== TIPS ==============
if not st.session_state.interview_active:
    st.markdown("---")
    st.markdown("### 💡 Interview Tips")

    tips = [
        ("🎯 Research the Company", "Learn about the company's mission, values, and recent news."),
        ("📖 Prepare STAR Stories", "Use Situation, Task, Action, Result for behavioral questions."),
        ("💭 Think Before You Speak", "Take a moment to organize your thoughts before answering."),
        ("😊 Show Enthusiasm", "Express genuine interest in the role and company."),
        ("❓ Ask Questions", "Prepare thoughtful questions to ask the interviewer.")
    ]

    cols = st.columns(2)
    for idx, (title, desc) in enumerate(tips):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="suggestion-item" style="margin: 15px 0;">
                <strong style='font-size: 16px;'>{title}</strong><br>
                <span style='font-size: 14px; color: #666;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)