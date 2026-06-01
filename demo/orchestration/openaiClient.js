// Minimal OpenAI client — adapted from Infinite-Summoner/frontend/forge-engine/openaiClient.js

const OPENAI_BASE = "https://api.openai.com";
export const DEFAULT_CHEAP_MODEL = "gpt-4o-mini";

async function openaiChat(apiKey, messages, opts = {}) {
  const body = {
    model: opts.model || DEFAULT_CHEAP_MODEL,
    messages,
    temperature: opts.temperature ?? 0.3,
    max_tokens: opts.max_tokens ?? 600,
  };
  if (opts.response_format) body.response_format = opts.response_format;

  const res = await fetch(`${OPENAI_BASE}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify(body),
  });
  return res;
}

function stripCodeFences(text) {
  return String(text || "").replace(/```json\n?/g, "").replace(/```/g, "").trim();
}

export function makeOpenAIChatCtx(apiKey) {
  if (!apiKey) throw new Error("makeOpenAIChatCtx: apiKey required");

  async function chatJson(messages, opts = {}) {
    const res = await openaiChat(apiKey, messages, {
      ...opts,
      response_format: opts.response_format ?? { type: "json_object" },
    });
    const raw = await res.text();
    if (!res.ok) throw new Error(`OpenAI HTTP ${res.status}: ${raw.slice(0, 200)}`);
    const json = JSON.parse(raw);
    if (json.error) throw new Error(`OpenAI API: ${json.error.message || "unknown"}`);
    const text = json.choices?.[0]?.message?.content || "";
    if (!text) return null;
    try {
      return JSON.parse(stripCodeFences(text));
    } catch (e) {
      throw new Error(`Invalid JSON from model: ${e.message}`);
    }
  }

  return { chatJson };
}
