"""
Flux AI – Local LLM Inference Service
Loads the fine-tuned LoRA adapter on top of the base model and runs inference.

Usage (in code):
    from flux_backend.local_llm import LocalLLM
    llm = LocalLLM.get_instance()
    response = llm.generate(instruction="Review this code", code="def foo(): pass")
"""
import json
import logging
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

logger = logging.getLogger(__name__)


# ─── Lazy imports (only needed when using local model) ────────────────────────

def _load_torch():
    try:
        import torch
        return torch
    except ImportError:
        raise ImportError("Install torch: pip install torch --index-url https://download.pytorch.org/whl/cu121")


def _load_transformers():
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
        return AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
    except ImportError:
        raise ImportError("Install transformers: pip install transformers")


def _load_peft():
    try:
        from peft import PeftModel
        return PeftModel
    except ImportError:
        raise ImportError("Install peft: pip install peft")


# ─── Prompt Template (must match training) ────────────────────────────────────

DEFAULT_INSTRUCTION = (
    "Review the following Python code and identify bugs, improvements, "
    "performance issues, and security risks."
)

def build_prompt(instruction: str, code: str) -> str:
    return (
        f"### Instruction:\n{instruction}\n\n"
        f"### Code:\n{code}\n\n"
        f"### Review:\n"
    )


# ─── Local LLM Singleton ─────────────────────────────────────────────────────

class LocalLLM:
    """
    Singleton that loads the base model + LoRA adapter in 4-bit and
    exposes a generate() method matching the OpenAI agent interface.
    """

    _instance: "LocalLLM | None" = None

    def __init__(self, adapter_path: str, base_model: str):
        torch = _load_torch()
        AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, _ = _load_transformers()
        PeftModel = _load_peft()

        logger.info(f"Loading tokenizer from: {adapter_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            adapter_path,
            trust_remote_code=True,
            padding_side="right",
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        logger.info(f"Loading base model (4-bit): {base_model}")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        base.config.use_cache = True

        logger.info(f"Loading LoRA adapter from: {adapter_path}")
        self.model = PeftModel.from_pretrained(base, adapter_path)
        self.model.eval()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Local model ready on: {self.device.upper()}")

    @classmethod
    def get_instance(cls) -> "LocalLLM":
        """Get or create the singleton instance. Reads config from env vars."""
        if cls._instance is None:
            adapter_path = os.getenv("LOCAL_MODEL_PATH", "models/lora_adapter")
            base_model = os.getenv(
                "BASE_MODEL",
                "deepseek-ai/deepseek-coder-6.7b-instruct",
            )
            if not Path(adapter_path).exists():
                raise RuntimeError(
                    f"Local model adapter not found at '{adapter_path}'. "
                    "Run fine-tuning first: python training/qlora_train.py"
                )
            cls._instance = cls(adapter_path=adapter_path, base_model=base_model)
        return cls._instance

    def generate(
        self,
        instruction: str,
        code: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        do_sample: bool = True,
    ) -> str:
        """
        Generate a code review for the given code.

        Args:
            instruction: The review instruction text.
            code: The source code to review.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (lower = more deterministic).
            do_sample: Whether to use sampling (True) or greedy (False).

        Returns:
            Raw generated text (JSON string matching the review schema).
        """
        import torch

        prompt = build_prompt(instruction, code)
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        # Decode only the newly generated tokens (not the prompt)
        prompt_len = inputs["input_ids"].shape[1]
        generated = outputs[0][prompt_len:]
        text = self.tokenizer.decode(generated, skip_special_tokens=True).strip()

        return text

    def review_code(self, code: str, language: str = "python") -> dict:
        """
        High-level method that runs the full review and returns a parsed dict.
        Mirrors the interface expected by the agent pipeline.
        """
        instruction = (
            f"Review the following {language} code and identify bugs, improvements, "
            f"performance issues, and security risks. Return a JSON object with keys: "
            f"bugs, improvements, performance, security, score (1-10)."
        )
        raw = self.generate(instruction=instruction, code=code)

        # Strip markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if fence_match:
            raw = fence_match.group(1).strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "bugs": "Unable to parse model output.",
                "improvements": "",
                "performance": "",
                "security": "",
                "score": 5,
                "_raw": raw[:1000],
            }
