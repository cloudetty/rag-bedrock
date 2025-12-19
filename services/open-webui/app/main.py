import json
import os
from html import escape as html_escape

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

OPENAI_API_BASE_URL = os.environ.get("OPENAI_API_BASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_BASE_URL:
    raise RuntimeError("OPENAI_API_BASE_URL is required")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY (shared gateway API key) is required")

APP_TITLE = os.environ.get("APP_TITLE", "Bedrock Chat")
APP_TAGLINE = os.environ.get("APP_TAGLINE", "Clean chat UI for Bedrock models")
DEFAULT_SYSTEM_PROMPT = os.environ.get("DEFAULT_SYSTEM_PROMPT", "You are a helpful assistant.")

DEFAULT_MODEL_PRIORITY = [
    "anthropic.claude-3-5-sonnet",
    "anthropic.claude-3-opus",
    "anthropic.claude-3-5-haiku",
    "amazon.nova-pro",
    "amazon.nova-lite",
    "meta.llama3-70b-instruct",
    "meta.llama3-8b-instruct",
    "mistral.large",
    "mistral.medium",
    "cohere.command",
    "amazon.titan-text",
]

preferred_from_env = [
    entry.strip()
    for entry in os.environ.get("PREFERRED_MODEL_IDS", "").split(",")
    if entry.strip()
]

PREFERRED_MODEL_IDS = preferred_from_env + [
    model for model in DEFAULT_MODEL_PRIORITY if model not in preferred_from_env
]

CONFIG = {
    "appTitle": APP_TITLE,
    "appTagline": APP_TAGLINE,
    "defaultSystemPrompt": DEFAULT_SYSTEM_PROMPT,
    "preferredModels": PREFERRED_MODEL_IDS,
}

BACKEND_URL = OPENAI_API_BASE_URL.rstrip("/")

app = FastAPI(title="Bedrock Chat UI", version="0.3.0")
client = httpx.AsyncClient(timeout=20.0)


@app.on_event("shutdown")
async def cleanup_client():
    await client.aclose()


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    html_page = RAW_HTML_PAGE.replace("{{APP_TITLE}}", html_escape(APP_TITLE))
    html_page = html_page.replace("{{APP_TAGLINE}}", html_escape(APP_TAGLINE))
    html_page = html_page.replace("{{CONFIG_JSON}}", json.dumps(CONFIG))
    return html_page


@app.get("/api/models")
async def proxy_models():
    try:
        response = await client.get(
            f"{BACKEND_URL}/models",
            headers={"x-openwebui-api-key": OPENAI_API_KEY},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

    return JSONResponse(content=response.json())


@app.post("/api/completions")
async def proxy_completion(payload: dict):
    try:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/completions",
            headers={"x-openwebui-api-key": OPENAI_API_KEY},
            json=payload,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

    return JSONResponse(content=response.json())


RAW_HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{{APP_TITLE}}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        color-scheme: dark;
        --bg: #0b0d11;
        --panel: #151923;
        --panel-strong: #1b212e;
        --border: rgba(255, 255, 255, 0.08);
        --muted: #a2aab8;
        --text: #f1f5f9;
        --accent: #f97316;
        --accent-soft: rgba(249, 115, 22, 0.16);
        --accent-2: #22c55e;
        --shadow: 0 40px 90px rgba(5, 8, 15, 0.55);
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
        background: radial-gradient(circle at 20% 20%, rgba(34, 197, 94, 0.15), transparent 45%),
          radial-gradient(circle at 80% 0%, rgba(249, 115, 22, 0.2), transparent 55%),
          linear-gradient(160deg, #0b0d11 0%, #0f131c 55%, #0b0d11 100%);
        color: var(--text);
        padding: 32px 16px 48px;
      }
      body::before,
      body::after {
        content: "";
        position: fixed;
        width: 360px;
        height: 360px;
        border-radius: 50%;
        filter: blur(0px);
        opacity: 0.24;
        z-index: 0;
      }
      body::before {
        background: radial-gradient(circle, rgba(249, 115, 22, 0.6), transparent 70%);
        top: -120px;
        left: -60px;
      }
      body::after {
        background: radial-gradient(circle, rgba(34, 197, 94, 0.55), transparent 70%);
        bottom: -140px;
        right: -40px;
      }
      main {
        position: relative;
        z-index: 1;
        width: min(1200px, 100%);
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 22px;
        animation: floatIn 0.6s ease forwards;
      }
      @keyframes floatIn {
        from {
          opacity: 0;
          transform: translateY(18px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      header {
        display: flex;
        gap: 16px;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
      }
      .title-block {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .eyebrow {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.25em;
        color: var(--muted);
      }
      h1 {
        margin: 0;
        font-size: clamp(26px, 3vw, 34px);
        letter-spacing: -0.02em;
      }
      .subtitle {
        margin: 0;
        color: var(--muted);
        font-size: 15px;
      }
      .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        font-size: 13px;
        font-weight: 600;
        color: var(--muted);
      }
      .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--accent-2);
        box-shadow: 0 0 0 5px rgba(34, 197, 94, 0.15);
      }
      .status-pill.error .status-dot {
        background: #ef4444;
        box-shadow: 0 0 0 5px rgba(239, 68, 68, 0.16);
      }
      .grid {
        display: grid;
        grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
        gap: 20px;
        align-items: start;
      }
      .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
      }
      .controls {
        display: flex;
        flex-direction: column;
        gap: 18px;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      label {
        font-weight: 600;
        font-size: 14px;
      }
      select,
      textarea,
      input[type="range"] {
        width: 100%;
      }
      select,
      textarea,
      input[type="text"] {
        border-radius: 12px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.04);
        color: var(--text);
        padding: 12px 14px;
        font-size: 15px;
        outline: none;
      }
      select:focus,
      textarea:focus,
      input[type="text"]:focus {
        border-color: rgba(249, 115, 22, 0.6);
        box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.15);
      }
      textarea {
        min-height: 90px;
        max-height: 220px;
        resize: vertical;
        line-height: 1.5;
      }
      .range-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      input[type="range"] {
        accent-color: var(--accent);
      }
      .range-value {
        font-size: 13px;
        color: var(--muted);
        font-weight: 600;
      }
      .helper {
        font-size: 13px;
        color: var(--muted);
      }
      .model-meta {
        font-size: 12px;
        color: var(--muted);
        line-height: 1.5;
      }
      .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .chip {
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.04);
        color: var(--text);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 12px;
        cursor: pointer;
        transition: border-color 0.15s ease, transform 0.1s ease;
      }
      .chip:hover {
        border-color: rgba(249, 115, 22, 0.4);
        transform: translateY(-1px);
      }
      .chat-panel {
        display: flex;
        flex-direction: column;
        gap: 16px;
        min-height: 520px;
      }
      #chat {
        display: flex;
        flex-direction: column;
        gap: 14px;
        max-height: 460px;
        overflow-y: auto;
        padding-right: 6px;
      }
      .empty-state {
        text-align: center;
        color: var(--muted);
        padding: 48px 12px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
        border-radius: 14px;
      }
      .message {
        display: grid;
        grid-template-columns: 52px 1fr;
        gap: 12px;
        align-items: start;
        animation: fadeUp 0.3s ease var(--delay, 0ms) both;
      }
      @keyframes fadeUp {
        from {
          opacity: 0;
          transform: translateY(8px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .avatar {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        color: #0b0d11;
      }
      .message.user .avatar {
        background: linear-gradient(135deg, #fbbf24, #f97316);
      }
      .message.assistant .avatar {
        background: linear-gradient(135deg, #34d399, #22c55e);
      }
      .bubble {
        border-radius: 16px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.04);
        padding: 12px 14px;
        line-height: 1.6;
      }
      .message.assistant .bubble {
        background: linear-gradient(145deg, rgba(34, 197, 94, 0.14), rgba(15, 23, 42, 0.7));
        border-color: rgba(34, 197, 94, 0.4);
      }
      .bubble.pending {
        color: var(--muted);
        font-style: italic;
      }
      .meta {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--muted);
        margin-bottom: 6px;
      }
      .composer {
        display: flex;
        flex-direction: column;
        gap: 12px;
        border-top: 1px solid var(--border);
        padding-top: 14px;
      }
      .composer textarea {
        min-height: 70px;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }
      button {
        border: none;
        border-radius: 12px;
        padding: 12px 18px;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.1s ease, box-shadow 0.15s ease, opacity 0.2s ease;
      }
      button.primary {
        background: linear-gradient(135deg, #f97316, #fbbf24);
        color: #111827;
        box-shadow: 0 14px 30px rgba(249, 115, 22, 0.25);
      }
      button.secondary {
        background: rgba(255, 255, 255, 0.08);
        color: var(--text);
        border: 1px solid var(--border);
      }
      button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        box-shadow: none;
      }
      button:active {
        transform: translateY(1px);
      }
      details {
        border-radius: 16px;
        background: var(--panel-strong);
        border: 1px solid var(--border);
        padding: 14px;
      }
      summary {
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
      }
      pre {
        font-family: "JetBrains Mono", monospace;
        font-size: 12px;
        background: #0b0f16;
        color: #d6dbe6;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 320px;
        overflow-y: auto;
      }
      .footer-note {
        font-size: 12px;
        color: var(--muted);
        margin-top: 8px;
      }
      @media (max-width: 960px) {
        .grid {
          grid-template-columns: 1fr;
        }
        #chat {
          max-height: 380px;
        }
      }
      @media (max-width: 640px) {
        body {
          padding: 24px 12px 36px;
        }
        .message {
          grid-template-columns: 1fr;
        }
        .avatar {
          width: 38px;
          height: 38px;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        * {
          animation: none !important;
          transition: none !important;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <div class="title-block">
          <div class="eyebrow">Bedrock UI</div>
          <h1>{{APP_TITLE}}</h1>
          <p class="subtitle">{{APP_TAGLINE}}</p>
        </div>
        <div class="status-pill" id="status-pill">
          <span class="status-dot"></span>
          <span id="status-text">Ready</span>
        </div>
      </header>

      <section class="grid">
        <aside class="panel controls">
          <div class="field">
            <label for="model">Model</label>
            <select id="model" aria-label="Choose a Bedrock model"></select>
            <div class="helper" id="model-hint">Loading models...</div>
            <div class="model-meta" id="model-meta"></div>
          </div>

          <div class="field">
            <label for="temperature">Temperature</label>
            <div class="range-wrap">
              <input id="temperature" type="range" min="0" max="1" step="0.05" />
              <span class="range-value" id="temperature-value">0.3</span>
            </div>
          </div>

          <div class="field">
            <label for="system">System prompt</label>
            <textarea id="system" placeholder="Optional tone or role. Example: You are concise."></textarea>
          </div>

          <div class="field">
            <label>Quick prompts</label>
            <div class="chip-row" id="prompt-chips"></div>
          </div>

          <div class="field">
            <label>Session</label>
            <div class="actions">
              <button class="secondary" id="clear-chat" type="button">New chat</button>
              <button class="secondary" id="save-chat" type="button">Save transcript</button>
            </div>
          </div>
        </aside>

        <section class="panel chat-panel">
          <div id="chat" role="log" aria-live="polite">
            <div class="empty-state" id="empty-state">
              Start a conversation. The assistant response will appear here.
            </div>
          </div>

          <div class="composer">
            <label for="prompt" style="display:none;">Message</label>
            <textarea
              id="prompt"
              rows="3"
              placeholder="Ask a question. Press Shift+Enter for a new line."
            ></textarea>
            <div class="actions">
              <button class="primary" id="run" type="button">Send</button>
            </div>
          </div>
        </section>
      </section>

      <details class="panel" open>
        <summary>Response details</summary>
        <pre id="output" aria-live="polite">Responses will appear here.</pre>
        <div class="footer-note">Raw gateway response for debugging.</div>
      </details>
    </main>

    <script>
      const CONFIG = {{CONFIG_JSON}};

      const modelsSelect = document.getElementById("model");
      const output = document.getElementById("output");
      const runButton = document.getElementById("run");
      const promptField = document.getElementById("prompt");
      const systemField = document.getElementById("system");
      const chatContainer = document.getElementById("chat");
      const emptyState = document.getElementById("empty-state");
      const statusPill = document.getElementById("status-pill");
      const statusText = document.getElementById("status-text");
      const modelHint = document.getElementById("model-hint");
      const modelMeta = document.getElementById("model-meta");
      const temperatureInput = document.getElementById("temperature");
      const temperatureValue = document.getElementById("temperature-value");
      const clearButton = document.getElementById("clear-chat");
      const saveButton = document.getElementById("save-chat");
      const promptChips = document.getElementById("prompt-chips");

      const STORAGE_KEY = "bedrock-chat-state-v1";
      const state = {
        models: [],
        history: [],
        temperature: 0.3,
        systemPrompt: CONFIG.defaultSystemPrompt || "",
        modelId: "",
      };
      let recommendedModelId = "";
      const storage = {
        get(key) {
          try {
            return window.localStorage ? localStorage.getItem(key) : null;
          } catch (err) {
            return null;
          }
        },
        set(key, value) {
          try {
            if (window.localStorage) {
              localStorage.setItem(key, value);
            }
          } catch (err) {
            // Ignore storage failures (private mode, blocked storage, quota, etc.).
          }
        },
      };

      const quickPrompts = [
        "Summarize this in three bullet points.",
        "Draft a short email reply.",
        "Explain this like I am five.",
        "Give me a checklist for a launch.",
      ];

      function setStatus(message, isError = false) {
        statusText.textContent = message;
        statusPill.classList.toggle("error", isError);
      }

      function reportError(message) {
        output.textContent = message;
        setStatus("Client error", true);
      }

      function saveState() {
        const payload = {
          history: state.history,
          temperature: state.temperature,
          systemPrompt: state.systemPrompt,
          modelId: state.modelId,
        };
        storage.set(STORAGE_KEY, JSON.stringify(payload));
      }

      function loadState() {
        const raw = storage.get(STORAGE_KEY);
        if (!raw) {
          return;
        }
        try {
          const stored = JSON.parse(raw);
          state.history = Array.isArray(stored.history) ? stored.history : [];
          state.temperature = typeof stored.temperature === "number" ? stored.temperature : 0.3;
          state.systemPrompt = stored.systemPrompt || "";
          state.modelId = stored.modelId || "";
        } catch (err) {
          console.warn("Failed to load stored state", err);
        }
      }

      function renderChat() {
        chatContainer.innerHTML = "";
        const recent = state.history.slice(-80);
        if (!recent.length) {
          chatContainer.appendChild(emptyState);
        } else {
          recent.forEach((msg, index) => {
            const row = document.createElement("div");
            row.className = `message ${msg.role}`;
            row.style.setProperty("--delay", `${index * 20}ms`);

            const avatar = document.createElement("div");
            avatar.className = "avatar";
            avatar.textContent = msg.role === "user" ? "YOU" : "AI";

            const bubble = document.createElement("div");
            bubble.className = "bubble" + (msg.pending ? " pending" : "");

            const meta = document.createElement("div");
            meta.className = "meta";
            meta.textContent = msg.role === "user" ? "User" : "Assistant";

            const text = document.createElement("div");
            text.textContent = msg.content || "";

            bubble.appendChild(meta);
            bubble.appendChild(text);
            row.appendChild(avatar);
            row.appendChild(bubble);
            chatContainer.appendChild(row);
          });
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }

      function renderChips() {
        promptChips.innerHTML = "";
        quickPrompts.forEach((text) => {
          const chip = document.createElement("button");
          chip.className = "chip";
          chip.type = "button";
          chip.textContent = text;
          chip.addEventListener("click", () => {
            promptField.value = text;
            promptField.focus();
            autoResize(promptField);
          });
          promptChips.appendChild(chip);
        });
      }

      function updateTemperature(value) {
        const clamped = Math.min(1, Math.max(0, value));
        state.temperature = clamped;
        temperatureInput.value = clamped;
        temperatureValue.textContent = clamped.toFixed(2);
        saveState();
      }

      function autoResize(textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`;
      }

      function normalizeModels(entries) {
        return entries
          .map((entry) => {
            const modelId = entry.modelId || entry.model_id || entry.id || "";
            return {
              id: modelId,
              name: entry.modelName || entry.name || modelId,
              provider: entry.providerName || entry.provider || "",
              inputModalities: entry.inputModalities || [],
              outputModalities: entry.outputModalities || [],
              inferenceTypes: entry.inferenceTypesSupported || [],
              raw: entry,
            };
          })
          .filter((entry) => entry.id);
      }

      function scoreModel(model) {
        const id = model.id || "";
        let score = 0;
        (CONFIG.preferredModels || []).forEach((key, index) => {
          if (id.includes(key)) {
            score = Math.max(score, 1000 - index * 10);
          }
        });
        if (/(70b|xlarge|xl|large|pro|opus)/i.test(id)) {
          score += 25;
        }
        if (/(8b|small|lite|haiku)/i.test(id)) {
          score -= 10;
        }
        if (model.inferenceTypes.includes("ON_DEMAND")) {
          score += 5;
        }
        return score;
      }

      function rankModels(models) {
        return [...models].sort((a, b) => {
          const diff = scoreModel(b) - scoreModel(a);
          if (diff !== 0) return diff;
          return a.name.localeCompare(b.name);
        });
      }

      function updateModelMeta(selectedId) {
        const model = state.models.find((entry) => entry.id === selectedId);
        if (!model) {
          modelMeta.textContent = "";
          return;
        }
        const parts = [];
        if (model.provider) parts.push(`Provider: ${model.provider}`);
        if (model.outputModalities?.length) parts.push(`Output: ${model.outputModalities.join(", ")}`);
        if (model.inferenceTypes?.length) parts.push(`Inference: ${model.inferenceTypes.join(", ")}`);
        modelMeta.textContent = parts.join(" | ");
      }

      async function loadModels() {
        try {
          setStatus("Loading models...");
          const response = await fetch("/api/models");
          if (!response.ok) {
            throw new Error(await response.text());
          }
          const data = await response.json();
          const entries = data.models || data.modelSummaries || [];

          const normalized = normalizeModels(entries);
          const filtered = normalized.filter((entry) => {
            if (!entry.outputModalities?.length) return true;
            const outputs = entry.outputModalities;
            const inference = entry.inferenceTypes || [];
            const isTextCapable = outputs.includes("TEXT");
            const isOnDemand = inference.includes("ON_DEMAND") || !inference.length;
            return isTextCapable && isOnDemand;
          });

          state.models = rankModels(filtered.length ? filtered : normalized);
          modelsSelect.innerHTML = "";

          state.models.forEach((entry, index) => {
            const option = document.createElement("option");
            option.value = entry.id;
            const provider = entry.provider ? ` - ${entry.provider}` : "";
            option.textContent = `${entry.name || entry.id}${provider}`;
            if (index === 0) {
              option.dataset.recommended = "true";
            }
            modelsSelect.appendChild(option);
          });

          if (!state.models.length) {
            const option = document.createElement("option");
            option.textContent = "No models found";
            option.disabled = true;
            modelsSelect.appendChild(option);
            setStatus("No models found", true);
            return;
          }

          recommendedModelId = state.models[0].id;
          const storedModel = state.modelId && state.models.find((m) => m.id === state.modelId);
          modelsSelect.value = storedModel ? state.modelId : recommendedModelId;
          state.modelId = modelsSelect.value;
          modelHint.textContent =
            state.modelId === recommendedModelId
              ? "Recommended model selected."
              : `Recommended: ${recommendedModelId}`;
          updateModelMeta(state.modelId);
          setStatus("Ready");
          saveState();
        } catch (err) {
          output.textContent = "Failed to load models: " + err.message;
          setStatus("Model load failed", true);
        }
      }

      function extractAssistantText(payload) {
        if (!payload) return "";
        const body = payload.body || payload;
        if (!body) return "";
        if (typeof body === "string") return body;
        if (body.generation) return body.generation;
        if (body.output) return body.output;
        if (Array.isArray(body.choices) && body.choices[0]) {
          const choice = body.choices[0];
          if (choice.message?.content) return choice.message.content;
          if (choice.text) return choice.text;
        }
        if (Array.isArray(body.outputs) && body.outputs[0]?.text) return body.outputs[0].text;
        if (Array.isArray(body.results) && body.results[0]?.outputText) return body.results[0].outputText;
        if (Array.isArray(body.generations) && body.generations[0]?.text) return body.generations[0].text;
        if (body.completion) return body.completion;
        if (body.message?.content) return body.message.content;
        if (Array.isArray(body.content)) {
          return body.content.map((part) => part.text || part.outputText || "").join("");
        }
        if (body.outputText) return body.outputText;
        return "";
      }

      async function runPrompt() {
        const modelId = modelsSelect.value;
        if (!modelId) {
          output.textContent = "Select a model before sending.";
          setStatus("Select a model", true);
          return;
        }

        const userMessage = promptField.value.trim();
        if (!userMessage) {
          output.textContent = "Type a message before sending.";
          setStatus("Nothing to send", true);
          return;
        }

        state.history.push({ role: "user", content: userMessage });
        const pending = { role: "assistant", content: "Thinking...", pending: true };
        state.history.push(pending);
        renderChat();
        promptField.value = "";
        autoResize(promptField);

        runButton.disabled = true;
        runButton.textContent = "Sending...";
        setStatus("Waiting for the gateway...");
        output.textContent = "Awaiting response...";

        try {
          const messages = state.history.filter((msg) => !msg.pending);
          if (state.systemPrompt) {
            messages.unshift({ role: "system", content: state.systemPrompt });
          }

          const response = await fetch("/api/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              modelId,
              messages,
              temperature: state.temperature,
            }),
          });

          if (!response.ok) {
            throw new Error(await response.text());
          }

          const data = await response.json();
          const text = extractAssistantText(data) || "No text returned. See response details.";
          pending.content = text;
          pending.pending = false;
          renderChat();
          output.textContent = JSON.stringify(data, null, 2);
          setStatus("Ready");
          saveState();
        } catch (err) {
          pending.content = "Request failed. See response details.";
          pending.pending = false;
          renderChat();
          output.textContent = "Request failed: " + err.message;
          setStatus("Request failed", true);
        } finally {
          runButton.disabled = false;
          runButton.textContent = "Send";
        }
      }

      function clearChat() {
        state.history = [];
        renderChat();
        saveState();
        setStatus("New chat started");
      }

      function saveTranscript() {
        if (!state.history.length) {
          setStatus("Nothing to save", true);
          return;
        }
        const lines = state.history.map((msg) => `${msg.role.toUpperCase()}: ${msg.content}`);
        const blob = new Blob([lines.join("\n\n")], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        const timestamp = new Date().toISOString().replace(/[:]/g, "-").slice(0, 19);
        link.download = `chat-${timestamp}.txt`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        setStatus("Transcript saved");
      }

      function updateSystemPrompt(value) {
        state.systemPrompt = value;
        saveState();
      }

      function handleModelChange() {
        state.modelId = modelsSelect.value;
        updateModelMeta(state.modelId);
        if (recommendedModelId) {
          modelHint.textContent =
            state.modelId === recommendedModelId
              ? "Recommended model selected."
              : `Recommended: ${recommendedModelId}`;
        }
        saveState();
      }

      function init() {
        loadState();
        renderChat();
        renderChips();
        systemField.value = state.systemPrompt;
        updateTemperature(state.temperature || 0.3);
        autoResize(promptField);
        loadModels();
      }

      window.addEventListener("error", (event) => {
        reportError(`Client error: ${event.message}`);
      });
      window.addEventListener("unhandledrejection", (event) => {
        const message = event.reason?.message || String(event.reason || "Unknown error");
        reportError(`Client error: ${message}`);
      });

      runButton.addEventListener("click", runPrompt);
      promptField.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          runPrompt();
        }
      });
      promptField.addEventListener("input", () => autoResize(promptField));
      systemField.addEventListener("input", (event) => updateSystemPrompt(event.target.value));
      modelsSelect.addEventListener("change", handleModelChange);
      temperatureInput.addEventListener("input", (event) => updateTemperature(Number(event.target.value)));
      clearButton.addEventListener("click", clearChat);
      saveButton.addEventListener("click", saveTranscript);

      init();
    </script>
  </body>
</html>
"""
