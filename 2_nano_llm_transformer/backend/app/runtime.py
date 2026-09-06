"""Runtime load + generation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from app.config import ARTIFACTS, NanoConfig
from app.model import NanoTransformer
from app.tokenizer import CharTokenizer

_STATE: dict = {
    "model": None,
    "tokenizer": None,
    "config": None,
    "device": None,
    "last_attn": None,
    "meta": {},
}


def _pick_checkpoint() -> Path:
    for name in ("model.pt", "sft.pt", "pretrain.pt"):
        path = ARTIFACTS / name
        if path.exists():
            return path
    raise FileNotFoundError(
        "No checkpoint in backend/artifacts. Run train_pretrain.py then train_sft.py."
    )


def load_runtime(device: str | None = None) -> dict:
    if _STATE["model"] is not None:
        return _STATE

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    ckpt_path = _pick_checkpoint()
    ckpt = torch.load(ckpt_path, map_location=dev, weights_only=False)
    tok = CharTokenizer.load(ARTIFACTS / "tokenizer.json")
    cfg_d = ckpt["config"]
    config = NanoConfig(
        vocab_size=cfg_d["vocab_size"],
        block_size=cfg_d["block_size"],
        n_layer=cfg_d["n_layer"],
        n_head=cfg_d["n_head"],
        n_embd=cfg_d["n_embd"],
        dropout=0.0,
    )
    model = NanoTransformer(config).to(dev)
    model.load_state_dict(ckpt["model"])
    model.eval()

    meta = {"checkpoint": ckpt_path.name, "stage": ckpt.get("stage"), "params": model.param_count()}
    for mf in ("sft_meta.json", "pretrain_meta.json"):
        p = ARTIFACTS / mf
        if p.exists():
            meta[mf] = json.loads(p.read_text(encoding="utf-8"))

    _STATE.update(
        model=model,
        tokenizer=tok,
        config=config,
        device=dev,
        meta=meta,
        last_attn=None,
    )
    return _STATE


def get_last_attention() -> dict | None:
    attn = _STATE.get("last_attn")
    if attn is None:
        return None
    # attn: (1, H, T, T) — return last query row averaged over heads
    a = attn[0].mean(dim=0)  # (T, T)
    last_row = a[-1].tolist()
    return {
        "seq_len": a.size(0),
        "n_heads": int(attn.size(1)),
        "last_query_avg_over_heads": last_row,
        "matrix_avg_heads": a.tolist(),
    }
