import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ai_code_review(code: str, language: str = "python") -> dict:
    """
    Call OpenAI to review the code and return a clean JSON dict.
    """
    system_prompt = """
    You are a senior code reviewer.
    Analyze the given code and return a JSON object with this structure:

    {
      "issues": [
        {
          "line": int,
          "severity": "critical|high|medium|low",
          "category": "bug|security|performance|style",
          "description": str,
          "suggestion": str
        }
      ],
      "summary": str,
      "score": int
    }

    Only return JSON. Do not include any other text.
    """

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Language: {language}\n\nCode:\n```{language}\n{code}\n```",
                },
            ]
        )

        text = response.output_text

        # 🔹 If the model wrapped JSON in ```json ...```, extract the inside part
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        # Try to parse JSON
        return json.loads(text)

    except Exception as e:
        print("AI error:", repr(e))
        return {
            "issues": [],
            "summary": f"AI error: {e}",
            "score": 0,
        }
