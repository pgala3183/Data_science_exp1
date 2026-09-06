"""Cleaner sample project for auditor unit tests."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


def run() -> float:
    rng = np.random.default_rng(RANDOM_STATE)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] > 0).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    # basic validation
    assert X_train_s.shape[1] == 4
    assert not np.isnan(X_train_s).any()
    clf = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE)
    clf.fit(X_train_s, y_train)
    return float(clf.score(X_test_s, y_test))
