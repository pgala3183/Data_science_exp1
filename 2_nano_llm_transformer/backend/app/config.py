from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
ARTIFACTS = BACKEND / "artifacts"
PORT = 8002


@dataclass
class NanoConfig:
    """~2–4M parameter decoder-only transformer."""

    vocab_size: int = 128  # filled from tokenizer
    block_size: int = 256
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 256
    dropout: float = 0.0
    # SwiGLU hidden = int(8/3 * n_embd), rounded to multiple of 64
    bias: bool = False

    def swiglu_hidden(self) -> int:
        h = int(8 * self.n_embd / 3)
        return ((h + 63) // 64) * 64

    def to_dict(self) -> dict:
        d = asdict(self)
        d["swiglu_hidden"] = self.swiglu_hidden()
        return d
