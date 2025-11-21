# Codexa – AI Code Reviewer 🧠💻

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Codexa is an AI-powered backend service that reviews source code and returns:

- 🔍 **Detected issues** (bug / style / performance / security)
- 📌 **Line numbers**
- 💡 **Suggestions for fixes**
- 🧾 **Readable summary**
- 🏆 **Overall quality score (0–100)**

Currently implemented as a **FastAPI backend** using OpenAI's GPT models.

---

## 🚀 Features

| Feature                   | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| 🧠 AI-powered code review | Uses OpenAI to analyze source code                    |
| 🐍 Multi-language-ready   | Currently Python; architecture supports JS, C++, Java |
| 📌 Line-by-line feedback  | Returns exact line numbers                            |
| 🔐 Secure key loading     | API credentials via `.env`                            |
| 📊 Quality scoring        | Calculates maintainability score                      |

---

## 🛠️ Tech Stack

- **Python 3.14**
- **FastAPI**
- **Uvicorn**
- **OpenAI Responses API**
- **Dotenv**

---

## 📁 Project Structure

````text
codexa/
│
├── backend/
│   ├── codexa_backend/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI endpoints
│   │   └── ai_reviewer.py   # Calls OpenAI & parses JSON response
│   │
│   ├── .env                # (ignored) contains OPENAI_API_KEY
│   ├── .env.example        # Template env file
│   └── requirements.txt    # Libraries (optional)
│
└── README.md

---

## ⚙️ Installation & Usage

### 1️⃣ Setup Virtual Environment

```bash
cd backend
py -m venv .venv
````

Activate:

```bash
.\.venv\Scripts\activate
```

### 2️⃣ Install Dependencies

```bash
pip install fastapi uvicorn[standard] openai python-dotenv
```

### 3️⃣ Add Your API Key

Create a `.env` file in `backend/`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> 🛑 **Do NOT upload `.env`** — it is ignored automatically.

---

### ▶️ Run the Backend Server

```bash
uvicorn codexa_backend.main:app --reload --port 8000
```

Open your browser and go to:

🔗 **http://127.0.0.1:8000/docs**

---

## 📬 Example API Request

`POST /api/review`

```json
{
  "filename": "example.py",
  "language": "python",
  "code": "def add(a,b): return a+b"
}
```

### 🧠 Example Response

```json
{
  "issues": [
    {
      "line": 1,
      "severity": "low",
      "category": "style",
      "description": "Function definition should have spaces after commas and a newline after the function header for better readability.",
      "suggestion": "Rewrite the function as:\n\ndef add(a, b):\n    return a + b"
    }
  ],
  "summary": "The function works correctly but does not follow common Python style conventions for readability.",
  "score": 90
}
```

---

## 📌 Roadmap

- 🔧 Support **multiple languages** (JS, C++, Java)
- 🛡️ Add security vulnerability scanning
- 🧮 Add code complexity metrics (Cyclomatic Complexity)
- 🧪 Auto-generated test suggestions
- 🌐 GitHub PR integration

---

### 👨‍💻 Author

Developed by **[Your Name]**  
📌 _AI enthusiast • Backend Developer_

---

### ⭐ Contribute

Want to improve Codexa? Feel free to fork and submit pull requests!
