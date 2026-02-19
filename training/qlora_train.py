"""
Flux AI – QLoRA Fine-Tuning Script
Fine-tunes DeepSeek-Coder or CodeLlama on the code review dataset using QLoRA (4-bit).

Hardware: RTX 4060 (8GB VRAM) or equivalent
Method: QLoRA (4-bit quantization + LoRA adapters)

Usage:
    python training/qlora_train.py
    python training/qlora_train.py --model deepseek-ai/deepseek-coder-6.7b-instruct --epochs 3

Requirements:
    pip install -r training/requirements-training.txt
"""
import argparse
import json
import os
import time
from pathlib import Path

import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
)
from trl import SFTTrainer, SFTConfig

# ─── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "deepseek-ai/deepseek-coder-6.7b-instruct"
FALLBACK_MODEL = "codellama/CodeLlama-7b-Instruct-hf"
DATASET_PATH = "data/dataset.jsonl"
OUTPUT_DIR = "models/lora_adapter"
MAX_SEQ_LENGTH = 2048


# ─── Prompt Template ──────────────────────────────────────────────────────────

def format_prompt(sample: dict) -> str:
    """Format an instruction-input-output sample into a training prompt."""
    instruction = sample["instruction"]
    code = sample["input"]
    output = sample["output"]

    return (
        f"### Instruction:\n{instruction}\n\n"
        f"### Code:\n{code}\n\n"
        f"### Review:\n{output}\n"
    )


def format_prompt_inference(instruction: str, code: str) -> str:
    """Format a prompt for inference (without the expected output)."""
    return (
        f"### Instruction:\n{instruction}\n\n"
        f"### Code:\n{code}\n\n"
        f"### Review:\n"
    )


# ─── Dataset Loading ──────────────────────────────────────────────────────────

def load_training_dataset(path: str) -> Dataset:
    """Load and preprocess the JSONL dataset."""
    print(f"📂 Loading dataset from: {path}")
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. "
            "Run: python data/generate_dataset.py"
        )

    samples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            sample = json.loads(line.strip())
            samples.append({"text": format_prompt(sample)})

    dataset = Dataset.from_list(samples)
    print(f"✅ Loaded {len(dataset)} training samples")
    return dataset


# ─── BitsAndBytes Config (4-bit) ──────────────────────────────────────────────

