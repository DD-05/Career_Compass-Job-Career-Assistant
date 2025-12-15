import streamlit as st
from services.CoverLetterModel import generate_cover_letter
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime

st.set_page_config(page_title="Cover Letter Generator", page_icon="✉️", layout="centered")

st.markdown("""
<div style='text-align: center; padding: 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, rgb(242 226 71) 0%, rgb(255, 195, 113) 100%) text;
    -webkit-text-fill-color: transparent;font-size: 48px;font-weight: 800;margin: 0px;'>
            Cover Letter Generator
    </h1>
    <p style='font-size: 1.2em; color: #666; margin-top: 15px;'>
        Generate a professional cover letter based on your resume
    </p>
</div>
""", unsafe_allow_html=True)

# Check if resume exists
if "resume" not in st.session_state or not st.session_state.resume:
    st.warning("Please analyze your resume first.")
    st.stop()

# Initialize session state
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = None

# Input fields
job_role = st.text_input(
    "Job Role*", 
    value=st.session_state.get('role', ''),
    placeholder="e.g., Software Engineer"
)

company_name = st.text_input(
    "Company Name (Optional)", 
    placeholder="e.g., Google"
)

# Generate button
if st.button("Generate Cover Letter", type="primary", use_container_width=True):
    if not job_role.strip():
        st.error("Please enter a job role.")
    else:
        with st.spinner("Generating your cover letter..."):
            cover_letter = generate_cover_letter(
                resume_text=st.session_state.resume,
                job_role=job_role,
                company_name=company_name
            )
            st.session_state.cover_letter = cover_letter
        st.success("Cover letter generated!")
        st.rerun()

# Display cover letter
if st.session_state.cover_letter:
    st.markdown("---")
    st.subheader("Your Cover Letter")
    
    # Display in text area for easy copying
    st.text_area(
        "Cover Letter",
        value=st.session_state.cover_letter,
        height=400,
        label_visibility="collapsed"
    )
    
    # Function to generate PDF
    def generate_cover_letter_pdf(cover_letter_text, job_role, company_name=""):
        """Generate a professional PDF cover letter"""
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='#2C3E50',
            spaceAfter=30,
            alignment=1
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            spaceAfter=12,
            alignment=0
        )
        
        content = []
        
        # Title
        company_text = f" - {company_name}" if company_name else ""
        title = Paragraph(f"Cover Letter: {job_role}{company_text}", title_style)
        content.append(title)
        content.append(Spacer(1, 0.2 * inch))
        
        # Date
        date_text = datetime.now().strftime("%B %d, %Y")
        date_para = Paragraph(f"<i>{date_text}</i>", body_style)
        content.append(date_para)
        content.append(Spacer(1, 0.3 * inch))
        
        # Cover letter content
        paragraphs = cover_letter_text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                p = Paragraph(para.strip().replace('\n', '<br/>'), body_style)
                content.append(p)
                content.append(Spacer(1, 0.15 * inch))
        
        doc.build(content)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    # Generate PDF data
    pdf_data = generate_cover_letter_pdf(
        st.session_state.cover_letter,
        job_role,
        company_name
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download button
        st.download_button(
            label="📄 Download as PDF",
            data=pdf_data,
            file_name=f"Cover_Letter_{job_role.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        # Clear button
        if st.button("Generate New", use_container_width=True):
            st.session_state.cover_letter = None
            st.rerun()