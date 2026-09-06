import { useEffect, useState } from "react";
import { fetchAcfPacf, fetchBacktest, fetchForecast } from "./api";
import { AcfPacfCharts } from "./components/AcfPacfCharts";
import { BacktestTable } from "./components/BacktestTable";
import { ForecastFan } from "./components/ForecastFan";
import type { AcfPacfResponse, BacktestResponse, ForecastResponse } from "./types";
import "./styles.css";

export default function App() {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [acf, setAcf] = useState<AcfPacfResponse | null>(null);
  const [backtest, setBacktest] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchForecast(), fetchAcfPacf(), fetchBacktest()])
      .then(([fc, ac, bt]) => {
        setForecast(fc);
        setAcf(ac);
        setBacktest(bt);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 12</p>
        <h1>Time Series Forecasting</h1>
        <p className="lede">
          Multi-horizon retail sales forecasts with SARIMA and lag-feature gradient
          boosting — evaluated by rolling-origin backtest, not random splits.
        </p>
        {forecast && (
          <p className="meta">
            last train={forecast.last_train_ds} · models=
            {forecast.forecasts.map((f) => f.model).join(", ")} · α={forecast.alpha}
          </p>
        )}
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!forecast && !error && (
        <p className="muted">Loading ACF/PACF, forecasts, and backtest…</p>
      )}

      {acf && <AcfPacfCharts data={acf} />}
      {forecast && <ForecastFan data={forecast} />}
      {backtest && <BacktestTable data={backtest} />}
    </div>
  );
}
