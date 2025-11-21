# ⚡ Codexa — AI Code Reviewer

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-blue.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Codexa is a full‑stack AI code review tool that analyzes source code and returns detected issues, exact line locations, actionable suggestions, a human‑readable summary, and an overall quality score.

---

## Key features

- AI-powered static review (bugs, style, security, performance)
- Per-line feedback with severity and category
- Suggestions and example fixes
- Readable summary and quality score (0–100)
- Web UI for paste/upload and interactive review
- Configurable and extensible for additional languages

---

## Tech stack

Backend

- Python 3.14, FastAPI, Uvicorn
- OpenAI Responses API
- python-dotenv

Frontend

- React + TypeScript, Vite
- Axios for API requests
- Minimal CSS for theming

---

## Project layout

```text
codexa-ai-code-reviewer/
├── backend/
│   ├── codexa_backend/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app + CORS
│   │   └── ai_reviewer.py   # OpenAI call + response parsing
│   ├── .env                 # (ignored) OPENAI_API_KEY
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── ...
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

---

## Installation

Prerequisites: Python 3.14, Node 18+ or compatible, npm

1. Backend

```bash
cd backend
python -m venv .venv
# Activate the venv (Windows)
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt

# Create backend/.env containing:
# OPENAI_API_KEY=your_openai_api_key_here

uvicorn codexa_backend.main:app --reload --port 8000
# API docs: http://127.0.0.1:8000/docs
```

2. Frontend (run in a separate terminal)

```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

---

## API

POST /api/review
Request JSON:

```json
{
  "filename": "example.py",
  "language": "python",
  "code": "def add(a,b): return a+b"
}
```

Example response:

```json
{
  "issues": [
    {
      "line": 1,
      "severity": "low",
      "category": "style",
      "description": "Function should have spaces after commas and a newline body.",
      "suggestion": "def add(a, b):\n    return a + b"
    }
  ],
  "summary": "Works but needs formatting for readability.",
  "score": 90
}
```

Schema notes:

- issues[].line: 1-based line number
- severity: low|medium|high
- category: style|bug|security|performance

---

## Roadmap

- Multi-language support (JS, C++, Java)
- Security vulnerability detection
- Complexity metrics and test generation
- GitHub PR integration

---

## Contributing

Contributions welcome. Please open issues or pull requests. Follow code style and include tests where appropriate.

---

## License

MIT — see LICENSE.

---

Developed by Mohamed Noorul Naseem — AI & Backend Engineering
