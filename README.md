# Autonomous CI/CD Healing Agent (RIFT 2026 Hackathon)

An AI-powered DevOps agent that automatically clones repositories, detects failures in tests, analyzes errors using Google Gemini, generates fixes, and commits them to a new branch, repeating the process until tests pass.

## 🚀 Features

- **Auto-Healing**: Detects test failures and applies AI-generated fixes.
- **Strict Branching**: Creates branches like `TEAM_LEADER_AI_Fix`.
- **Dashboard**: Real-time React UI to monitor the healing process.
- **LangGraph Orchestration**: Uses a state machine for robust error loops.
- **Gemini Free Tier**: Zero-cost LLM integration.

## 🛠 Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Chart.js
- **Backend**: Python, FastAPI, LangGraph, GitPython
- **AI**: Google Gemini Pro (via LangChain)

## 📦 Setup & Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git installed on system
- Google Gemini API Key

### Backend Setup

1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure Environment:
   Create `.env` inside `backend/`:
   ```env
   GEMINI_API_KEY=your_google_api_key_here
   ```
4. Run Server:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Frontend Setup

1. Navigate to frontend:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run Dev Server:
   ```bash
   npm run dev
   ```

## 🐳 Docker Support

A `Dockerfile` is provided for the backend.

```bash
docker build -t healing-agent-backend ./backend
docker run -p 8000:8000 -e GEMINI_API_KEY=... healing-agent-backend
```

## 🏗 Architecture

```
START -> Clone -> Run Tests -> [PASS?] -> END
                     |
                   [FAIL]
                     v
                Analyze Error (Gemini)
                     |
                Generate Fix (Gemini)
                     |
                Apply Fix -> Commit -> Push -> Retry (Max 5)
```

## ⚠️ Notes

- Ensure the repository provided has a `pytest` compatible test suite.
- The agent creates a `workspace` folder in the backend directory to check out code.
