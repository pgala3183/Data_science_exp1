import type { FormEvent } from "react";

type Props = {
  datetime: string;
  passengers: number;
  selecting: "pickup" | "dropoff";
  canPredict: boolean;
  loading: boolean;
  onDatetimeChange: (v: string) => void;
  onPassengersChange: (v: number) => void;
  onSelectingChange: (v: "pickup" | "dropoff") => void;
  onPredict: () => void;
  onClear: () => void;
};

export function TripForm({
  datetime,
  passengers,
  selecting,
  canPredict,
  loading,
  onDatetimeChange,
  onPassengersChange,
  onSelectingChange,
  onPredict,
  onClear,
}: Props) {
  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onPredict();
  }

  return (
    <form className="panel form" onSubmit={handleSubmit} aria-labelledby="trip-form-title">
      <h2 id="trip-form-title">Trip inputs</h2>

      <fieldset>
        <legend>Map click mode</legend>
        <div className="segmented" role="group" aria-label="Point to place on map">
          <button
            type="button"
            className={selecting === "pickup" ? "active" : ""}
            aria-pressed={selecting === "pickup"}
            onClick={() => onSelectingChange("pickup")}
          >
            Pickup
          </button>
          <button
            type="button"
            className={selecting === "dropoff" ? "active" : ""}
            aria-pressed={selecting === "dropoff"}
            onClick={() => onSelectingChange("dropoff")}
          >
            Dropoff
          </button>
        </div>
      </fieldset>

      <div className="field">
        <label htmlFor="pickup-datetime">Pickup date &amp; time</label>
        <input
          id="pickup-datetime"
          type="datetime-local"
          value={datetime}
          onChange={(e) => onDatetimeChange(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="passengers">Passenger count</label>
        <input
          id="passengers"
          type="number"
          min={1}
          max={6}
          value={passengers}
          onChange={(e) => onPassengersChange(Number(e.target.value))}
          required
        />
      </div>

      <div className="actions">
        <button type="submit" className="btn primary" disabled={!canPredict || loading}>
          {loading ? "Predicting…" : "Predict duration"}
        </button>
        <button type="button" className="btn" onClick={onClear}>
          Clear points
        </button>
      </div>
    </form>
  );
}
