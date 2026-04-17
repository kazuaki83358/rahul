# 🧠 Multimodal RAG Code Assistant

A portfolio-grade AI coding assistant with multi-agent RAG, DSA graph scoring, voice/image input, and a live code sandbox.

## ✨ Features

- **Multimodal Input**: Support for text, voice (Whisper), and screenshot OCR (GPT-4V).
- **Multi-Agent Pipeline**: Specialized agents for Retrieval, Generation, Debugging, and Optimization.
- **DSA Score™**: Intelligent code similarity scoring for technical interview preparation.
- **Live Sandbox**: Run Python code directly in your browser via Pyodide.
- **Modern UI**: Dark-themed, responsive dashboard built with Next.js and Tailwind CSS.

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** and **Node.js 18+**
- **Redis** running locally (port 6379)
- **OpenAI** and **Gemini** API keys

### 2. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python -m app.utils.seed      # Creates database & seeds data
uvicorn app.main:app --reload # Starts backend at http://localhost:8000
```

### 3. Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev                   # Starts frontend at http://localhost:3000
```

## 🔑 Configuration
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
DATABASE_URL=sqlite:///./dev.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your_secret_key
```

## 🛠️ Project Structure
- `backend/`: FastAPI application, agents, and RAG logic.
- `frontend/`: Next.js 15 app with custom Tailwind components.
- `dataset/`: Seed data for LeetCode problems.
