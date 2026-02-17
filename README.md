# ⚡ Flux – AI Code Reviewer 🧠💻

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-blue.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Flux is a state-of-the-art, multi-agent AI code review platform. It goes beyond simple linting by deploying a pipeline of specialized agents (Security, Performance, Style, Bug Hunter, and Auto-Fix) to provide deep, context-aware analysis of your code.

---

## ✨ Key Features

- **🚀 Multi-Agent Orchestration**: 5 specialized AI agents work in parallel to audit your code.
- **📡 Real-time Streaming**: Watch the agents work in real-time via Server-Sent Events (SSE).
- **🛡️ Deep Security Audit**: Detects SQL injection, XSS, SSRF, and 50+ vulnerability patterns.
- **⚡ Performance Profiling**: Identifies algorithmic bottlenecks (O(n²)), memory leaks, and N+1 queries.
- **🔧 Auto-Fix Generation**: One-click production-ready fixes with visual diffs.
- **📊 Letter Grade System**: Instant quality assessment from A+ to F based on weighted metrics.
- **🎨 High-End UI/UX**: Dark mode, glassmorphism, animated metrics, and integrated Monaco Editor.
- **📈 Analytics Dashboard**: Track code quality trends, scores, and issue patterns over time.

---

## 📁 Project Structure

```
Flux AI/
│
├── backend/
│   ├── flux_backend/
│   │   ├── main.py          (API endpoints + SSE streaming)
│   │   ├── orchestrator.py  (Multi-agent pipeline coordinator)
│   │   ├── agents.py        (Specialized AI agent definitions)
│   │   ├── database.py      (SQLite persistence)
│   │   └── auth.py          (JWT-based authentication)
│   │
│   ├── .env                 (ignored) OPENAI API key + Config
│   ├── .env.example         (env template)
│   └── requirements.txt     (Python dependencies)
│
├── frontend/
│   ├── src/
│   │   ├── pages/           (Landing, Review, Dashboard, etc.)
│   │   ├── services/api.ts  (Streaming SSE client + API calls)
│   │   ├── context/         (Auth & State management)
│   │   └── assets/          (Brand assets & icons)
│   │
│   ├── index.html           (SEO & Entry point)
│   ├── package.json         (React dependencies)
│   └── vite.config.ts       (Build configuration)
│
└── README.md
```

---

## ⚙️ Quick Start

### 💻 Backend Setup

1. **Navigate and Environment**:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in `backend/`:

   ```env
   OPENAI_API_KEY=sk-your-key-here
   DATABASE_URL=sqlite:///./flux.db
   SECRET_KEY=your-secret-key
   ```

3. **Run Server**:
   ```bash
   python -m uvicorn flux_backend.main:app --reload --port 8000
   ```

---

### 🌐 Frontend Setup

1. **Install and Run**:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Access the App**: [http://localhost:5173](http://localhost:5173)

---

## 🧠 The Agentic Pipeline

Flux uses a proprietary orchestrator that manages:

1. **Security Agent**: Audits for OWASP Top 10 and common pitfalls.
2. **Performance Agent**: Evaluates time/space complexity and resource usage.
3. **Style Agent**: Enforces standards, naming conventions, and DRY principles.
4. **Bug Detector**: Logic hunter focus on edge cases and race conditions.
5. **Auto-Fix Agent**: Merges all findings into a corrected version of the code.

---

## 👨‍💻 Author

👤 **Mohamed Noorul Naseem**  
_AI & Backend Engineering Enthusiast_

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

⭐ **If you like Flux, please star the repo!**
