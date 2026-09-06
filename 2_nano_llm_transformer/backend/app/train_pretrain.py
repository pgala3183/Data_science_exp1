"""Pretrain nano transformer on TinyShakespeare (character LM)."""

from __future__ import annotations

import argparse
import json
import time

import torch

from app.config import ARTIFACTS, DATA_PROCESSED, NanoConfig
from app.model import NanoTransformer
from app.tokenizer import CharTokenizer


def get_batch(data: torch.Tensor, block_size: int, batch_size: int, device: torch.device):
    ix = torch.randint(len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i : i + block_size] for i in ix])
    y = torch.stack([data[i + 1 : i + block_size + 1] for i in ix])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, data, block_size, batch_size, device, eval_iters: int = 20) -> float:
    model.eval()
    losses = torch.zeros(eval_iters)
    for k in range(eval_iters):
        xb, yb = get_batch(data, block_size, batch_size, device)
        _, loss = model(xb, yb)
        losses[k] = loss.item()
    model.train()
    return float(losses.mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    text_path = DATA_PROCESSED / "pretrain.txt"
    if not text_path.exists():
        raise SystemExit("Missing data. Run: python data/fetch_data.py")

    print("Loading corpus...", flush=True)
    text = text_path.read_text(encoding="utf-8")
    tokenizer = CharTokenizer.from_text(text)
    config = NanoConfig(vocab_size=tokenizer.vocab_size)

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        device = torch.device("cpu")
    else:
        device = torch.device(args.device if args.device == "cpu" or torch.cuda.is_available() else "cpu")

    ids = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    n = int(0.9 * len(ids))
    train_ids, val_ids = ids[:n], ids[n:]

    model = NanoTransformer(config).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)
    print(
        f"params={model.param_count():,} vocab={config.vocab_size} device={device}",
        flush=True,
    )

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    tokenizer.save(ARTIFACTS / "tokenizer.json")

    model.train()
    t0 = time.time()
    best_val = float("inf")

    for step in range(1, args.steps + 1):
        xb, yb = get_batch(train_ids, config.block_size, args.batch_size, device)
        _, loss = model(xb, yb)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step % 50 == 0 or step == 1:
            val = estimate_loss(model, val_ids, config.block_size, args.batch_size, device)
            print(
                f"step {step:4d}/{args.steps} train_loss={loss.item():.3f} val_loss={val:.3f}",
                flush=True,
            )
            if val < best_val:
                best_val = val
                torch.save(
                    {
                        "model": model.state_dict(),
                        "config": config.to_dict(),
                        "stage": "pretrain",
                        "val_loss": val,
                        "steps": step,
                    },
                    ARTIFACTS / "pretrain.pt",
                )

    elapsed = time.time() - t0
    meta = {
        "stage": "pretrain",
        "params": model.param_count(),
        "steps": args.steps,
        "seconds": round(elapsed, 1),
        "best_val_loss": best_val,
        "device": str(device),
        "config": config.to_dict(),
    }
    (ARTIFACTS / "pretrain_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Also copy as model.pt until SFT runs
    ckpt = torch.load(ARTIFACTS / "pretrain.pt", map_location="cpu", weights_only=False)
    torch.save(ckpt, ARTIFACTS / "model.pt")
    print(f"Done pretrain in {elapsed:.1f}s -> {ARTIFACTS / 'pretrain.pt'}", flush=True)


if __name__ == "__main__":
    main()
