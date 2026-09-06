from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "telemetry.parquet"
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
PORT = 8006
FEATURE_COLS = [
    "cpu_pct",
    "mem_pct",
    "disk_io",
    "net_in",
    "net_out",
    "temp_c",
    "latency_ms",
    "error_rate",
]
RANDOM_STATE = 42
TEST_FRACTION = 0.25
