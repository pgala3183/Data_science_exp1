import type { GenSettings } from "../types";

type Props = {
  settings: GenSettings;
  onChange: (s: GenSettings) => void;
};

export function SettingsPanel({ settings, onChange }: Props) {
  return (
    <section className="panel settings" aria-labelledby="settings-title">
      <h2 id="settings-title">Generation settings</h2>
      <label>
        Temperature ({settings.temperature.toFixed(2)})
        <input
          type="range"
          min={0.1}
          max={1.5}
          step={0.05}
          value={settings.temperature}
          onChange={(e) => onChange({ ...settings, temperature: Number(e.target.value) })}
        />
      </label>
      <label>
        Top-p ({settings.top_p.toFixed(2)})
        <input
          type="range"
          min={0.1}
          max={1}
          step={0.05}
          value={settings.top_p}
          onChange={(e) => onChange({ ...settings, top_p: Number(e.target.value) })}
        />
      </label>
      <label>
        Top-k ({settings.top_k})
        <input
          type="range"
          min={0}
          max={100}
          step={1}
          value={settings.top_k}
          onChange={(e) => onChange({ ...settings, top_k: Number(e.target.value) })}
        />
      </label>
      <label>
        Max tokens ({settings.max_tokens})
        <input
          type="range"
          min={16}
          max={256}
          step={8}
          value={settings.max_tokens}
          onChange={(e) => onChange({ ...settings, max_tokens: Number(e.target.value) })}
        />
      </label>
    </section>
  );
}
