"""CRISP-DM data preparation: load → engineer → time-based split → cluster fit on train only."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.cluster import KMeans

from app.config import DATA_PATH, FEATURE_COLUMNS, N_CLUSTERS, RANDOM_STATE, TARGET, TEST_FRACTION
from app.features import add_time_and_distance_features, filter_valid_trips


@dataclass
class PreparedData:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    pickup_kmeans: KMeans
    dropoff_kmeans: KMeans
    feature_columns: list[str]


def load_raw(path=DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python data/fetch_data.py from the project root."
        )
    return pd.read_parquet(path)


def time_based_split(
    df: pd.DataFrame, test_fraction: float = TEST_FRACTION
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split by pickup time — earlier trips train, later trips test.

    Random splits leak future traffic patterns into training and inflate metrics.
    """
    ordered = df.sort_values("pickup_datetime").reset_index(drop=True)
    cut = int(len(ordered) * (1.0 - test_fraction))
    cut = max(1, min(cut, len(ordered) - 1))
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()


def fit_coordinate_clusters(
    train: pd.DataFrame, n_clusters: int = N_CLUSTERS
) -> tuple[KMeans, KMeans]:
    pickup_kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    dropoff_kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
    pickup_kmeans.fit(train[["pickup_latitude", "pickup_longitude"]])
    dropoff_kmeans.fit(train[["dropoff_latitude", "dropoff_longitude"]])
    return pickup_kmeans, dropoff_kmeans


def assign_clusters(
    df: pd.DataFrame, pickup_kmeans: KMeans, dropoff_kmeans: KMeans
) -> pd.DataFrame:
    out = df.copy()
    out["pickup_cluster"] = pickup_kmeans.predict(out[["pickup_latitude", "pickup_longitude"]])
    out["dropoff_cluster"] = dropoff_kmeans.predict(
        out[["dropoff_latitude", "dropoff_longitude"]]
    )
    return out


def prepare_dataset(path=DATA_PATH) -> PreparedData:
    raw = load_raw(path)
    featured = add_time_and_distance_features(raw)
    clean = filter_valid_trips(featured)
    train_df, test_df = time_based_split(clean)

    pickup_kmeans, dropoff_kmeans = fit_coordinate_clusters(train_df)
    train_df = assign_clusters(train_df, pickup_kmeans, dropoff_kmeans)
    test_df = assign_clusters(test_df, pickup_kmeans, dropoff_kmeans)

    return PreparedData(
        X_train=train_df[FEATURE_COLUMNS],
        X_test=test_df[FEATURE_COLUMNS],
        y_train=train_df[TARGET],
        y_test=test_df[TARGET],
        train_df=train_df,
        test_df=test_df,
        pickup_kmeans=pickup_kmeans,
        dropoff_kmeans=dropoff_kmeans,
        feature_columns=list(FEATURE_COLUMNS),
    )


def build_feature_row(
    *,
    pickup_latitude: float,
    pickup_longitude: float,
    dropoff_latitude: float,
    dropoff_longitude: float,
    pickup_datetime: str,
    passenger_count: int,
    pickup_kmeans: KMeans,
    dropoff_kmeans: KMeans,
) -> pd.DataFrame:
    row = pd.DataFrame(
        [
            {
                "pickup_datetime": pickup_datetime,
                "pickup_latitude": pickup_latitude,
                "pickup_longitude": pickup_longitude,
                "dropoff_latitude": dropoff_latitude,
                "dropoff_longitude": dropoff_longitude,
                "passenger_count": passenger_count,
            }
        ]
    )
    row = add_time_and_distance_features(row)
    row = assign_clusters(row, pickup_kmeans, dropoff_kmeans)
    return row[FEATURE_COLUMNS]


def pipeline_diagram() -> dict:
    return {
        "name": "NycTaxiDurationPreprocessor",
        "steps": [
            {
                "id": "bbox_filter",
                "title": "Geographic & passenger filters",
                "detail": "Keep trips inside NYC bbox with passenger_count 1–6.",
            },
            {
                "id": "target_hygiene",
                "title": "Target hygiene (not feature engineering)",
                "detail": "Drop impossible durations (60s–7200s) before split; never derive features from duration.",
            },
            {
                "id": "time_distance",
                "title": "Pre-trip features",
                "detail": "Haversine km, hour, day_of_week, weekend & rush-hour flags.",
            },
            {
                "id": "time_split",
                "title": "Time-based train/test split",
                "detail": "Sort by pickup_datetime; earlier → train, later → test (no random shuffle).",
            },
            {
                "id": "kmeans_train_only",
                "title": "Zone clusters (train-only fit)",
                "detail": "KMeans on pickup/dropoff lat-lon fit on train; test and /predict only call predict().",
            },
            {
                "id": "assert_schema",
                "title": "Schema assertion",
                "detail": "FEATURE_COLUMNS exclude trip_duration and all post-trip fields (fare, tip, speed).",
            },
        ],
        "numeric_features": list(FEATURE_COLUMNS),
        "categorical_features": ["pickup_cluster", "dropoff_cluster", "is_weekend", "is_rush_hour"],
    }
