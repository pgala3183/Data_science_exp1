"""Isolation Forest, LOF, and PyTorch autoencoder backbones."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


class TabularAutoencoder(nn.Module):
    def __init__(self, n_features: int, hidden: int = 16, latent: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, latent),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_features),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def train_autoencoder(
    X_train: np.ndarray,
    *,
    epochs: int = 40,
    lr: float = 1e-3,
    batch_size: int = 64,
    seed: int = 42,
) -> TabularAutoencoder:
    torch.manual_seed(seed)
    model = TabularAutoencoder(X_train.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    data = torch.tensor(X_train, dtype=torch.float32)
    model.train()
    for _ in range(epochs):
        perm = torch.randperm(data.size(0))
        for i in range(0, data.size(0), batch_size):
            batch = data[perm[i : i + batch_size]]
            opt.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            opt.step()
    model.eval()
    return model


@torch.no_grad()
def ae_scores(model: TabularAutoencoder, X: np.ndarray) -> np.ndarray:
    x = torch.tensor(X, dtype=torch.float32)
    recon = model(x)
    return ((recon - x) ** 2).mean(dim=1).numpy()


@dataclass
class FittedBackbones:
    scaler: StandardScaler
    isolation_forest: IsolationForest
    lof: LocalOutlierFactor
    autoencoder: TabularAutoencoder
    feature_names: list[str]
    # Calibration ranges for mapping raw → [0,1] consistently with eval
    score_min: dict[str, float] = field(default_factory=dict)
    score_max: dict[str, float] = field(default_factory=dict)


def fit_backbones(X_normal: np.ndarray, feature_names: list[str], seed: int = 42) -> FittedBackbones:
    scaler = StandardScaler().fit(X_normal)
    Xs = scaler.transform(X_normal)

    iforest = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=seed,
        n_jobs=-1,
    ).fit(Xs)

    lof = LocalOutlierFactor(
        n_neighbors=20,
        contamination=0.05,
        novelty=True,
        n_jobs=-1,
    ).fit(Xs)

    ae = train_autoencoder(Xs, epochs=35, seed=seed)

    return FittedBackbones(
        scaler=scaler,
        isolation_forest=iforest,
        lof=lof,
        autoencoder=ae,
        feature_names=feature_names,
    )


def raw_scores(backbones: FittedBackbones, X: np.ndarray) -> dict[str, np.ndarray]:
    Xs = backbones.scaler.transform(X)
    return {
        "isolation_forest": -backbones.isolation_forest.decision_function(Xs),
        "lof": -backbones.lof.decision_function(Xs),
        "autoencoder": ae_scores(backbones.autoencoder, Xs),
    }


def _normalize(raw: np.ndarray, lo: float, hi: float) -> np.ndarray:
    if hi - lo < 1e-12:
        return np.zeros_like(raw)
    return np.clip((raw - lo) / (hi - lo), 0.0, 1.0)


def calibrate(backbones: FittedBackbones, X_ref: np.ndarray) -> FittedBackbones:
    raw = raw_scores(backbones, X_ref)
    for name, arr in raw.items():
        backbones.score_min[name] = float(arr.min())
        backbones.score_max[name] = float(arr.max())
    return backbones


def score_matrix(backbones: FittedBackbones, X: np.ndarray) -> dict[str, np.ndarray]:
    raw = raw_scores(backbones, X)
    if not backbones.score_min:
        # Fallback: batch-local minmax (tests / before calibrate)
        def mm(a: np.ndarray) -> np.ndarray:
            lo, hi = float(a.min()), float(a.max())
            return _normalize(a, lo, hi)

        if_n, lof_n, ae_n = mm(raw["isolation_forest"]), mm(raw["lof"]), mm(raw["autoencoder"])
    else:
        if_n = _normalize(
            raw["isolation_forest"],
            backbones.score_min["isolation_forest"],
            backbones.score_max["isolation_forest"],
        )
        lof_n = _normalize(raw["lof"], backbones.score_min["lof"], backbones.score_max["lof"])
        ae_n = _normalize(
            raw["autoencoder"],
            backbones.score_min["autoencoder"],
            backbones.score_max["autoencoder"],
        )

    ensemble = (if_n + lof_n + ae_n) / 3.0
    return {
        "isolation_forest": if_n,
        "lof": lof_n,
        "autoencoder": ae_n,
        "ensemble": ensemble,
    }
