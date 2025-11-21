# ⚡ Codexa – AI Code Reviewer 🧠💻

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-blue.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Codexa is a full-stack AI-powered code review system that analyzes source code and automatically generates:

- 🔍 Detected issues (bugs, style, security, performance)
- 📌 Line numbers for each issue
- 💡 Suggestions for improvements
- 🧾 Readable multi-point summary
- 🏆 Overall quality score (0–100)

Built using FastAPI + Python (backend) & React + TypeScript (frontend), powered by OpenAI Responses API.

---

## 🚀 Features

| Feature                  | Description                                |
| ------------------------ | ------------------------------------------ |
| 🧠 AI-powered review     | Uses OpenAI to analyze code deeply         |
| 🐍 Multi-language ready  | Python now; extendable to JS, C++, Java    |
| 📌 Line-by-line feedback | Shows exact line numbers for issues        |
| 🔐 Secure config         | `.env` for API key, not shared in Git      |
| 📊 Code Quality Score    | Ranks maintainability / readability        |
| 🌐 Modern Web UI         | User-friendly interface for reviewing code |

---

## 📁 Project Structure

codexa-ai-code-reviewer/
│
├── backend/
│ ├── codexa_backend/
│ │ ├── **init**.py
│ │ ├── main.py (FastAPI endpoints + CORS)
│ │ └── ai_reviewer.py (OpenAI request + JSON parsing)
│ │
│ ├── .env (ignored) OpenAI key
│ ├── .env.example (env template)
│ └── requirements.txt (Python dependencies)
│
├── frontend/
│ ├── src/
│ │ ├── App.tsx (UI logic + API call)
│ │ ├── App.css (UI styling)
│ │ └── ...
│ ├── vite.config.ts (Frontend config)
│ └── package.json (React dependencies)
│
└── README.md

---

## ⚙️ Installation & Usage

### 💻 1️⃣ Backend Setup (FastAPI)

cd backend
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

Create a `.env` file inside backend/ and add:
OPENAI_API_KEY=your_openai_api_key_here

Run the backend:
uvicorn codexa_backend.main:app --reload --port 8000

📌 Open API Docs: http://127.0.0.1:8000/docs

---

### 🌐 2️⃣ Frontend Setup (React + TypeScript)

Open a new terminal (do not close backend)

cd frontend
npm install
npm run dev

🌍 Frontend URL: http://localhost:5173

---

## 📬 Example API Usage

### 📥 Request

POST /api/review

{
"filename": "example.py",
"language": "python",
"code": "def add(a,b): return a+b"
}

### 📤 Example Response

{
"issues": [
{
"line": 1,
"severity": "low",
"category": "style",
"description": "Function definition lacks spacing.",
"suggestion": "Use: def add(a, b): return a + b"
}
],
"summary": "Logic works but lacks readability and proper spacing.",
"score": 90
}

---

## 🧭 Roadmap

- Multi-language support (JS, C++, Java)
- Security vulnerability detection
- Cyclomatic Complexity metrics
- Auto-generated test cases
- GitHub pull-request integration

---

## 👨‍💻 Author

Developed by **Mohamed Noorul Naseem**
_AI & Backend Engineering Enthusiast_

---

## 🤝 Contribute

Pull requests are welcome!
Have an idea? Open an issue or contribute.

---

### ⭐ If you like Codexa, don’t forget to star the repo!
