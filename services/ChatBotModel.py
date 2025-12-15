import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# ============= ENHANCED RATE LIMITING =============
_last_api_call = 0
_min_call_interval = 5  # 5 SECONDS between calls (increased from 2)
_api_call_count = 0
_max_calls_per_minute = 10  # Maximum 10 calls per minute

# ============= RESPONSE CACHE =============
_response_cache = {}
_cache_max_size = 200  # Increased cache size

# ============= LLM INSTANCE =============
llm = None

def _get_llm():
    """Lazy load LLM only when needed"""
    global llm
    if llm is None:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-8b",  # Most stable free model
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            max_tokens=300,
            request_timeout=30  # Add timeout
        )
    return llm


def _rate_limit_check():
    """Enforce strict rate limiting with quota awareness"""
    global _last_api_call, _api_call_count
    current_time = time.time()
    time_since_last = current_time - _last_api_call
    
    # Enforce minimum interval
    if time_since_last < _min_call_interval:
        sleep_time = _min_call_interval - time_since_last
        print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s")
        time.sleep(sleep_time)
    
    _last_api_call = time.time()
    _api_call_count += 1


def _get_cache_key(question, resume, role, jd):
    """Generate cache key"""
    return hash((
        question.lower().strip()[:100],
        bool(resume), 
        role[:50] if role else "", 
        jd[:50] if jd else ""
    ))


