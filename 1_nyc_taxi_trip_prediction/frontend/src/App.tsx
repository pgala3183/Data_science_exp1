import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchMetrics, predictTrip } from "./api";
import { MetricsPanel } from "./components/MetricsPanel";
import { ResultCard } from "./components/ResultCard";
import { TripForm } from "./components/TripForm";
import { TripMap } from "./components/TripMap";
import type { LatLng, ModelMetrics, PredictResponse } from "./types";
import "./styles.css";

function defaultDatetimeLocal(): string {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export default function App() {
  const [pickup, setPickup] = useState<LatLng | null>(null);
  const [dropoff, setDropoff] = useState<LatLng | null>(null);
  const [selecting, setSelecting] = useState<"pickup" | "dropoff">("pickup");
  const [datetime, setDatetime] = useState(defaultDatetimeLocal);
  const [passengers, setPassengers] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);

  useEffect(() => {
    fetchMetrics()
      .then(setMetrics)
      .catch(() => setMetrics(null));
  }, []);

  const onMapClick = useCallback(
    (point: LatLng) => {
      if (selecting === "pickup") {
        setPickup(point);
        setSelecting("dropoff");
      } else {
        setDropoff(point);
      }
      setResult(null);
      setError(null);
    },
    [selecting],
  );

  const canPredict = Boolean(pickup && dropoff && datetime);

  async function onPredict() {
    if (!pickup || !dropoff) return;
    setLoading(true);
    setError(null);
    try {
      const iso = new Date(datetime).toISOString();
      const res = await predictTrip({
        pickup_latitude: pickup.lat,
        pickup_longitude: pickup.lng,
        dropoff_latitude: dropoff.lat,
        dropoff_longitude: dropoff.lng,
        pickup_datetime: iso,
        passenger_count: passengers,
      });
      setResult(res);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  const coordsSummary = useMemo(() => {
    if (!pickup && !dropoff) return "No points selected";
    const parts: string[] = [];
    if (pickup) parts.push(`P ${pickup.lat.toFixed(4)}, ${pickup.lng.toFixed(4)}`);
    if (dropoff) parts.push(`D ${dropoff.lat.toFixed(4)}, ${dropoff.lng.toFixed(4)}`);
    return parts.join(" · ");
  }, [pickup, dropoff]);

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="hero">
        <p className="eyebrow">Experiment 1 · CRISP-DM</p>
        <h1>NYC Taxi Trip Duration</h1>
        <p className="lede">
          Click pickup and dropoff on the map. Predict duration from pre-trip features only —
          distance, time-of-day, rush hour, and location clusters.
        </p>
      </header>

      <div className="layout" id="main">
        <div className="map-column">
          <TripMap
            pickup={pickup}
            dropoff={dropoff}
            selecting={selecting}
            onMapClick={onMapClick}
          />
          <p className="coords" aria-live="polite">
            {coordsSummary}
          </p>
        </div>

        <aside className="side">
          <TripForm
            datetime={datetime}
            passengers={passengers}
            selecting={selecting}
            canPredict={canPredict}
            loading={loading}
            onDatetimeChange={setDatetime}
            onPassengersChange={setPassengers}
            onSelectingChange={setSelecting}
            onPredict={() => void onPredict()}
            onClear={() => {
              setPickup(null);
              setDropoff(null);
              setSelecting("pickup");
              setResult(null);
              setError(null);
            }}
          />
          <ResultCard result={result} metrics={metrics} error={error} />
          <MetricsPanel metrics={metrics} />
        </aside>
      </div>
    </div>
  );
}
