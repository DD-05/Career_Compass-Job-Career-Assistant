import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from services.ResumeModel import analyze_resume_langgraph, analyze_job_fit
from pathlib import Path
from chatbot_component import render_page_components
import time

load_dotenv()

st.set_page_config(page_title="Fix My Resume", page_icon="🔧", layout="centered")

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Render back button and chatbot
render_page_components()

# ============== ANIMATED TITLE ==============
st.markdown("""
<div style='text-align: center; padding: 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
        AI Resume Improver
    </h1>
    <p style='font-size: 1.2em; color: #666; margin-top: 15px;'>
        Get AI-powered suggestions to enhance your resume professionally
    </p>
</div>
""", unsafe_allow_html=True)

# Check if resume exists
if "resume" not in st.session_state or not st.session_state.resume:
    st.warning("⚠️ Please analyze your resume first.")
    if st.button("← Go to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# Initialize session state
if "fixed_resume" not in st.session_state:
    st.session_state.fixed_resume = None
if "fix_suggestions" not in st.session_state:
    st.session_state.fix_suggestions = None
if "original_score" not in st.session_state:
    st.session_state.original_score = None
if "improved_score" not in st.session_state:
    st.session_state.improved_score = None
if "auto_analyzing" not in st.session_state:
    st.session_state.auto_analyzing = False

# Store original scores
if st.session_state.analysis_result and st.session_state.original_score is None:
    st.session_state.original_score = {
        'overall': st.session_state.analysis_result.get('Overall_Score', 0),
        'match': st.session_state.job_match_result.get('match_score', 0) if st.session_state.job_match_result else 0
    }

# ============== CURRENT STATUS ==============
st.markdown("### 📊 Current Resume Status")

st.info(f"**🎯 Target Role:** {st.session_state.get('role', 'Not specified')}")

if st.session_state.original_score:
    col1, col2 = st.columns(2)
    with col1:
        score = st.session_state.original_score['overall']
        st.markdown(f"""
        <div style='padding: 25px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);'>
            <h3 style='margin: 0; font-size: 16px;'>Current Score</h3>
            <h1 style='margin: 15px 0 0 0; font-size: 48px; font-weight: 800;'>{score}/100</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        match = st.session_state.original_score['match']
        st.markdown(f"""
        <div style='padding: 25px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border-radius: 20px; text-align: center; color: white;
                    box-shadow: 0 8px 25px rgba(240, 147, 251, 0.4);'>
            <h3 style='margin: 0; font-size: 16px;'>Match Score</h3>
            <h1 style='margin: 15px 0 0 0; font-size: 48px; font-weight: 800;'>{match:.1f}/10</h1>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Rate-limited LLM
_last_llm_call = 0

def rate_limited_llm_invoke(prompt, min_interval=3):
    """Call LLM with rate limiting"""
    global _last_llm_call
    current_time = time.time()
    time_since_last = current_time - _last_llm_call
    
    if time_since_last < min_interval:
        time.sleep(min_interval - time_since_last)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2
    )
    
    _last_llm_call = time.time()
    return llm.invoke(prompt)

# Fix resume function
def fix_resume_with_ai(resume_text, role, job_description=""):
    prompt = f"""
    You are an expert resume writer. Rewrite this resume to be professional, ATS-friendly, and impactful.
    
    Current Resume: {resume_text[:8000]}
    Target Role: {role}
    Job Description: {job_description[:2000] if job_description else "Not provided"}
    
    Instructions:
    1. Improve formatting with clear sections
    2. Use strong action verbs (Led, Developed, Achieved)
    3. Add quantifiable metrics where possible
    4. Optimize for ATS with relevant keywords
    5. Highlight achievements over responsibilities
    6. Keep information accurate but present it better
    7. Make bullet points concise and impactful
    
    Return the improved resume as plain text with clear sections.
    """
    
    response = rate_limited_llm_invoke(prompt)
    return response.content.strip()

def generate_fix_suggestions(original_resume, fixed_resume):
    prompt = f"""
    Compare these resumes and list TOP 5 improvements made.
    
    Original: {original_resume[:3000]}
    Improved: {fixed_resume[:3000]}
    
    Return 5 bullet points starting with "• "
    """
    
    response = rate_limited_llm_invoke(prompt)
    return response.content.strip()

# ============== GENERATE IMPROVED RESUME ==============
st.markdown("### 🚀 Improve Your Resume")

if st.button("🔧 Improve Resume with AI", use_container_width=True, type="primary"):
    with st.spinner("🤖 AI is improving your resume..."):
        try:
            fixed = fix_resume_with_ai(
                st.session_state.resume,
                st.session_state.get('role', ''),
                st.session_state.get('job_description', '')
            )
            st.session_state.fixed_resume = fixed
            
            suggestions = generate_fix_suggestions(
                st.session_state.resume,
                fixed
            )
            st.session_state.fix_suggestions = suggestions
            st.success("✅ Resume improved!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)[:200]}")
            st.info("💡 Try again in a moment. The AI service might be busy.")

# ============== DISPLAY IMPROVED RESUME ==============
if st.session_state.fixed_resume:
    st.markdown("---")
    st.markdown("### ✨ Your Improved Resume")
    
    if st.session_state.fix_suggestions:
        with st.expander("📋 Key Improvements Made", expanded=True):
            st.markdown(f"""
            <div class="strength-item">
                {st.session_state.fix_suggestions.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
    
    # Display improved resume
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); 
                padding: 30px; border-radius: 20px; 
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
                border-left: 6px solid #11998e;
                margin: 20px 0;'>
    """, unsafe_allow_html=True)
    
    st.text_area(
        "Improved Resume",
        value=st.session_state.fixed_resume,
        height=400,
        label_visibility="collapsed"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Generate PDF function
    def generate_resume_pdf(resume_text, role):
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            spaceBefore=16,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        content = []
        sections = resume_text.split('\n\n')
        
        for section in sections:
            if section.strip():
                lines = section.split('\n')
                first_line = lines[0].strip()
                common_headings = ['SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 
                                 'CERTIFICATIONS', 'ACHIEVEMENTS', 'CONTACT']
                
                is_heading = (first_line.isupper() or 
                            any(heading in first_line.upper() for heading in common_headings))
                
                if is_heading:
                    content.append(Paragraph(first_line, heading_style))
                    if len(lines) > 1:
                        body_text = '<br/>'.join(lines[1:])
                        content.append(Paragraph(body_text, body_style))
                else:
                    body_text = '<br/>'.join(lines)
                    content.append(Paragraph(body_text, body_style))
                
                content.append(Spacer(1, 0.1 * inch))
        
        doc.build(content)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    # ============== ACTION BUTTONS ==============
    st.markdown("### 📥 Next Steps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pdf_data = generate_resume_pdf(
            st.session_state.fixed_resume,
            st.session_state.get('role', 'Resume')
        )
        
        st.download_button(
            label="📄 Download PDF",
            data=pdf_data,
            file_name=f"Improved_Resume.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        if st.button("✅ Use & Re-analyze", use_container_width=True, type="primary"):
            st.session_state.auto_analyzing = True
            st.rerun()

# ============== AUTO-ANALYZE ==============
if st.session_state.auto_analyzing:
    with st.spinner("🔄 Analyzing your improved resume..."):
        try:
            # Update to fixed resume
            st.session_state.resume = st.session_state.fixed_resume
            
            # Re-analyze
            new_analysis = analyze_resume_langgraph(
                st.session_state.fixed_resume,
                st.session_state.role,
                st.session_state.job_description
            )
            
            # Calculate new job match
            new_job_match = None
            if st.session_state.job_description:
                time.sleep(2)  # Rate limiting
                new_job_match = analyze_job_fit(
                    st.session_state.fixed_resume,
                    st.session_state.job_description
                )
            
            # Store improved scores
            st.session_state.improved_score = {
                'overall': new_analysis.get('Overall_Score', 0),
                'match': new_job_match.get('match_score', 0) if new_job_match else 0
            }
            
            # Update session state
            st.session_state.analysis_result = new_analysis
            st.session_state.job_match_result = new_job_match
            st.session_state.analysis_signature = None
            
            # Calculate improvements
            score_improvement = st.session_state.improved_score['overall'] - st.session_state.original_score['overall']
            match_improvement = st.session_state.improved_score['match'] - st.session_state.original_score['match']
            
            st.success("✅ Fixed resume is now active!")
            
            st.markdown("### 📊 Score Comparison")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Overall Score",
                    f"{st.session_state.improved_score['overall']}/100",
                    f"+{score_improvement}" if score_improvement > 0 else f"{score_improvement}"
                )
            with col2:
                st.metric(
                    "Match Score",
                    f"{st.session_state.improved_score['match']:.1f}/10",
                    f"+{match_improvement:.1f}" if match_improvement > 0 else f"{match_improvement:.1f}"
                )
            
            if score_improvement > 0 or match_improvement > 0:
                st.balloons()
                st.success(f"🎉 Improved by {score_improvement} points overall!")
            
            st.session_state.auto_analyzing = False
            
            time.sleep(2)
            st.switch_page("Home.py")
            
        except Exception as e:
            st.error(f"Analysis error: {str(e)[:200]}")
            st.info("💡 Try again in a moment.")
            st.session_state.auto_analyzing = False
    
    if st.button("🔄 Generate Different Version", use_container_width=True):
        st.session_state.fixed_resume = None
        st.session_state.fix_suggestions = None
        st.rerun()

# ============== TIPS ==============
st.markdown("---")
st.markdown("### 💡 Resume Improvement Tips")

tips = [
    ("🎯 Use Action Verbs", "Start bullet points with strong verbs like 'Led', 'Developed', 'Increased'."),
    ("📊 Quantify Achievements", "Add numbers and metrics: 'Increased sales by 30%' vs 'Increased sales'."),
    ("🔑 Include Keywords", "Use keywords from the job description naturally in your resume."),
    ("✂️ Be Concise", "Aim for 1-2 pages. Remove outdated or irrelevant information."),
    ("🎨 Format Professionally", "Use consistent formatting, clear headers, and proper spacing.")
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