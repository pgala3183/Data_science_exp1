from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "transactions.parquet"
PORT = 8003
RANDOM_STATE = 42
K_RANGE = range(2, 9)
