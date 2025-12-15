import streamlit as st
import pdfplumber
import pandas as pd
import plotly.graph_objects as go
import tempfile
import re
import time
from pathlib import Path

from services.ResumeModel import (
    analyze_resume_langgraph,
    display_basic_info_from_resume,
    analyze_job_fit
)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📃",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------- LOAD CSS ----------------
def load_css():
    css_file = Path(__file__).parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ---------------- TITLE ----------------
st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
            AI Resume Analyzer
    </h1>
    <p style='font-size: 1.2em; color: #666; margin-top: 15px;'>
    Upload your resume and get AI-powered feedback tailored to your career goals!
    </p>
    
</div>
""", unsafe_allow_html=True)

# Add link to chatbot page
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("💬 Open Career Assistant", use_container_width=True, type="secondary"):
        st.switch_page("pages/Chatbot.py")

# ---------------- SESSION STATE INIT ----------------
for key in ["resume", "role", "job_description", "allow_mock", "analysis_result", 
            "analysis_signature", "job_match_result"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "allow_mock" else False

# ---------------- INPUTS ----------------
st.markdown("<br>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📄 Upload your resume (PDF or TXT)", 
    type=["pdf", "txt"],
    help="Upload your resume in PDF or TXT format"
)

col1, col2 = st.columns([2, 1])

with col1:
    job_role = st.text_input(
        "🎯 Job Role", 
        value=st.session_state.get('role', '') or '',
        placeholder="e.g., Software Engineer, Data Scientist"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze = st.button("🚀 Analyze", use_container_width=True, type="primary")

job_description = st.text_area(
    "📋 Job Description (Optional - for better match analysis)",
    height=150,
    placeholder="Paste the full job description here for detailed match analysis...",
    value=st.session_state.get('job_description', '') or ''
)

# ---------------- HELPERS ----------------
def make_signature(resume_text, role, jd):
    return hash((resume_text.strip(), role.strip(), jd.strip()))

def extract_text_from_pdf_filelike(file_like):
    text = ""
    try:
        file_like.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_like.getbuffer())
            tmp_path = tmp.name
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
    except:
        text = ""
    return text

def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            return extract_text_from_pdf_filelike(uploaded_file)
        else:
            uploaded_file.seek(0)
            return uploaded_file.getbuffer().tobytes().decode("utf-8", errors="ignore")
    except:
        return ""

# ---------------- ANALYZE ----------------
if analyze:
    if not uploaded_file:
        st.error("⚠️ Please upload a resume file before analyzing.")
        st.stop()
    if not job_role.strip():
        st.error("⚠️ Please enter the job role before analyzing your resume.")
        st.stop()

    file_content = extract_text_from_file(uploaded_file)
    if not file_content.strip():
        st.error("⚠️ File doesn't contain any readable content.")
        st.stop()

    st.session_state.resume = file_content.strip()
    st.session_state.role = job_role.strip()
    st.session_state.job_description = job_description.strip()

    current_signature = make_signature(
        st.session_state.resume,
        st.session_state.role,
        st.session_state.job_description
    )

    if st.session_state.analysis_signature != current_signature:
        with st.spinner("🔍 Analyzing your resume with AI..."):
            try:
                result = analyze_resume_langgraph(
                    st.session_state.resume,
                    st.session_state.role,
                    st.session_state.job_description
                )
                st.session_state.analysis_result = result
                st.session_state.analysis_signature = current_signature
                st.session_state.job_match_result = None
                st.session_state.allow_mock = True
                st.balloons()
                st.success("✅ Analysis complete!")
            except Exception as e:
                st.error(f"Analysis failed: {str(e)[:200]}")
                st.info("💡 Try again in a moment or with a shorter job description.")
                st.stop()

# ---------------- DISPLAY ANALYSIS ----------------
if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ---- BASIC INFO ----
    if uploaded_file and uploaded_file.type == "application/pdf":
        try:
            uploaded_file.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                display_basic_info_from_resume(resume_data=None, pdf_path=tmp.name)
        except:
            pass
    else:
        txt = st.session_state.resume
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", txt)
        phone_match = re.search(r"\+?\d[\d\s\-]{8,15}", txt)
        first_line = next((l.strip() for l in txt.splitlines() if l.strip()), "Not Found")

        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF6B9D 0%, #FFC371 100%); 
                    padding: 30px; border-radius: 25px; color: white; text-align: center;
                    box-shadow: 0 15px 45px rgba(255, 107, 157, 0.4); margin: 20px 0;
                    animation: fadeInUp 0.6s ease;'>
            <h2 style='margin: 0 0 20px 0;'>📋 Resume Analysis</h2>
            <h3 style='margin: 0; font-size: 32px;'>Hello, {first_line}! 👋</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📧 Email: {email_match.group() if email_match else 'Not Found'}")
        with col2:
            st.info(f"📱 Contact: {phone_match.group() if phone_match else 'Not Found'}")

    st.markdown("---")

    # ---- ANIMATED PIE CHART ----
    scores = result.get("Category_Scores", {})
    
    if scores:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown("<h3 style='text-align: center;'>📊 Category-wise Score Distribution</h3>", 
                       unsafe_allow_html=True)
            
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=list(scores.keys()),
                values=list(scores.values()),
                hole=.35,
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=16, family="Inter", color='#2c3e50'),
                marker=dict(
                    colors=['#FF6B9D', '#FFC371', '#A8E6CF', '#56CCF2', '#FFD89B', '#CE93D8', '#84FAB0'],
                    line=dict(color='#FFFFFF', width=3)
                ),
                pull=[0.05] * len(scores),
                hovertemplate='<b>%{label}</b><br>Score: %{value}<br>Percentage: %{percent}<extra></extra>'
            ))
            
            fig.update_layout(
                showlegend=True,
                height=650,
                width=800,
                margin=dict(t=40, b=40, l=40, r=200),
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=14, family="Inter", color='#2c3e50'),
                    bgcolor='rgba(255, 255, 255, 0.95)',
                    bordercolor='#e0e0e0',
                    borderwidth=2
                ),
                font=dict(family="Inter", size=14)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Category scores not available")

    st.markdown("---")

    # ---- SKILL GAP ----
    st.markdown("<h3 style='text-align: center;'>🧩 Skill Gap Analysis</h3>", 
               unsafe_allow_html=True)
    
    resume_skills = list(result.get("resume_skills", []))
    required_skills = list(result.get("job_required_skills", []))
    skills_to_improve = list(result.get("skills_to_improve", []))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Your Skills")
        if resume_skills:
            for skill in resume_skills[:15]:
                st.markdown(f'<div class="skill-badge">🔹 {skill}</div>', unsafe_allow_html=True)
        else:
            st.info("No skills detected - add a skills section to your resume!")
    
    with col2:
        st.markdown("### 🎯 Required Skills")
        if required_skills:
            for skill in required_skills[:15]:
                st.markdown(f'<div class="skill-badge">🎯 {skill}</div>', unsafe_allow_html=True)
        else:
            st.info("Add job description above for skill requirements")
    
    if skills_to_improve:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📌 Priority Skills to Develop")
        cols = st.columns(3)
        for idx, skill in enumerate(skills_to_improve[:12]):
            with cols[idx % 3]:
                st.markdown(f'<div class="medium-item" style="text-align: center; padding: 15px;">➜ **{skill}**</div>', 
                          unsafe_allow_html=True)
    else:
        st.success("✨ Great! You have all the required skills!")

    st.markdown("---")

    # ---- JOB MATCH SCORE ----
    st.markdown("<h3 style='text-align: center;'>🎯 Job Match Score</h3>", 
               unsafe_allow_html=True)

    if st.session_state.job_description:
        if st.session_state.job_match_result is None:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📊 Calculate Job Match Score", type="primary", use_container_width=True):
                    with st.spinner("Calculating match..."):
                        try:
                            time.sleep(3)
                            st.session_state.job_match_result = analyze_job_fit(
                                st.session_state.resume,
                                st.session_state.job_description
                            )
                            st.success("✅ Match calculated!")
                            st.rerun()
                        except Exception as e:
                            st.error("⚠️ Match calculation failed. Try again later.")
                            print(f"Match error: {e}")
        
        if st.session_state.job_match_result:
            job_match = st.session_state.job_match_result
            score = job_match.get("match_score", 0)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if score >= 8:
                    gradient = "linear-gradient(135deg, #84FAB0 0%, #8FD3F4 100%)"
                    emoji = "⭐"
                    label = "Strong Match"
                elif score >= 5:
                    gradient = "linear-gradient(135deg, #FFD89B 0%, #FF9A8B 100%)"
                    emoji = "📊"
                    label = "Moderate Match"
                else:
                    gradient = "linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%)"
                    emoji = "📈"
                    label = "Needs Improvement"
                
                st.markdown(f"""
                <div style='padding: 40px 30px; background: {gradient}; border-radius: 30px;
                            text-align: center; color: white; 
                            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.3); margin: 20px 0;
                            animation: fadeInUp 0.6s ease;'>
                    <h1 style='margin: 0; font-size: 52px;'>{emoji} {round(score, 1)}/10</h1>
                    <p style='margin: 15px 0 0 0; font-size: 20px;'>{label}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.progress(min(score / 10, 1.0))
            st.info(f"💡 **Actionable Tip:** {job_match.get('actionable_tip', 'Keep improving!')}")
    else:
        st.info("💡 Add a job description above to calculate your match score!")

    st.markdown("---")

    # ---- NAVIGATION ----
    st.markdown("<h3 style='text-align: center;'>📋 Explore More Features</h3>", 
               unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Detailed\nAnalysis", use_container_width=True, key="btn1"):
            st.switch_page("pages/DetailedAnalysis.py")
    
    with col2:
        if st.button("📘 Generate\nQ&A", disabled=not st.session_state.allow_mock, 
                    use_container_width=True, key="btn2"):
            st.switch_page("pages/QnA.py")
    
    with col3:
        if st.button("🤖 Mock\nInterview", disabled=not st.session_state.allow_mock, 
                    use_container_width=True, key="btn3"):
            st.switch_page("pages/MockInterview.py")
    
    with col4:
        if st.button("✉️ Cover\nLetter", disabled=not st.session_state.allow_mock, 
                    use_container_width=True, key="btn4"):
            st.switch_page("pages/CoverLetter.py")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if st.button("🔧 Fix My\nResume", disabled=not st.session_state.allow_mock, 
                    use_container_width=True, key="btn5"):
            st.switch_page("pages/FixMyResume.py")
    
    with col6:
        if st.button("💬 Career\nAssistant", use_container_width=True, key="btn6"):
            st.switch_page("pages/Chatbot.py")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")