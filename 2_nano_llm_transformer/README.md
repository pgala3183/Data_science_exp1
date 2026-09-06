# Nano LLM Transformer (Experiment 2)

A **from-scratch** autoregressive decoder-only transformer in PyTorch (RoPE, SwiGLU, pre-norm multi-head attention), pretrained on TinyShakespeare, lightly SFT’d on a tiny instruction set, and served with **SSE token streaming**.

> Honest framing: this is a **nano** model (a few million parameters, character-level). It will **not** match GPT-4. Expect brittle answers, Shakespearean babble, and frequent failure on anything outside the tiny SFT set.

## Problem statement

Learn the internals of modern LLMs by implementing the stack yourself, then expose generation through a chat UI with adjustable sampling and an attention visualization.

## Dataset & source

| Stage | Data | Source |
|-------|------|--------|
| Pretrain | TinyShakespeare | [karpathy/char-rnn](https://github.com/karpathy/char-rnn) `input.txt` via `data/fetch_data.py` |
| SFT | 25 hand-written instruction/response pairs | `data/fetch_data.py` → `data/processed/sft.jsonl` |

```bash
python data/fetch_data.py
```

## Architecture

- **Causal multi-head self-attention** (implemented in `backend/app/model.py`)
- **RoPE** positional encoding on Q/K (`backend/app/rope.py`)
- **SwiGLU** feed-forward, **RMSNorm** pre-norm residuals
- **Weight tying** between token embedding and LM head
- Default size: `n_layer=4`, `n_head=4`, `n_embd=256`, `block_size=256` → **~3–4M params** (exact count printed at train time / `/model/info`)

## Training

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python -m app.train_pretrain --steps 600 --batch-size 32 --device cpu
python -m app.train_sft --epochs 40 --device cpu
```

### Reported run (this machine)

| Item | Value |
|------|--------|
| Parameters | **3,231,744 (~3.2M)** |
| Vocab | 71 characters + special tokens |
| Pretrain | 300 steps, batch 16, **223s** on CPU · best val loss **1.81** |
| SFT | 40 epochs on 25 pairs, **42s** on CPU · final loss **0.15** |
| Checkpoint | `backend/artifacts/model.pt` (~12MB) |

### Sample outputs

| Prompt | Output (observed) |
|--------|-------------------|
| Say hello. | `Hello! How may I help thee today?` |
| Name a Shakespeare play. | often `Hamlet` (SFT-memorized) |

**Expected failures (honest):** open-ended reasoning, long essays, modern factual Q&A, and anything far from the 25 SFT prompts — the model drifts into Shakespearean character soup. That is expected for a nano character LM, not a production chatbot.

## How to run the app

Ports (experiment **2**): API **8002**, UI **5175**.

```bash
# API
cd backend
.\.venv\Scripts\activate
uvicorn main:app --reload --port 8002

# UI
cd frontend
npm install
npm run dev
```

Open http://localhost:5175 — Chat streams tokens; Architecture shows config + last-layer attention heatmap after a generation.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + `model_ready` |
| `GET` | `/model/info` | Params, config, train meta |
| `GET` | `/model/attention` | Last captured attention matrix |
| `POST` | `/generate` | SSE stream (`token` / `done` events) |

Body: `{ "prompt", "temperature", "max_tokens", "top_k", "top_p", "chat": true }`.

## Sample outputs & failure cases

**Sometimes OK (after SFT):**

- “Say hello.” → `Hello! How may I help thee today?`
- “Name a Shakespeare play.” → often “Hamlet”

**Expected failures:**

- Multi-step reasoning / novel math.
- Long coherent essays — character LM + tiny context drifts into gibberish.
- Modern factual Q&A — pretrained on plays, not the web.
- Soft prompt variants not in the 25-example SFT set.

## Leakage / eval notes

This is a generative LM demo, not a supervised metric leaderboard. Val loss during pretrain uses a held-out **suffix** of the Shakespeare text (last 10%). SFT is too small for a meaningful holdout; we report train loss only and emphasize qualitative honesty.

## Tests

```bash
cd backend
pytest
ruff check app tests
```
