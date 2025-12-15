#  ------------- old claude version without ui ----------
import os
from dotenv import load_dotenv
from services.RateLimiter import rate_limit, cached
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2
)

@rate_limit 
@cached
def generate_cover_letter(resume_text, job_role, company_name=""):
    """
    Generate a simple, professional cover letter.
    
    Args:
        resume_text (str): Full resume content
        job_role (str): Target job role
        company_name (str): Company name (optional)
    
    Returns:
        str: Cover letter text
    """
    
    # Truncate resume if too long
    MAX_CHARS = 8000
    if len(resume_text) > MAX_CHARS:
        resume_text = resume_text[:MAX_CHARS]
    
    company_context = f"at {company_name}" if company_name else ""
    
    prompt = f"""
    Write a professional cover letter for the following candidate applying for {job_role} {company_context}.
    
    CANDIDATE RESUME:
    {resume_text}
    
    REQUIREMENTS:
    - Length: 250-350 words (3 paragraphs)
    - Structure:
      1. Opening: Express interest in the role
      2. Body: Highlight 2-3 key achievements/skills from resume
      3. Closing: Express enthusiasm and next steps
    - Professional and concise tone
    - Start with "Dear Hiring Manager,"
    - End with "Sincerely," (no name needed)
    - DO NOT include address or date
    
    Write ONLY the cover letter content.
    """
    
    response = llm.invoke(prompt)
    return response.content.strip()