def _get_fallback_response(question_lower):
    """Provide intelligent fallback responses without API calls"""
    
    # Interview preparation
    if "interview" in question_lower:
        return (
            "**Interview Preparation Tips:**\n\n"
            "✅ **Technical Interviews:**\n"
            "• Practice coding problems on LeetCode/HackerRank (start with Easy)\n"
            "• Review core data structures: Arrays, LinkedLists, Trees, Graphs\n"
            "• Study common algorithms: Sorting, Searching, Dynamic Programming\n"
            "• Understand time/space complexity (Big O notation)\n\n"
            "✅ **Behavioral Interviews:**\n"
            "• Use STAR method (Situation, Task, Action, Result)\n"
            "• Prepare 5-7 stories showcasing your skills\n"
            "• Practice answers out loud\n\n"
            "✅ **General Tips:**\n"
            "• Research the company thoroughly\n"
            "• Prepare thoughtful questions to ask\n"
            "• Dress professionally and arrive early\n"
            "• Show enthusiasm and confidence"
        )
    
    # Resume improvement
    elif "resume" in question_lower or "cv" in question_lower:
        return (
            "**Resume Improvement Guide:**\n\n"
            "✅ **Content:**\n"
            "• Use strong action verbs (Led, Developed, Achieved, Implemented)\n"
            "• Quantify achievements with numbers (Increased sales by 30%)\n"
            "• Focus on impact and results, not just duties\n"
            "• Tailor content to match job description keywords\n\n"
            "✅ **Format:**\n"
            "• Keep it to 1-2 pages maximum\n"
            "• Use clear section headers (Experience, Education, Skills, Projects)\n"
            "• Choose a clean, ATS-friendly template\n"
            "• Use consistent formatting and fonts\n\n"
            "✅ **Sections:**\n"
            "• Professional Summary (2-3 lines at top)\n"
            "• Relevant technical skills\n"
            "• Work experience (reverse chronological)\n"
            "• Education and certifications\n"
            "• Notable projects with tech stack"
        )
    
    # Skill development
    elif "skill" in question_lower or "learn" in question_lower:
        return (
            "**Skill Development Strategy:**\n\n"
            "✅ **For Software Engineering:**\n"
            "• Master one programming language deeply (Python/Java/JavaScript)\n"
            "• Learn Git and version control\n"
            "• Understand databases (SQL and NoSQL)\n"
            "• Study system design basics\n"
            "• Practice data structures & algorithms\n\n"
            "✅ **Learning Resources:**\n"
            "• freeCodeCamp (free, comprehensive)\n"
            "• Coursera / edX (structured courses)\n"
            "• YouTube tutorials (The Net Ninja, Traversy Media)\n"
            "• Official documentation (best for deep learning)\n\n"
            "✅ **Practice:**\n"
            "• Build 3-5 portfolio projects\n"
            "• Contribute to open source on GitHub\n"
            "• Do coding challenges daily\n"
            "• Write technical blog posts to solidify learning"
        )
    
    # Job search
    elif "job" in question_lower and ("find" in question_lower or "search" in question_lower):
        return (
            "**Job Search Strategy:**\n\n"
            "✅ **Where to Apply:**\n"
            "• LinkedIn Jobs (set up job alerts)\n"
            "• Company career pages directly\n"
            "• AngelList (for startups)\n"
            "• Indeed, Glassdoor, Naukri\n"
            "• Referrals (most effective!)\n\n"
            "✅ **Application Tips:**\n"
            "• Apply to 10-15 jobs per week consistently\n"
            "• Customize your resume for each application\n"
            "• Write personalized cover letters\n"
            "• Follow up after 1-2 weeks\n\n"
            "✅ **Networking:**\n"
            "• Connect with alumni from your college\n"
            "• Attend tech meetups and conferences\n"
            "• Engage in LinkedIn posts and discussions\n"
            "• Reach out for informational interviews"
        )
    
    # Salary negotiation
    elif "salary" in question_lower or "negotiate" in question_lower:
        return (
            "**Salary Negotiation Tips:**\n\n"
            "✅ **Research:**\n"
            "• Use Glassdoor, Levels.fyi, Payscale for market rates\n"
            "• Consider location, company size, experience level\n"
            "• Know your minimum acceptable salary\n\n"
            "✅ **Timing:**\n"
            "• Never discuss salary in first interview\n"
            "• Wait for offer before negotiating\n"
            "• Let them make the first offer\n\n"
            "✅ **Negotiation:**\n"
            "• Express enthusiasm for the role first\n"
            "• Provide data-backed reasons for your ask\n"
            "• Consider total compensation (benefits, equity, bonus)\n"
            "• Be professional and collaborative\n"
            "• Practice your pitch beforehand\n\n"
            "✅ **Script:** 'I'm very excited about this opportunity! Based on my research and experience level, I was expecting a range of [X-Y]. Is there flexibility in the offer?'"
        )
    
    # Career change/transition
    elif "career change" in question_lower or "switch" in question_lower or "transition" in question_lower:
        return (
            "**Career Transition Guide:**\n\n"
            "✅ **Self-Assessment:**\n"
            "• Identify transferable skills from current role\n"
            "• Research target industry requirements\n"
            "• Set realistic timeline (6-12 months typically)\n\n"
            "✅ **Skill Building:**\n"
            "• Take online courses in target field\n"
            "• Build portfolio projects demonstrating new skills\n"
            "• Get relevant certifications if needed\n"
            "• Consider bootcamps for intensive training\n\n"
            "✅ **Networking:**\n"
            "• Connect with people in target industry\n"
            "• Attend industry meetups and events\n"
            "• Find a mentor in your desired field\n"
            "• Join professional communities\n\n"
            "✅ **Application Strategy:**\n"
            "• Highlight transferable skills prominently\n"
            "• Address career change in cover letter\n"
            "• Consider entry-level or junior positions initially\n"
            "• Be prepared to explain your motivation"
        )
    
    # Default career advice
    else:
        return (
            "**General Career Advice:**\n\n"
            "I'm here to help with:\n"
            "• **Resume/CV optimization** - Improving your resume content and format\n"
            "• **Interview preparation** - Tips for technical and behavioral interviews\n"
            "• **Skill development** - Learning roadmap and resources\n"
            "• **Job search** - Application strategies and networking\n"
            "• **Career planning** - Transitioning roles or advancing your career\n\n"
            "**Quick Tips:**\n"
            "✅ Keep learning - Technology evolves rapidly\n"
            "✅ Build your personal brand - Blog, GitHub, LinkedIn\n"
            "✅ Network actively - 70% of jobs are found through connections\n"
            "✅ Document your achievements - Helps with resume and reviews\n"
            "✅ Seek feedback - Continuous improvement is key\n\n"
            "**Ask me specifically about:**\n"
            "• 'How to prepare for interviews?'\n"
            "• 'How to improve my resume?'\n"
            "• 'What skills should I learn for [role]?'\n"
            "• 'How to find jobs?'\n"
            "• 'How to negotiate salary?'"
        )


