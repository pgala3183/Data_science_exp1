import { useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { fetchAttention, fetchModelInfo, streamGenerate } from "./api";
import { AttentionHeatmap } from "./components/AttentionHeatmap";
import { ChatWindow } from "./components/ChatWindow";
import { SettingsPanel } from "./components/SettingsPanel";
import type { AttentionPayload, ChatMessage, GenSettings, ModelInfo } from "./types";
import "./styles.css";

const defaultSettings: GenSettings = {
  temperature: 0.9,
  top_p: 0.9,
  top_k: 40,
  max_tokens: 100,
};

function ChatPage({ info }: { info: ModelInfo | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [settings, setSettings] = useState<GenSettings>(defaultSettings);
  const [error, setError] = useState<string | null>(null);

  async function onSend() {
    const prompt = input.trim();
    if (!prompt || streaming) return;
    setError(null);
    setInput("");
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: prompt };
    const asstId = crypto.randomUUID();
    setMessages((m) => [...m, userMsg, { id: asstId, role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      await streamGenerate(
        prompt,
        settings,
        (_piece, full) => {
          setMessages((m) => m.map((msg) => (msg.id === asstId ? { ...msg, content: full } : msg)));
        },
        (full) => {
          setMessages((m) => m.map((msg) => (msg.id === asstId ? { ...msg, content: full } : msg)));
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="chat-layout">
      <ChatWindow
        messages={messages}
        input={input}
        streaming={streaming}
        onInput={setInput}
        onSend={() => void onSend()}
        onClear={() => setMessages([])}
      />
      <aside>
        <SettingsPanel settings={settings} onChange={setSettings} />
        {info && (
          <p className="meta-line">
            Serving <strong>{info.checkpoint}</strong> · {(info.params / 1e6).toFixed(2)}M params ·{" "}
            {info.stage}
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </aside>
    </div>
  );
}

function ArchitecturePage() {
  const [attention, setAttention] = useState<AttentionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<ModelInfo | null>(null);

  useEffect(() => {
    fetchModelInfo()
      .then(setInfo)
      .catch(() => setInfo(null));
    fetchAttention()
      .then(setAttention)
      .catch((e) => setError(e instanceof Error ? e.message : "No attention"));
  }, []);

  return (
    <div className="arch">
      <section className="panel">
        <h2>Architecture</h2>
        <ul className="arch-list">
          <li>
            <strong>Decoder-only transformer</strong> — causal LM predicting the next character.
          </li>
          <li>
            <strong>Multi-head self-attention</strong> with causal mask (no future tokens).
          </li>
          <li>
            <strong>RoPE</strong> — rotary position embeddings on Q/K (no absolute position table).
          </li>
          <li>
            <strong>SwiGLU</strong> MLP and <strong>pre-norm</strong> (RMSNorm) residuals.
          </li>
          <li>
            <strong>Weight-tied</strong> embedding / LM head. Size: a few million parameters.
          </li>
        </ul>
        {info && (
          <pre className="code-block">{JSON.stringify(info.config, null, 2)}</pre>
        )}
      </section>
      <section className="panel">
        <h2>Attention heatmap</h2>
        <AttentionHeatmap attention={attention} error={attention ? null : error} />
        <button
          type="button"
          className="btn"
          onClick={() => {
            setError(null);
            fetchAttention()
              .then(setAttention)
              .catch((e) => setError(e instanceof Error ? e.message : "No attention"));
          }}
        >
          Refresh attention
        </button>
      </section>
    </div>
  );
}

export default function App() {
  const [info, setInfo] = useState<ModelInfo | null>(null);

  useEffect(() => {
    fetchModelInfo()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  return (
    <div className="app">
      <header className="top">
        <div>
          <p className="eyebrow">Experiment 2</p>
          <h1>
            <Link to="/">Nano LLM Transformer</Link>
          </h1>
          <p className="lede">From-scratch RoPE + SwiGLU decoder · streamed character tokens</p>
        </div>
        <nav>
          <NavLink to="/" end>
            Chat
          </NavLink>
          <NavLink to="/architecture">Architecture</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<ChatPage info={info} />} />
        <Route path="/architecture" element={<ArchitecturePage />} />
      </Routes>
    </div>
  );
}
