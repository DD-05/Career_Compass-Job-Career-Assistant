"""
Simple Navigation Component - Back Button Only
Chatbot is now accessible only from Home page
"""

import streamlit as st


def render_back_button():
    """Renders animated back to home button"""
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


def render_page_components():
    """Renders back button - call this in every page except Home"""
    render_back_button()