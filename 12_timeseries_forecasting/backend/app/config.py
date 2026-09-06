from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "retail_sales.parquet"
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
PORT = 8012

MAX_LAGS = 40
HORIZONS = (1, 7, 30)
# SARIMA: weekly seasonality (s=7); orders guided by ACF/PACF (lag-7 spikes)
SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL_ORDER = (1, 0, 1, 7)

# Gradient boosting lag / rolling feature config
LAGS = (1, 2, 3, 7, 14, 21, 28)
ROLL_WINDOWS = (7, 14, 28)

# Rolling-origin backtest (stride keeps wall-clock reasonable)
MIN_TRAIN = 400
STEP = 45  # origin stride (days)
ALPHA = 0.05  # 95% prediction intervals
RANDOM_STATE = 42
