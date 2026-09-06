import { useEffect, useState } from "react";
import { recommend } from "../api";
import type { RecommendItem } from "../types";

type Props = { catalog: string[] };

export function BasketSimulator({ catalog }: Props) {
  const [basket, setBasket] = useState<string[]>([]);
  const [pick, setPick] = useState("");
  const [recs, setRecs] = useState<RecommendItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!catalog.length) return;
    setPick(catalog[0]);
  }, [catalog]);

  useEffect(() => {
    if (basket.length === 0) {
      setRecs([]);
      return;
    }
    setLoading(true);
    setError(null);
    recommend(basket)
      .then(setRecs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"))
      .finally(() => setLoading(false));
  }, [basket]);

  function addItem() {
    if (!pick || basket.includes(pick)) return;
    setBasket((b) => [...b, pick]);
  }

  return (
    <section className="panel" aria-labelledby="sim-title">
      <h2 id="sim-title">Basket simulator</h2>
      <p className="muted">Add items; recommendations come from rules whose antecedents ⊆ your basket.</p>
      <div className="sim-controls">
        <label htmlFor="item-pick">Item</label>
        <select id="item-pick" value={pick} onChange={(e) => setPick(e.target.value)}>
          {catalog.map((item) => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <button type="button" className="btn primary" onClick={addItem}>
          Add
        </button>
        <button type="button" className="btn" onClick={() => setBasket([])}>
          Clear
        </button>
      </div>

      <ul className="chips" aria-label="Current basket">
        {basket.map((item) => (
          <li key={item}>
            <button type="button" onClick={() => setBasket((b) => b.filter((x) => x !== item))}>
              {item.replaceAll("_", " ")} ×
            </button>
          </li>
        ))}
        {basket.length === 0 && <li className="muted">Basket empty</li>}
      </ul>

      {loading && <p className="muted">Scoring add-ons…</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <h3>Recommended add-ons</h3>
      <ol className="recs">
        {recs.map((r) => (
          <li key={r.item}>
            <strong>{r.item.replaceAll("_", " ")}</strong>
            <span>
              lift {r.lift.toFixed(2)} · conf {r.confidence.toFixed(2)} · via{" "}
              {r.rule.antecedents.join(" + ")} → {r.rule.consequents.join(" + ")}
            </span>
            <button type="button" className="btn" onClick={() => setBasket((b) => [...b, r.item])}>
              Add to basket
            </button>
          </li>
        ))}
        {!loading && basket.length > 0 && recs.length === 0 && (
          <li className="muted">No matching rules — try a themed pair like pasta + tomato sauce.</li>
        )}
      </ol>
    </section>
  );
}
