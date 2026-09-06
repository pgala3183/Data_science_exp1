import type { NodeType } from "../types";
import { NODE_TYPE_META } from "../types";

const TYPES: NodeType[] = ["fetch", "transform", "train", "notify"];

interface Props {
  onAdd: (type: NodeType) => void;
  disabled?: boolean;
}

export function NodePalette({ onAdd, disabled }: Props) {
  return (
    <aside className="palette">
      <h2>Steps</h2>
      <p className="palette__hint">Click to drop a node onto the canvas.</p>
      <ul>
        {TYPES.map((type) => {
          const meta = NODE_TYPE_META[type];
          return (
            <li key={type}>
              <button
                type="button"
                className="palette__btn"
                style={{ ["--accent" as string]: meta.accent }}
                onClick={() => onAdd(type)}
                disabled={disabled}
              >
                <span className="palette__swatch" />
                <span>
                  <strong>{meta.label}</strong>
                  <small>{meta.description}</small>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
