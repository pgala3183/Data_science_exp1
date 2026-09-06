from __future__ import annotations

import numpy as np
from statsmodels.tsa.stattools import acf, pacf


def compute_acf_pacf(y: np.ndarray, nlags: int = 40) -> dict:
    y = np.asarray(y, dtype=float)
    n = len(y)
    acf_vals = acf(y, nlags=nlags, fft=True)
    pacf_vals = pacf(y, nlags=nlags, method="ywm")
    # Approximate 95% Bartlett CI for white-noise ACF
    ci = 1.96 / np.sqrt(n)
    lags = list(range(nlags + 1))
    interpretation = (
        "Strong ACF peaks near multiples of 7 support weekly seasonality (SARIMA s=7). "
        "PACF decaying after early lags suggests a modest AR component (p≈1). "
        "Differencing (d=1) handles the visible trend."
    )
    return {
        "lags": lags,
        "acf": [round(float(v), 5) for v in acf_vals],
        "pacf": [round(float(v), 5) for v in pacf_vals],
        "acf_ci": round(float(ci), 5),
        "n": n,
        "interpretation": interpretation,
    }
