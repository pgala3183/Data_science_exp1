import { useMemo, useState, type FormEvent } from "react";
import { demoImageSrc, predictForm } from "../api";
import type { DemoSample, PredictResponse } from "../types";

type Props = {
  samples: DemoSample[];
  onResult: (r: PredictResponse) => void;
};

const empty = {
  description: "",
  price: "49.99",
  rating: "4.0",
  brand_tier: "mid",
  weight_oz: "8.0",
  is_fragile: "0",
};

export function PredictForm({ samples, onResult }: Props) {
  const [fields, setFields] = useState(empty);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const sampleChips = useMemo(() => samples.slice(0, 5), [samples]);

  function onFile(f: File | null) {
    setFile(f);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(f ? URL.createObjectURL(f) : null);
  }

  async function loadSample(s: DemoSample) {
    setFields({
      description: s.description,
      price: String(s.price),
      rating: String(s.rating),
      brand_tier: s.brand_tier,
      weight_oz: String(s.weight_oz),
      is_fragile: String(s.is_fragile),
    });
    const res = await fetch(demoImageSrc(s.image_url));
    const blob = await res.blob();
    const f = new File([blob], "demo.jpg", { type: blob.type || "image/jpeg" });
    onFile(f);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setErr("Upload a product image (or pick a demo sample).");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      fd.append("description", fields.description);
      fd.append("price", fields.price);
      fd.append("rating", fields.rating);
      fd.append("brand_tier", fields.brand_tier);
      fd.append("weight_oz", fields.weight_oz);
      fd.append("is_fragile", fields.is_fragile);
      const out = await predictForm(fd);
      onResult(out);
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Prediction failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Try a product listing</h2>
      <p className="hint">Upload image + text + tabular fields. Each modality model votes separately.</p>

      {sampleChips.length > 0 && (
        <div className="sample-row">
          <span className="sample-label">Demo hold-outs</span>
          {sampleChips.map((s, i) => (
            <button key={i} type="button" className="chip" onClick={() => void loadSample(s)}>
              {s.true_category ?? `sample ${i + 1}`}
            </button>
          ))}
        </div>
      )}

      <form className="form" onSubmit={(e) => void onSubmit(e)}>
        <label className="file-field">
          <span>Product image</span>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          {preview && <img src={preview} alt="Upload preview" className="thumb" />}
        </label>

        <label>
          <span>Description</span>
          <textarea
            rows={3}
            value={fields.description}
            onChange={(e) => setFields({ ...fields, description: e.target.value })}
            required
          />
        </label>

        <div className="grid-2">
          <label>
            <span>Price ($)</span>
            <input
              type="number"
              step="0.01"
              value={fields.price}
              onChange={(e) => setFields({ ...fields, price: e.target.value })}
              required
            />
          </label>
          <label>
            <span>Rating</span>
            <input
              type="number"
              min="1"
              max="5"
              step="0.1"
              value={fields.rating}
              onChange={(e) => setFields({ ...fields, rating: e.target.value })}
            />
          </label>
          <label>
            <span>Brand tier</span>
            <select
              value={fields.brand_tier}
              onChange={(e) => setFields({ ...fields, brand_tier: e.target.value })}
            >
              <option value="budget">budget</option>
              <option value="mid">mid</option>
              <option value="premium">premium</option>
            </select>
          </label>
          <label>
            <span>Weight (oz)</span>
            <input
              type="number"
              step="0.1"
              value={fields.weight_oz}
              onChange={(e) => setFields({ ...fields, weight_oz: e.target.value })}
            />
          </label>
          <label>
            <span>Fragile?</span>
            <select
              value={fields.is_fragile}
              onChange={(e) => setFields({ ...fields, is_fragile: e.target.value })}
            >
              <option value="0">no</option>
              <option value="1">yes</option>
            </select>
          </label>
        </div>

        {err && (
          <p className="error" role="alert">
            {err}
          </p>
        )}

        <button type="submit" className="cta" disabled={busy}>
          {busy ? "Scoring…" : "Predict category"}
        </button>
      </form>
    </section>
  );
}
