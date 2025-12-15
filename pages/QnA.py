import streamlit as st
import pandas as pd
from services.QnAGeneratorModel import generate_qna_from_resume
from services.PdfGenerator import generate_qna_pdf
from pathlib import Path
from chatbot_component import render_page_components

st.set_page_config(page_title="AI Q&A Generator", page_icon="📘", layout="wide")

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Add specific CSS for Q&A display with proper text visibility
st.markdown("""
<style >
/* Ensure Q&A text is always visible */
.qna-question {
    background: linear-gradient(135deg, #e7f3ff 0%, #cfe2ff 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    border-left: 5px solid #2196f3;
}

.qna-question p, .qna-question strong {
    color: #1565c0 !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
}

.qna-answer {
    background: linear-gradient(135deg, #d4edda 0%, #b8e0c7 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    border-left: 5px solid #28a745;
}

.qna-answer p, .qna-answer strong {
    color: #155724 !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
}

/* Fix expander text visibility */
.streamlit-expanderHeader {
    color: #2c3e50 !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    background-color: #ffffff !important;
}

.streamlit-expanderContent p {
    color: #2c3e50 !important;
}
</style>
""", unsafe_allow_html=True)

# Render back button and chatbot
render_page_components()

# ============== ANIMATED TITLE ==============
st.markdown("""
<div style='text-align: center; padding: 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
        AI Interview Q&A Generator
    </h1>
    <p style='font-size: 1.2em; color: #666; margin-top: 15px;'>
        Get tailored interview questions & answers based on your resume and job role
    </p>
</div>
""", unsafe_allow_html=True)

if "resume" not in st.session_state or "role" not in st.session_state:
    st.warning("⚠️ Please analyze your resume first.")
    if st.button("← Go to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

if "qa_set" not in st.session_state:
    st.session_state.qa_set = None

# ============== INPUT SECTION ==============
st.markdown("### QnA Section")

col1, col2 = st.columns([3, 1])
with col1:
    role = st.text_input("🎯 Job Role", value=st.session_state.role, placeholder="e.g., Software Engineer")
with col2:
    num_questions = st.number_input("📊 Number of Q&A", min_value=5, max_value=20, value=10, step=1)

generate_btn = st.button("⚙️ Generate Q&A", use_container_width=True, type="primary")

if generate_btn:
    with st.spinner("🤖 Generating interview questions & answers..."):
        try:
            qna_list = generate_qna_from_resume(st.session_state.resume, role, num_questions)
            st.session_state.qa_set = qna_list
            st.success(f"✅ Generated {len(qna_list)} questions!")
            st.balloons()
        except Exception as e:
            st.error(f"Generation failed: {str(e)[:200]}")
            st.info("💡 Try again in a moment. The AI service might be busy.")

# ============== DISPLAY Q&A ==============
if st.session_state.qa_set:
    st.markdown("---")
    st.markdown("### 🧩 Generated Q&A Set")

    df = pd.DataFrame(st.session_state.qa_set)
    
    # Category-wise display with colors
    categories = df['Category'].unique()
    
    category_colors = {
        'Technical': ('🔵', 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'),
        'DSA': ('🟣', 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'), 
        'Behavioral': ('🟢', 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'),
        'Scenario': ('🟡', 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)')
    }
    
    for category in categories:
        cat_df = df[df['Category'] == category]
        icon, gradient = category_colors.get(category, ('⚪', 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)'))
                
        for i, row in cat_df.iterrows():
            with st.expander(f"Q{i+1}. {row['Question'][:80]}..."):
                # Question
                st.markdown(f"""
                <div class="qna-question">
                    <strong style='font-size: 18px; color: #2196f3;'>📌 Question:</strong><br>
                    <p style='font-size: 16px; margin: 10px 0; line-height: 1.6; color: #1565c0;'>{row['Question']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Answer
                st.markdown(f"""
                <div class="qna-answer">
                    <strong style='font-size: 18px; color: #28a745;'>💡 Answer:</strong><br>
                    <p style='font-size: 16px; margin: 10px 0; line-height: 1.6; color: #155724;'>{row['Answer']}</p>
                </div>
                """, unsafe_allow_html=True)

    # ============== ACTIONS ==============
    st.markdown("---")
    st.markdown("### 📥 Export & Actions")
    
    pdf_data = generate_qna_pdf(df, role)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📄 Download PDF",
            data=pdf_data,
            file_name=f"{role.replace(' ', '_')}_QnA.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.qa_set = None
            st.rerun()
    
    with col3:
        if st.button("🏠 Go to Home", use_container_width=True):
            st.switch_page("Home.py")

# ============== TIPS ==============
st.markdown("---")
st.markdown("### 💡 Interview Preparation Tips")

tips = [
    ("📖 Study Each Question", "Review all generated questions thoroughly and practice your answers out loud."),
    ("🎯 Customize Answers", "Tailor the provided answers to your specific experience and projects."),
    ("⏱️ Practice Timing", "Time yourself - aim for 2-3 minutes per behavioral question, 5-10 minutes for technical."),
    ("🤖 Mock Practice", "Use our Mock Interview feature to practice with AI feedback."),
    ("📝 STAR Method", "For behavioral questions, use Situation, Task, Action, Result framework.")
]

cols = st.columns(2)
for idx, (title, desc) in enumerate(tips):
    with cols[idx % 2]:
        st.markdown(f"""
        <div class="suggestion-item" style="margin: 15px 0;">
            <strong style='font-size: 16px; color: #2c3e50;'>{title}</strong><br>
            <span style='font-size: 14px; color: #666;'>{desc}</span>
        </div>
        """, unsafe_allow_html=True)