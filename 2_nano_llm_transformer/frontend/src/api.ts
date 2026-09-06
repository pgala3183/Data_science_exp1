import type { AttentionPayload, GenSettings, ModelInfo } from "./types";

export async function fetchModelInfo(): Promise<ModelInfo> {
  const res = await fetch("/api/model/info");
  if (!res.ok) throw new Error("Model not ready — train checkpoints first");
  return res.json();
}

export async function fetchAttention(): Promise<AttentionPayload> {
  const res = await fetch("/api/model/attention");
  if (!res.ok) throw new Error("No attention yet");
  return res.json();
}

/** Parse SSE from a POST /generate response body. */
export async function streamGenerate(
  prompt: string,
  settings: GenSettings,
  onToken: (piece: string, full: string) => void,
  onDone: (full: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      prompt,
      temperature: settings.temperature,
      top_p: settings.top_p,
      top_k: settings.top_k,
      max_tokens: settings.max_tokens,
      chat: true,
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    const err = await res.text();
    throw new Error(err || `Generate failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n");
    buffer = chunks.pop() ?? "";

    for (const line of chunks) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const data = line.slice(5).trim();
        try {
          const parsed = JSON.parse(data) as { token?: string; text?: string };
          if (eventName === "token" && parsed.token != null && parsed.text != null) {
            onToken(parsed.token, parsed.text);
          } else if (eventName === "done") {
            onDone(parsed.text ?? "");
          }
        } catch {
          // ignore keepalive / partial
        }
        eventName = "message";
      }
    }
  }
}
