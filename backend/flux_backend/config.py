"""
Flux Configuration — Central settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


class Settings:
    # App
    APP_NAME: str = "Flux AI Code Reviewer"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # OpenAI (used when USE_LOCAL_MODEL is False)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4.1-mini")

    # Local Model (set USE_LOCAL_MODEL=true to use fine-tuned model)
    USE_LOCAL_MODEL: bool = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
    LOCAL_MODEL_PATH: str = os.getenv("LOCAL_MODEL_PATH", "models/lora_adapter")
    BASE_MODEL: str = os.getenv("BASE_MODEL", "deepseek-ai/deepseek-coder-6.7b-instruct")


settings = Settings()
