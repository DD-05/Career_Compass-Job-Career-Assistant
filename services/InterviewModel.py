import os
import json
import re
import time
from dotenv import load_dotenv
from services.RateLimiter import rate_limit, cached
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ============= ENHANCED RATE LIMITING =============
_last_interview_call = 0
_min_interview_interval = 5  # 5 seconds between interview calls

def _rate_limit_interview():
    """Enforce 5 second interval between interview API calls"""
    global _last_interview_call
    current_time = time.time()
    time_since_last = current_time - _last_interview_call
    
    if time_since_last < _min_interview_interval:
        sleep_time = _min_interview_interval - time_since_last
        print(f"⏳ Interview rate limit: waiting {sleep_time:.1f}s")
        time.sleep(sleep_time)
    
    _last_interview_call = time.time()


# Use stable model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-8b",  # Most stable free model
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3,
    request_timeout=30
)

memory = MemorySaver()
agent = create_react_agent(model=llm, tools=[], checkpointer=memory)

# ============= FALLBACK QUESTIONS =============
_FALLBACK_QUESTIONS = {
    "intro": [
        "Tell me about yourself and your experience with {role}.",
        "Walk me through your resume and highlight your most relevant experience.",
        "What interests you about this {role} position?"
    ],
    "technical": [
        "Describe a challenging technical problem you solved recently.",
        "What programming languages and technologies are you most comfortable with?",
        "Tell me about a project you're particularly proud of."
    ],
    "behavioral": [
        "Tell me about a time you worked on a team project. What was your role?",
        "Describe a situation where you had to learn something new quickly.",
        "How do you handle tight deadlines and pressure?"
    ],
    "closing": [
        "Do you have any questions for me about the role or company?",
        "Why should we hire you for this position?",
        "What are your salary expectations?"
    ]
}

_question_count = 0

@rate_limit
def start_interview_langchain(job_role, resume_text):
    """Start interview with enhanced error handling"""
    global _question_count
    _question_count = 0
    
    _rate_limit_interview()
    
    # Truncate resume
    if len(resume_text) > 5000:
        resume_text = resume_text[:5000]
    
    system_prompt = """You are a professional interviewer for a tech company.
    
    Rules:
    - Ask questions about the candidate's resume, experience, and skills
    - Ask behavioral questions about teamwork and problem-solving
    - Ask one question at a time
    - Be professional but friendly
    - After 5-7 questions, conclude with: "Thank you for your time. We will review your application and get back to you soon."
    - Introduce yourself with a professional name
    """
    
    context_prompt = f"""Candidate Information:
    Job Role: {job_role}
    Resume: {resume_text}
    
    Start the interview by introducing yourself and asking the first question about their experience."""
    
    try:
        response = list(agent.stream(
            {"messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_prompt)
            ]},
            {"configurable": {"thread_id": "123"}}
        ))
        
        output = response[0]["agent"]["messages"][0].content
        _question_count += 1
        return output
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ Interview start error: {e}")
        
        # Fallback question
        if any(word in error_msg for word in ["429", "quota", "resource_exhausted"]):
            print("🚨 Using fallback interview question")
        
        _question_count += 1
        return (
            f"Hello! I'm Sarah, and I'll be conducting your interview today for the {job_role} position. "
            f"Let's start with an introduction. {_FALLBACK_QUESTIONS['intro'][0].format(role=job_role)}"
        )

@rate_limit
def continue_interview(candidate_answer):
    """Continue interview with fallback logic"""
    global _question_count
    
    _rate_limit_interview()
    _question_count += 1
    
    # End after 6 questions
    if _question_count >= 6:
        return (
            "Thank you for your detailed responses throughout this interview. "
            "We've covered your technical background, experience, and problem-solving approach. "
            "We will review your application along with today's conversation and get back to you "
            "within the next week. Do you have any final questions for me?"
        )
    
    try:
        response = list(agent.stream(
            {"messages": [HumanMessage(content=candidate_answer)]},
            {"configurable": {"thread_id": "123"}}
        ))
        
        output = response[0]["agent"]["messages"][0].content
        return output
        
    except Exception as e:
        print(f"❌ Interview continue error: {e}")
        
        # Fallback questions based on progress
        if _question_count <= 2:
            questions = _FALLBACK_QUESTIONS['technical']
        elif _question_count <= 4:
            questions = _FALLBACK_QUESTIONS['behavioral']
        else:
            questions = _FALLBACK_QUESTIONS['closing']
        
        idx = (_question_count - 1) % len(questions)
        return (
            "That's interesting. " + questions[idx]
        )

@rate_limit 
@cached
def get_interview_feedback(chat_history, job_role):
    """Generate interview feedback with enhanced fallback"""
    _rate_limit_interview()
    
    # Format conversation (limit tokens)
    conversation = "\n".join([
        f"{speaker}: {text[:150]}" for speaker, text in chat_history[-8:]
    ])
    
    feedback_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-8b",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
        request_timeout=30
    )
    
    prompt = f"""
    Analyze this mock interview and provide feedback.
    
    Job Role: {job_role}
    
    Recent Interview Conversation:
    {conversation}
    
    Return JSON:
    {{
        "communication_score": "X/10",
        "technical_score": "X/10",
        "confidence_score": "X/10",
        "strengths": ["strength1", "strength2", "strength3"],
        "improvements": ["area1", "area2", "area3"],
        "suggestions": ["tip1", "tip2", "tip3"],
        "overall_comment": "2-3 sentence assessment"
    }}
    
    Return ONLY valid JSON.
    """
    
    try:
        response = feedback_llm.invoke(prompt)
        content = response.content.strip()
        cleaned = re.sub(r"```json|```", "", content).strip()
        feedback = json.loads(cleaned)
        
        # Validate required fields
        required = ["communication_score", "technical_score", "confidence_score", 
                   "strengths", "improvements", "suggestions", "overall_comment"]
        for field in required:
            if field not in feedback:
                raise ValueError(f"Missing field: {field}")
        
        return feedback
        
    except Exception as e:
        print(f"❌ Feedback generation error: {e}")
        
        # Analyze based on response length and content
        total_words = sum(len(text.split()) for _, text in chat_history if _ == "Candidate")
        avg_words = total_words / max(len([t for s, t in chat_history if s == "Candidate"]), 1)
        
        # Basic scoring
        if avg_words > 50:
            comm_score = "8/10"
            conf_score = "7/10"
        elif avg_words > 30:
            comm_score = "7/10"
            conf_score = "6/10"
        else:
            comm_score = "6/10"
            conf_score = "5/10"
        
        return {
            "communication_score": comm_score,
            "technical_score": "7/10",
            "confidence_score": conf_score,
            "strengths": [
                "Provided clear responses",
                "Demonstrated relevant experience",
                "Professional communication style"
            ],
            "improvements": [
                "Provide more specific examples with metrics",
                "Demonstrate deeper technical knowledge",
                "Show more enthusiasm and energy"
            ],
            "suggestions": [
                "Practice using the STAR method (Situation, Task, Action, Result)",
                "Research common interview questions for your role",
                "Prepare 5-7 detailed project examples",
                "Practice speaking about technical concepts clearly",
                "Record yourself to improve delivery"
            ],
            "overall_comment": (
                f"Good effort in the {job_role} interview! You communicated your experience well. "
                "Focus on providing more detailed examples with quantifiable results. "
                "With more practice, you'll feel even more confident. Keep preparing!"
            ),
            "note": "Basic feedback provided - detailed AI analysis temporarily unavailable"
        }