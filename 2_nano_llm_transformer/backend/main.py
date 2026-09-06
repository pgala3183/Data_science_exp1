"""FastAPI nano-LLM service with SSE token streaming."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import ARTIFACTS, PORT  # noqa: E402
from app.runtime import get_last_attention, load_runtime  # noqa: E402
from app.schemas import GenerateRequest, ModelInfo  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if (ARTIFACTS / "tokenizer.json").exists() and any(
        (ARTIFACTS / name).exists() for name in ("model.pt", "sft.pt", "pretrain.pt")
    ):
        load_runtime()
    yield


app = FastAPI(
    title="Nano LLM Transformer",
    description="From-scratch RoPE+SwiGLU decoder LM with SSE generation",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    ready = False
    try:
        load_runtime()
        ready = True
    except FileNotFoundError:
        ready = False
    return {"ok": True, "model_ready": ready, "port": PORT}


@app.get("/model/info", response_model=ModelInfo)
def model_info():
    try:
        st = load_runtime()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return ModelInfo(
        params=st["model"].param_count(),
        checkpoint=st["meta"].get("checkpoint", ""),
        stage=st["meta"].get("stage"),
        config=st["config"].to_dict(),
        meta=st["meta"],
    )


@app.get("/model/attention")
def model_attention():
    attn = get_last_attention()
    if attn is None:
        raise HTTPException(404, "No attention captured yet — generate first")
    return attn


@app.post("/generate")
async def generate(req: GenerateRequest):
    try:
        st = load_runtime()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e

    model = st["model"]
    tok = st["tokenizer"]
    device = st["device"]
    special_ids = set(tok.special.values())

    if req.chat:
        ids = tok.format_chat(req.prompt, assistant=None)
    else:
        ids = tok.encode(req.prompt, add_bos=True)

    idx = torch.tensor([ids], dtype=torch.long, device=device)

    async def event_gen():
        text_out = ""
        yield {
            "event": "meta",
            "data": json.dumps({"prompt_tokens": len(ids), "params": model.param_count()}),
        }
        for token_id, attn in model.generate(
            idx,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            top_k=req.top_k or None,
            top_p=req.top_p if req.top_p > 0 else None,
            eos_id=tok.eos_id,
            return_attn=True,
        ):
            if attn is not None:
                st["last_attn"] = attn.cpu()
            if token_id == tok.eos_id:
                yield {"event": "done", "data": json.dumps({"text": text_out})}
                return
            if token_id in special_ids:
                continue
            piece = tok.decode([token_id])
            if not piece:
                continue
            text_out += piece
            yield {"event": "token", "data": json.dumps({"token": piece, "text": text_out})}
        yield {"event": "done", "data": json.dumps({"text": text_out})}

    return EventSourceResponse(event_gen())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