def get_bnb_config() -> BitsAndBytesConfig:
    """4-bit quantization configuration for QLoRA."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,          # Nested quantization for extra savings
        bnb_4bit_quant_type="nf4",               # NormalFloat4 — best for LLMs
        bnb_4bit_compute_dtype=torch.bfloat16,   # Compute in bfloat16
    )


# ─── LoRA Config ──────────────────────────────────────────────────────────────

def get_lora_config() -> LoraConfig:
    """LoRA adapter configuration."""
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,                          # Rank — higher = more capacity, more VRAM
        lora_alpha=32,                 # Alpha — scaling factor (usually 2x rank)
        lora_dropout=0.05,             # Dropout for regularization
        bias="none",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",   # Attention
            "gate_proj", "up_proj", "down_proj",        # FFN
        ],
    )


# ─── Training Arguments ───────────────────────────────────────────────────────

def get_training_args(output_dir: str, epochs: int, batch_size: int) -> SFTConfig:
    """Training hyperparameters — tuned for RTX 4060 8GB."""
    return SFTConfig(
        output_dir=output_dir,
        max_length=MAX_SEQ_LENGTH,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=8,          # Effective batch size = 8
        gradient_checkpointing=True,             # Save VRAM at cost of speed
        optim="paged_adamw_8bit",                # Memory-efficient optimizer
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_steps=20,
        fp16=False,
        bf16=True,                               # Use bfloat16 if RTX 30xx/40xx
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none",                        # Disable wandb/tensorboard
        dataloader_pin_memory=False,
        dataset_text_field="text",               # Column containing formatted text
    )


# ─── Callbacks ────────────────────────────────────────────────────────────────

class ProgressCallback(TrainerCallback):
    """Print readable training progress."""

    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.start_time = time.time()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and state.global_step % 10 == 0:
            elapsed = time.time() - self.start_time
            progress = state.global_step / max(self.total_steps, 1) * 100
            loss = logs.get("loss", "N/A")
            lr = logs.get("learning_rate", "N/A")
            print(
                f"  Step {state.global_step}/{self.total_steps} "
                f"({progress:.1f}%) | Loss: {loss:.4f} | LR: {lr:.2e} | "
                f"Elapsed: {elapsed:.0f}s"
            )


# ─── Main Training Function ───────────────────────────────────────────────────

def train(
    model_name: str = DEFAULT_MODEL,
    dataset_path: str = DATASET_PATH,
    output_dir: str = OUTPUT_DIR,
    epochs: int = 3,
    batch_size: int = 1,
):
    """Run the full QLoRA fine-tuning pipeline."""
    print("\n" + "="*60)
    print("  Flux AI — QLoRA Fine-Tuning")
    print("="*60)
    print(f"  Base model : {model_name}")
    print(f"  Dataset    : {dataset_path}")
    print(f"  Output     : {output_dir}")
    print(f"  Epochs     : {epochs}")
    print(f"  GPU        : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (not recommended)'}")
    print("="*60 + "\n")

    # Check GPU
    if not torch.cuda.is_available():
        print("⚠️  WARNING: No GPU detected. Training will be extremely slow on CPU.")
        print("   Install CUDA and PyTorch with GPU support.\n")

    # ── 1. Load dataset ──────────────────────────────────
    dataset = load_training_dataset(dataset_path)

    # ── 2. Load tokenizer ────────────────────────────────
    print(f"⬇️  Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── 3. Load model in 4-bit ───────────────────────────
    print(f"⬇️  Loading model in 4-bit: {model_name}")
    bnb_config = get_bnb_config()
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False                    # Required for gradient checkpointing
    model.config.pretraining_tp = 1

    # ── 4. Apply LoRA ────────────────────────────────────
    print("🔧 Applying LoRA adapters...")
    model = prepare_model_for_kbit_training(model)
    lora_config = get_lora_config()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── 5. Setup trainer ─────────────────────────────────
    print("⚙️  Setting up trainer...")
    training_args = get_training_args(output_dir, epochs, batch_size)

    total_steps = (len(dataset) // batch_size) * epochs
    progress_cb = ProgressCallback(total_steps)

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
        callbacks=[progress_cb],
    )

    # ── 6. Train ─────────────────────────────────────────
    print("\n🚀 Starting training...\n")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    print(f"\n✅ Training complete in {elapsed / 60:.1f} minutes")

    # ── 7. Save adapter ──────────────────────────────────
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"💾 LoRA adapter saved to: {output_dir}")

    # Save training metadata
    metadata = {
        "base_model": model_name,
        "dataset_path": dataset_path,
        "num_samples": len(dataset),
        "epochs": epochs,
        "batch_size": batch_size,
        "gradient_accumulation_steps": 8,
        "max_seq_length": MAX_SEQ_LENGTH,
        "training_time_minutes": round(elapsed / 60, 1),
        "lora_r": 16,
        "lora_alpha": 32,
    }
    meta_path = Path(output_dir) / "training_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    print(f"📄 Metadata saved to: {meta_path}\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flux AI – QLoRA Fine-Tuning")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"HuggingFace model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dataset",
        default=DATASET_PATH,
        help=f"Path to JSONL dataset (default: {DATASET_PATH})",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_DIR,
        help=f"Output directory for LoRA adapter (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Per-device batch size (default: 1 for 8GB VRAM)",
    )
    args = parser.parse_args()

    train(
        model_name=args.model,
        dataset_path=args.dataset,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