def chatbot_reply(user_question, resume=None, role=None, job_description=None):
    """
    Career-focused chatbot with robust error handling and fallbacks
    """
    
    # ============= STEP 1: CHECK CACHE =============
    cache_key = _get_cache_key(user_question, resume, role, job_description)
    if cache_key in _response_cache:
        print("✅ Using cached response")
        return _response_cache[cache_key]
    
    question_lower = user_question.lower().strip()
    
    # ============= STEP 2: GREETINGS (NO API) =============
    greeting_words = ["hi", "hello", "hey", "good morning", "good evening", "greetings"]
    if any(question_lower.startswith(word) for word in greeting_words):
        response = (
            "Hello! 👋 I'm your Career Assistant!\n\n"
            "I can help you with:\n"
            "• Resume improvement & optimization\n"
            "• Job search strategies\n"
            "• Interview preparation tips\n"
            "• Skill development paths\n"
            "• Career planning & guidance\n\n"
            "What would you like to know about your career?"
        )
        _response_cache[cache_key] = response
        return response
    
    # ============= STEP 3: THANK YOU (NO API) =============
    thank_words = ["thank", "thanks", "appreciate"]
    if any(word in question_lower for word in thank_words):
        response = (
            "You're very welcome! 😊\n\n"
            "I'm here to help with your career journey. "
            "Feel free to ask me anything about resumes, interviews, "
            "job search, or skill development!"
        )
        _response_cache[cache_key] = response
        return response
    
    # ============= STEP 4: CAREER KEYWORDS CHECK =============
    career_keywords = [
        "job", "career", "resume", "cv", "interview", "skill", "experience", 
        "work", "professional", "employment", "application", "salary",
        "qualification", "training", "education", "portfolio", "project",
        "technical", "programming", "developer", "engineer", "prepare",
        "improve", "learn", "switch", "transition", "advance", "grow"
    ]
    
    is_career_question = any(keyword in question_lower for keyword in career_keywords)
    
    # ============= STEP 5: BLOCKED TOPICS (NO API) =============
    blocked_topics = [
        "love", "dating", "relationship", "movie", "politics", 
        "religion", "game", "recipe", "weather", "horoscope"
    ]
    
    if not is_career_question and any(topic in question_lower for topic in blocked_topics):
        response = (
            "I'm your Career Assistant 💼\n\n"
            "I specialize in career-related topics:\n"
            "✅ Resume & CV optimization\n"
            "✅ Job search strategies\n"
            "✅ Interview preparation\n"
            "✅ Skills development\n"
            "✅ Career planning\n\n"
            "Please ask me a career-related question!"
        )
        _response_cache[cache_key] = response
        return response

    # ============= STEP 6: TRY API CALL WITH FALLBACK =============
    try:
        _rate_limit_check()
        
        # Minimal context to reduce tokens
        role_context = role[:100] if role else "Not specified"
        
        prompt = f"""You are a friendly Career Assistant helping job seekers.

Target Role: {role_context}

User Question: "{user_question}"

Instructions:
1. Provide helpful, specific career advice
2. Keep response 3-5 sentences
3. Be encouraging and practical
4. Give actionable tips

Your response:"""

        llm_instance = _get_llm()
        response = llm_instance.invoke(prompt)
        result = response.content.strip()
        
        # Validate response
        if not result or len(result) < 20:
            print("⚠️ Empty/short API response, using fallback")
            result = _get_fallback_response(question_lower)
        
        # Cache the response
        if len(_response_cache) >= _cache_max_size:
            _response_cache.pop(next(iter(_response_cache)))
        _response_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ API Error: {e}")
        
        # Handle quota exhaustion
        if any(word in error_msg for word in ["429", "quota", "resource_exhausted", "rate limit"]):
            print("🚨 Quota exhausted - using comprehensive fallback")
            result = _get_fallback_response(question_lower)
            _response_cache[cache_key] = result
            return result
        
        # Other errors - still provide fallback
        else:
            print("⚠️ Other API error - using fallback")
            result = _get_fallback_response(question_lower)
            _response_cache[cache_key] = result
            return result