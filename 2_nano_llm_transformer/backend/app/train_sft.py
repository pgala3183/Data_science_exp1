"""Lightweight SFT on instruction/response pairs (character-level chat format)."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset

from app.config import ARTIFACTS, DATA_PROCESSED, NanoConfig
from app.model import NanoTransformer
from app.tokenizer import CharTokenizer


class SFTDataset(Dataset):
    def __init__(self, rows: list[dict], tokenizer: CharTokenizer, block_size: int):
        self.samples: list[torch.Tensor] = []
        for row in rows:
            ids = tokenizer.format_chat(row["user"], row["assistant"])
            if len(ids) < 3:
                continue
            if len(ids) > block_size + 1:
                ids = ids[: block_size + 1]
            self.samples.append(torch.tensor(ids, dtype=torch.long))
        self.block_size = block_size
        self.pad_id = tokenizer.pad_id

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        ids = self.samples[idx]
        # pad to block_size+1 for simple batching
        need = self.block_size + 1 - ids.size(0)
        if need > 0:
            ids = torch.cat([ids, torch.full((need,), self.pad_id, dtype=torch.long)])
        x, y = ids[:-1].clone(), ids[1:].clone()
        # Mask pad positions in targets
        y[y == self.pad_id] = -100
        # Also mask user prompt tokens in loss: only train on assistant span when possible
        return x, y


def load_model(device: torch.device) -> tuple[NanoTransformer, CharTokenizer, NanoConfig]:
    tok = CharTokenizer.load(ARTIFACTS / "tokenizer.json")
    ckpt = torch.load(ARTIFACTS / "pretrain.pt", map_location=device, weights_only=False)
    cfg_dict = ckpt["config"]
    config = NanoConfig(
        vocab_size=cfg_dict["vocab_size"],
        block_size=cfg_dict["block_size"],
        n_layer=cfg_dict["n_layer"],
        n_head=cfg_dict["n_head"],
        n_embd=cfg_dict["n_embd"],
        dropout=cfg_dict.get("dropout", 0.0),
    )
    model = NanoTransformer(config).to(device)
    model.load_state_dict(ckpt["model"])
    return model, tok, config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    sft_path = DATA_PROCESSED / "sft.jsonl"
    if not sft_path.exists() or not (ARTIFACTS / "pretrain.pt").exists():
        raise SystemExit("Need pretrain checkpoint and data/processed/sft.jsonl")

    device = torch.device("cpu" if not torch.cuda.is_available() else args.device)
    if args.device == "cpu":
        device = torch.device("cpu")

    model, tokenizer, config = load_model(device)
    rows = [json.loads(line) for line in sft_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ds = SFTDataset(rows, tokenizer, config.block_size)
    loader = DataLoader(ds, batch_size=min(args.batch_size, len(ds)), shuffle=True)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    model.train()
    t0 = time.time()
    last_loss = 0.0

    for epoch in range(1, args.epochs + 1):
        total = 0.0
        n = 0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            logits, _ = model(xb)
            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                yb.view(-1),
                ignore_index=-100,
            )
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += loss.item()
            n += 1
        last_loss = total / max(n, 1)
        if epoch % 5 == 0 or epoch == 1:
            print(f"epoch {epoch}/{args.epochs} loss={last_loss:.3f}")

    elapsed = time.time() - t0
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": model.state_dict(),
            "config": config.to_dict(),
            "stage": "sft",
            "sft_loss": last_loss,
            "epochs": args.epochs,
        },
        ARTIFACTS / "sft.pt",
    )
    # Prefer SFT as the serving checkpoint
    torch.save(
        {
            "model": model.state_dict(),
            "config": config.to_dict(),
            "stage": "sft",
            "sft_loss": last_loss,
            "epochs": args.epochs,
        },
        ARTIFACTS / "model.pt",
    )
    meta = {
        "stage": "sft",
        "params": model.param_count(),
        "epochs": args.epochs,
        "seconds": round(elapsed, 1),
        "final_loss": last_loss,
        "n_examples": len(rows),
        "device": str(device),
    }
    (ARTIFACTS / "sft_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Done SFT in {elapsed:.1f}s -> {ARTIFACTS / 'model.pt'}")


if __name__ == "__main__":
    main()
