import streamlit as st
from pathlib import Path
from services.ChatBotModel import chatbot_reply

st.set_page_config(
    page_title="Career Assistant",
    page_icon="💬",
    layout="centered"
)

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Back button
st.markdown("""
<a href="/" target="_self">
    <button class="back-to-home">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.42-1.41L7.83 13H20v-2z"/>
        </svg>
        Home
    </button>
</a>
""", unsafe_allow_html=True)

# ============== ANIMATED TITLE ==============
st.markdown("""
<div style='text-align: center; padding: 40px 0 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
         Career Assistant
    </h1>
    <p style='font-size: 1.3em; color: #666; margin-top: 20px;'>
        Your AI-powered career companion for guidance and support
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "bot_chat_history" not in st.session_state:
    st.session_state.bot_chat_history = []

# Welcome card
if not st.session_state.bot_chat_history:
    st.markdown("""
    <div style='padding: 30px; 
                background: linear-gradient(135deg, #FFE5EC 0%, #FFF9E6 100%);
                border-radius: 25px; 
                margin: 30px 0;
                box-shadow: 0 10px 35px rgba(255, 107, 157, 0.2);
                border: 2px solid rgba(255, 107, 157, 0.2);
                animation: fadeInUp 0.8s ease;'>
        <h2 style='color: #FF6B9D; margin: 0 0 20px 0; font-size: 28px;'>
            👋 Welcome! I'm here to help you succeed
        </h2>
        <div style='background: white; padding: 20px; border-radius: 15px; margin: 15px 0;'>
            <h4 style='color: #56CCF2; margin: 0 0 10px 0;'>💼 I can assist you with:</h4>
            <ul style='margin: 10px 0; padding-left: 25px; color: #555; line-height: 2;'>
                <li><strong>Resume Analysis:</strong> Get feedback on your resume content and structure</li>
                <li><strong>Interview Preparation:</strong> Practice common questions and get tips</li>
                <li><strong>Career Guidance:</strong> Explore career paths and opportunities</li>
                <li><strong>Skill Development:</strong> Learn what skills to focus on</li>
                <li><strong>Job Search Tips:</strong> Strategies for finding the right opportunities</li>
            </ul>
        </div>
        <div style='background: linear-gradient(135deg, #A8E6CF 0%, #56CCF2 100%); 
                    padding: 15px; border-radius: 15px; margin-top: 20px;'>
            <p style='color: white; margin: 0; font-size: 16px; text-align: center;'>
                💡 <strong>Tip:</strong> Ask specific questions for the best guidance!
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Chat container
st.markdown("<br>", unsafe_allow_html=True)

# Display chat history with proper formatting
if st.session_state.bot_chat_history:
    st.markdown("### 💭 Conversation History")
    
    for sender, msg in st.session_state.bot_chat_history:
        if sender == "You":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg)

# Chat input
st.markdown("<br>", unsafe_allow_html=True)

user_message = st.chat_input("💬 Ask me anything about your career journey...")

if user_message:
    # Add user message
    st.session_state.bot_chat_history.append(("You", user_message))
    
    # Get bot response
    with st.spinner("🤔 Thinking..."):
        try:
            response = chatbot_reply(
                user_question=user_message,
                resume=st.session_state.get("resume"),
                role=st.session_state.get("role"),
                job_description=st.session_state.get("job_description")
            )
            
            # Validate response
            if not response or len(response.strip()) < 10:
                response = (
                    "I understand your question! Let me help:\n\n"
                    "For career advice, I recommend:\n"
                    "• Research your target role requirements\n"
                    "• Build relevant skills through practice\n"
                    "• Network with professionals in your field\n"
                    "• Tailor your application materials\n\n"
                    "Could you provide more specific details?"
                )
        except Exception as e:
            response = (
                "I'm experiencing a temporary issue. Here's some quick guidance:\n\n"
                "• Focus on relevant skill development\n"
                "• Practice interview questions\n"
                "• Optimize your resume for ATS\n"
                "• Build a strong portfolio\n\n"
                "Please try asking again in a moment! 😊"
            )
            print(f"Chatbot error: {e}")
    
    # Add bot response
    st.session_state.bot_chat_history.append(("Bot", response))
    st.rerun()

# Action buttons
if st.session_state.bot_chat_history:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.bot_chat_history = []
            st.rerun()
    
    with col2:
        if st.button("📥 Download Chat", use_container_width=True):
            chat_text = "\n\n".join([f"{sender}: {msg}" for sender, msg in st.session_state.bot_chat_history])
            st.download_button(
                label="💾 Save as TXT",
                data=chat_text,
                file_name="career_assistant_chat.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col3:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.switch_page("Home.py")

# Quick question suggestions
st.markdown("---")
st.markdown("### 💡 Quick Questions to Get Started")

suggestions = [
    "How can I improve my resume?",
    "What skills should I learn for [your role]?",
    "How do I prepare for technical interviews?",
    "What's a good career path in [your field]?",
    "How do I negotiate salary?"
]

cols = st.columns(2)
for idx, suggestion in enumerate(suggestions):
    with cols[idx % 2]:
        if st.button(f"💬 {suggestion}", use_container_width=True, key=f"sugg_{idx}"):
            st.session_state.bot_chat_history.append(("You", suggestion))
            
            with st.spinner("🤔 Thinking..."):
                try:
                    response = chatbot_reply(
                        user_question=suggestion,
                        resume=st.session_state.get("resume"),
                        role=st.session_state.get("role"),
                        job_description=st.session_state.get("job_description")
                    )
                    
                    # Validate response
                    if not response or len(response.strip()) < 10:
                        response = "That's a great topic! Could you provide more details about your specific situation?"
                except Exception as e:
                    response = "I'm having a brief issue. Please try the question again in a moment! 😊"
                    print(f"Chatbot error: {e}")
            
            st.session_state.bot_chat_history.append(("Bot", response))
            st.rerun()

# Tips section
st.markdown("---")
st.markdown("### 🎯 Tips for Better Conversations")

tips = [
    ("Be Specific", "Ask detailed questions about particular topics for more helpful answers"),
    ("Provide Context", "Mention your role, experience level, or goals for personalized advice"),
    ("Ask Follow-ups", "Don't hesitate to ask for clarification or more details"),
    ("Stay Career-Focused", "I specialize in career topics like resumes, interviews, and skills")
]

for title, desc in tips:
    st.markdown(f"""
    <div class="suggestion-item" style="margin: 15px 0;">
        <strong style='font-size: 16px; color: #FF6B9D;'>{title}</strong><br>
        <span style='font-size: 14px; color: #666; margin-top: 5px; display: block;'>{desc}</span>
    </div>
    """, unsafe_allow_html=True)