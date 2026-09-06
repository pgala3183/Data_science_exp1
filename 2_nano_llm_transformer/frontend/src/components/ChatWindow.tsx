import type { FormEvent } from "react";
import type { ChatMessage } from "../types";

type Props = {
  messages: ChatMessage[];
  input: string;
  streaming: boolean;
  onInput: (v: string) => void;
  onSend: () => void;
  onClear: () => void;
};

export function ChatWindow({ messages, input, streaming, onInput, onSend, onClear }: Props) {
  function submit(e: FormEvent) {
    e.preventDefault();
    onSend();
  }

  return (
    <section className="panel chat" aria-label="Chat">
      <div className="messages" role="log" aria-live="polite">
        {messages.length === 0 && (
          <p className="empty">
            Ask something simple — this is a few-million-parameter character model, not GPT-4.
            Try: “Say hello.” or “Name a Shakespeare play.”
          </p>
        )}
        {messages.map((m) => (
          <article key={m.id} className={`bubble ${m.role}`}>
            <header>{m.role}</header>
            <p>{m.content || (streaming && m.role === "assistant" ? "…" : "")}</p>
          </article>
        ))}
      </div>
      <form className="composer" onSubmit={submit}>
        <label htmlFor="prompt" className="sr-only">
          Prompt
        </label>
        <textarea
          id="prompt"
          rows={2}
          value={input}
          onChange={(e) => onInput(e.target.value)}
          placeholder="Type a prompt…"
          disabled={streaming}
        />
        <div className="composer-actions">
          <button type="submit" className="btn primary" disabled={streaming || !input.trim()}>
            {streaming ? "Streaming…" : "Send"}
          </button>
          <button type="button" className="btn" onClick={onClear} disabled={streaming}>
            Clear
          </button>
        </div>
      </form>
    </section>
  );
}
