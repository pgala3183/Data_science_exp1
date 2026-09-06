from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "baskets.parquet"
PORT = 8004
DEFAULT_MIN_SUPPORT = 0.02
DEFAULT_MIN_CONFIDENCE = 0.2
DEFAULT_MIN_LIFT = 1.0
