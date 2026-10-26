# 🧭 Career Compass: AI-Powered Career Assistant & Mock Interviewer

**Career Compass** is an intelligent career acceleration platform built with **Streamlit** and powered by **Google Gemini**. The application provides an end-to-end interview and job-hunt preparation suite featuring a voice-driven interactive mock interviewer alongside an automated resume analyzer equipped with in-memory caching and request rate limiting.

---

## 🌟 Key Features

* **Voice-Interactive Mock Interviews:** Simulates live technical and behavioral interviews using real-time Speech-to-Text (STT) input and dynamic Text-to-Speech (TTS) audio feedback.
* **Context-Aware Questioning:** Dynamically generates targeted technical, situational, and behavioral interview questions mapped directly to specific job descriptions or roles.
* **AI Resume Evaluation:** Analyzes uploaded resumes against target roles, pinpointing ATS formatting gaps, missing keywords, skill deficiencies, and core strengths.
* **Optimized API Integration:** Implements built-in in-memory caching and token rate-limiting in the `ResumeModel` service layer to prevent quota exhaustion and reduce response latency.
* **Modern Multi-Page UI:** Clean, responsive design crafted using Streamlit multi-page routing and custom modular CSS.

---

## 🏗️ Project Architecture

```text
Career_Compass-Job-Career-Assistant/
├── .env                     # Local environment variables (API keys)
├── Home.py                  # Main application entry point & dashboard
├── chatbot_component.py     # Stateful conversational engine & prompt flows
├── requirements.txt         # Core dependencies and libraries
├── style.css                # Custom UI styling overrides
├── pages/                   # Multi-page routing (Mock Interview, Resume Analyzer)
└── services/                # Business logic, caching, and rate limiting
```

---

## ⚙️ Prerequisites

* **Python:** Version 3.8 or higher
* **Google Gemini API Key:** Accessible via [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/DD-05/Career_Compass-Job-Career-Assistant.git
cd Career_Compass-Job-Career-Assistant
```

### 2. Create and Activate a Virtual Environment

* **Windows:**
  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  ```

* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 5. Launch the Application

```bash
streamlit run Home.py
```

Access the application locally at `http://localhost:8501`.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend & UI** | Streamlit, Custom CSS |
| **LLM & NLP** | Google Gemini API, Prompt Engineering |
| **Audio Processing** | Speech-to-Text (STT), Text-to-Speech (TTS) |
| **Backend Utilities** | Python-dotenv, In-Memory Caching, Rate Limiting |

---

## 📄 License

This project is open-source and free to use.

---


✨ Happy Interviewing!
