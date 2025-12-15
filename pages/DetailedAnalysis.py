import streamlit as st
from pathlib import Path
from chatbot_component import render_page_components

st.set_page_config(
    page_title="Detailed Analysis",
    page_icon="📊",
    layout="centered"
)

# Load CSS
def load_css():
    css_file = Path(__file__).parent.parent / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Render back button
render_page_components()

# Check if analysis exists
if "analysis_result" not in st.session_state or not st.session_state.analysis_result:
    st.warning("⚠️ Please analyze your resume first from the Home page.")
    if st.button("← Go to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

result = st.session_state.analysis_result

# ============== ANIMATED TITLE ==============
st.markdown("""
<div style='text-align: center; padding: 20px 0; animation: fadeInUp 0.6s ease;'>
    <h1 style='background: linear-gradient(135deg, #FF6B9D 0%, #FFC371 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-size: 3em; font-weight: 800; margin: 0;'>
        📊 Detailed Analysis
    </h1>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**🎯 Target Role:** {st.session_state.get('role', 'N/A')}")

# ============== OVERALL SCORE WITH GRADIENT ==============
overall_score = result.get('Overall_Score', 0)

if overall_score >= 80:
    score_color = "linear-gradient(135deg, #84FAB0 0%, #8FD3F4 100%)"
    score_emoji = "🌟"
    score_label = "Excellent"
elif overall_score >= 60:
    score_color = "linear-gradient(135deg, #A8E6CF 0%, #56CCF2 100%)"
    score_emoji = "⭐"
    score_label = "Good"
elif overall_score >= 40:
    score_color = "linear-gradient(135deg, #FFD89B 0%, #FF9A8B 100%)"
    score_emoji = "📊"
    score_label = "Fair"
else:
    score_color = "linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%)"
    score_emoji = "📈"
    score_label = "Needs Work"

st.markdown(f"""
<div style='padding: 40px; background: {score_color}; border-radius: 30px; 
            text-align: center; color: white; box-shadow: 0 15px 45px rgba(0, 0, 0, 0.3);
            margin: 30px 0; position: relative; overflow: hidden;
            animation: fadeInUp 0.8s ease;'>
    <div style='position: relative; z-index: 1;'>
        <h1 style='margin: 0; font-size: 72px; font-weight: 900;'>{score_emoji} {overall_score}/100</h1>
        <p style='margin: 15px 0 0 0; font-size: 24px; font-weight: 600;'>{score_label} Resume Score</p>
    </div>
    <div style='position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: shimmer 3s infinite;'></div>
</div>

<style>
@keyframes shimmer {{
    0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0; }}
    50% {{ transform: translate(0%, 0%) scale(1.5); opacity: 1; }}
}}
</style>
""", unsafe_allow_html=True)

st.markdown("---")

# ============== STRENGTHS ==============
st.markdown("### ✅ Key Strengths")
st.markdown("<p style='color: #666; margin-bottom: 20px;'>These are the strong points in your resume:</p>", unsafe_allow_html=True)

strengths = result.get("Strengths", [])
if strengths:
    for idx, strength in enumerate(strengths[:5], 1):
        st.markdown(f"""
        <div class="strength-item fade-in-up" style="animation-delay: {idx * 0.1}s;">
            <strong style='font-size: 18px;'>✓</strong> {strength}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No significant strengths identified.")

st.markdown("---")

# ============== WEAKNESSES ==============
st.markdown("### ⚠️ Areas to Improve")
st.markdown("<p style='color: #666; margin-bottom: 20px;'>Focus on these areas to strengthen your resume:</p>", unsafe_allow_html=True)

weaknesses = result.get("Weaknesses", {})

if weaknesses.get("Critical"):
    st.markdown("#### 🔴 Critical Issues (Fix Immediately)")
    for idx, item in enumerate(weaknesses["Critical"][:3], 1):
        st.markdown(f"""
        <div class="critical-item fade-in-up" style="animation-delay: {idx * 0.1}s;">
            <strong style='font-size: 18px;'>!</strong> {item}
        </div>
        """, unsafe_allow_html=True)

if weaknesses.get("Medium"):
    st.markdown("#### 🟡 Medium Priority")
    for idx, item in enumerate(weaknesses["Medium"][:3], 1):
        st.markdown(f"""
        <div class="medium-item fade-in-up" style="animation-delay: {(idx + 3) * 0.1}s;">
            <strong style='font-size: 18px;'>→</strong> {item}
        </div>
        """, unsafe_allow_html=True)

if weaknesses.get("Low"):
    st.markdown("#### 🟢 Low Priority (Optional)")
    for idx, item in enumerate(weaknesses["Low"][:2], 1):
        st.markdown(f"""
        <div class="suggestion-item fade-in-up" style="animation-delay: {(idx + 6) * 0.1}s;">
            <strong style='font-size: 18px;'>•</strong> {item}
        </div>
        """, unsafe_allow_html=True)

