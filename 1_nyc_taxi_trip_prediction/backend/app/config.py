from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "trips.parquet"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
N_CLUSTERS = 8
TEST_FRACTION = 0.2
RANDOM_STATE = 42
TARGET = "trip_duration"
PORT = 8001

FEATURE_COLUMNS = [
    "haversine_km",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_rush_hour",
    "passenger_count",
    "pickup_cluster",
    "dropoff_cluster",
    "pickup_latitude",
    "pickup_longitude",
    "dropoff_latitude",
    "dropoff_longitude",
]
