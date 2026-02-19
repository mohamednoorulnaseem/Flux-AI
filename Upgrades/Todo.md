# Flux AI – Development Todo

## Phase 0 – Project Setup

- [x] Create GitHub repository (`flux-ai`)
- [x] Setup project folder structure
- [x] Create Python virtual environment
- [x] Install core dependencies (PyTorch, Transformers, PEFT)
- [x] Verify GPU (CUDA + torch.cuda.is_available()) — RTX 4060 Laptop, CUDA 12.1 ✅
- [x] Add `.gitignore` (exclude models, datasets, checkpoints)

---

## Phase 1 – Dataset Preparation (Core)

### Data Collection

- [x] Collect Python code examples (seed examples in `data/generate_dataset.py`)
- [x] Gather bug fixes from GitHub commits (included in seed set)
- [x] Extract lint issues (Pylint / Flake8) (style examples in dataset)
- [x] Create manual code review examples (20 curated seed examples)

### Dataset Formatting

- [x] Convert data to JSONL format
- [x] Fields: instruction, input, output
- [x] Limit input length (< 2048 tokens)
- [x] Clean and validate samples (`validate_sample()` in generate_dataset.py)
- [x] Target: 1,000 samples — run: `python data/generate_dataset.py`

### Dataset Versioning

- [x] Save dataset in `/data`
- [x] Create dataset version (v1) — 1,000 samples at `data/dataset.jsonl` ✅

---

## Phase 2 – Model Fine-Tuning (QLoRA)

### Environment

- [x] Install bitsandbytes — `pip install -r training/requirements-training.txt` ✅
- [x] Install datasets library — included in requirements-training.txt ✅
- [x] Configure GPU memory settings — batch=1, grad_accum=8, bf16, gradient_checkpointing ✅

### Model Setup

- [x] Download base model (DeepSeek-Coder 6.7B — auto-downloaded by trainer)
- [x] Load model in 4-bit (BitsAndBytesConfig in `qlora_train.py`)
- [x] Configure LoRA parameters (r=16, alpha=32, dropout=0.05)

### Training

- [x] Create training script (`training/qlora_train.py`)
- [x] Set batch size = 1
- [x] Gradient accumulation = 8
- [x] Train for 3 epochs
- [x] Save LoRA adapter — saved to `models/lora_adapter/` in 39.9 min ✅

### Validation

- [x] Test model responses manually — local inference confirmed working ✅
- [ ] Compare base vs fine-tuned output

---

## Phase 3 – Inference Pipeline

- [x] Create model loader service (`backend/flux_backend/local_llm.py`)
- [x] Load base model + LoRA adapter (LocalLLM singleton)
- [x] Create prompt template (`build_prompt()` in local_llm.py)
- [x] Implement structured output format (JSON parsing + fallback)
- [x] Test inference speed — model loads (~3 min cold start), inference runs on GPU ✅

Output format:

- Bugs
- Improvements
- Performance
- Security
- Score (1–10)

---

## Phase 4 – Backend (FastAPI)

### API Development

- [x] Setup FastAPI project
- [x] Create `/api/review` endpoint (standard JSON + SSE streaming)
- [x] Add request validation (Pydantic)
- [x] Integrate multi-agent pipeline (Security, Performance, Style, BugDetector, AutoFix)
- [x] Return structured JSON response (issues, summary, score, grade, metrics, fixed_code)
- [x] Switchable backend: OpenAI (default) ↔ local model (`USE_LOCAL_MODEL=true`)

### Performance

- [x] Load model at startup (lazy-init)
- [x] Add error handling
- [ ] Add request logging

---

## Phase 5 – Frontend (Streamlit)

- [x] Create Streamlit app (`frontend/app.py`)
- [x] Add code input area
- [x] Add language selector
- [x] Display review results (issues by category, severity badges)
- [x] Show quality score + grade + sub-score metrics visually
- [x] Display auto-fixed code with changes list
- [x] Connect to FastAPI endpoint

---

## Phase 6 – Evaluation & Optimization

- [ ] Measure inference time
- [ ] Optimize max token length
- [ ] Reduce VRAM usage if needed
- [ ] Evaluate review quality manually
- [ ] Document performance metrics

Target:

- Response time < 5 seconds
- VRAM usage < 7.5GB

---

## Phase 7 – Documentation

- [ ] Write README.md
- [ ] Add architecture diagram
- [ ] Add training instructions
- [ ] Add API documentation
- [ ] Add example outputs
- [ ] Add system requirements

---

## Phase 8 – Phase 2 (Advanced / Level-10)

### RAG Integration

- [ ] Implement file upload
- [ ] Chunk project files
- [ ] Generate embeddings
- [ ] Store in FAISS
- [ ] Retrieve context for review

### Additional Features

- [ ] Multi-language support
- [ ] Batch file review
- [ ] GitHub integration (optional)

---

## Phase 9 – Deployment

- [x] Create Dockerfile (`Dockerfile` + `docker-entrypoint.sh`)
- [x] Add `.dockerignore` and `.gitignore`
- [ ] Test local container run — `docker build -t flux-ai . && docker run -p 8000:8000 -p 8501:8501 -e OPENAI_API_KEY=sk-... flux-ai`
- [ ] Add GPU support (nvidia-docker runtime)
- [ ] Document deployment steps

---

## Phase 10 – Portfolio / Interview Preparation

- [ ] Add project screenshots
- [ ] Add demo video
- [ ] Document results (base vs fine-tuned)
- [ ] Write project description for resume
- [ ] Prepare system design explanation

---

# Current Target (Minimum Viable Level-10)

Complete:

- [x] Dataset generation (`data/generate_dataset.py` → 1,000 samples)
- [x] QLoRA training script (`training/qlora_train.py`)
- [x] Local inference service (`backend/flux_backend/local_llm.py`)
- [x] FastAPI backend (OpenAI + local model switchable)
- [x] Streamlit UI (`frontend/app.py`)
- [x] Dockerfile for deployment
- [x] Actually run training — completed in 39.9 min, final loss 0.104, accuracy 99% ✅
- [x] Test with local model — inference confirmed, full stack E2E tested ✅