if not weaknesses.get("Critical") and not weaknesses.get("Medium"):
    st.success("✨ Great! No major weaknesses found.")

st.markdown("---")

# ============== SUGGESTIONS ==============
st.markdown("### 💡 Action Plan")
st.markdown("<p style='color: #666; margin-bottom: 20px;'>Follow these steps to improve your resume:</p>", unsafe_allow_html=True)

suggestions = result.get("Suggestions", {})

all_suggestions = []

if suggestions.get("Critical"):
    for item in suggestions["Critical"][:2]:
        all_suggestions.append(("🔴 High Priority", item, "#FF9A9E"))

if suggestions.get("Medium"):
    for item in suggestions["Medium"][:3]:
        all_suggestions.append(("🟡 Medium Priority", item, "#FFD89B"))

if suggestions.get("Low"):
    for item in suggestions["Low"][:2]:
        all_suggestions.append(("🟢 Optional", item, "#84FAB0"))

if all_suggestions:
    for idx, (priority, suggestion, color) in enumerate(all_suggestions, 1):
        st.markdown(f"""
        <div class="suggestion-item fade-in-up" style="animation-delay: {idx * 0.1}s; border-left-color: {color};">
            <strong style='font-size: 18px; color: {color};'>{idx}. {priority}</strong><br>
            <span style='font-size: 16px; margin-top: 8px; display: block;'>{suggestion}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✨ Your resume looks excellent!")

st.markdown("---")

# ============== SUMMARY METRICS ==============
st.markdown("### 📈 Quick Summary")

col1, col2, col3 = st.columns(3)

with col1:
    strength_count = len(strengths)
    st.markdown(f"""
    <div style='padding: 30px 20px; background: linear-gradient(135deg, #84FAB0 0%, #8FD3F4 100%);
                border-radius: 25px; text-align: center; color: white;
                box-shadow: 0 8px 30px rgba(132, 250, 176, 0.4);
                transition: all 0.3s ease; animation: fadeInUp 1s ease;'>
        <h3 style='margin: 0; font-size: 18px;'>Strengths</h3>
        <h1 style='margin: 15px 0 10px 0; font-size: 56px; font-weight: 800;'>{strength_count}</h1>
        <p style='margin: 0; font-size: 16px; opacity: 0.9;'>{'Great!' if strength_count > 3 else 'Build More'}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_weaknesses = len(weaknesses.get("Critical", [])) + len(weaknesses.get("Medium", []))
    st.markdown(f"""
    <div style='padding: 30px 20px; background: linear-gradient(135deg, #FFD89B 0%, #FF9A8B 100%);
                border-radius: 25px; text-align: center; color: white;
                box-shadow: 0 8px 30px rgba(255, 216, 155, 0.4);
                transition: all 0.3s ease; animation: fadeInUp 1.2s ease;'>
        <h3 style='margin: 0; font-size: 18px;'>Improvements</h3>
        <h1 style='margin: 15px 0 10px 0; font-size: 56px; font-weight: 800;'>{total_weaknesses}</h1>
        <p style='margin: 0; font-size: 16px; opacity: 0.9;'>{'Focus Here' if total_weaknesses > 0 else 'Perfect!'}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    action_count = len(all_suggestions)
    st.markdown(f"""
    <div style='padding: 30px 20px; background: linear-gradient(135deg, #FF6B9D 0%, #FFC371 100%);
                border-radius: 25px; text-align: center; color: white;
                box-shadow: 0 8px 30px rgba(255, 107, 157, 0.4);
                transition: all 0.3s ease; animation: fadeInUp 1.4s ease;'>
        <h3 style='margin: 0; font-size: 18px;'>Action Items</h3>
        <h1 style='margin: 15px 0 10px 0; font-size: 56px; font-weight: 800;'>{action_count}</h1>
        <p style='margin: 0; font-size: 16px; opacity: 0.9;'>{'Start Now' if action_count > 0 else 'All Set!'}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============== NAVIGATION ==============
st.markdown("### 🚀 Next Steps")
st.markdown("<p style='color: #666; margin-bottom: 20px;'>Choose your next action:</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Overview", use_container_width=True):
        st.switch_page("Home.py")

with col2:
    if st.button("📘 Generate Q&A", use_container_width=True):
        st.switch_page("pages/QnA.py")

with col3:
    if st.button("🔧 Fix Resume", use_container_width=True):
        st.switch_page("pages/FixMyResume.py")

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    if st.button("🤖 Mock Interview", use_container_width=True):
        st.switch_page("pages/MockInterview.py")

with col5:
    if st.button("✉️ Cover Letter", use_container_width=True):
        st.switch_page("pages/CoverLetter.py")

with col6:
    if st.button("💬 Career Chat", use_container_width=True):
        st.switch_page("pages/Chatbot.py")