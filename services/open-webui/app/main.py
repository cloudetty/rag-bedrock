import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

OPENAI_API_BASE_URL = os.environ.get("OPENAI_API_BASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_BASE_URL:
    raise RuntimeError("OPENAI_API_BASE_URL is required")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY (shared gateway API key) is required")

BACKEND_URL = OPENAI_API_BASE_URL.rstrip("/")

app = FastAPI(title="Open WebUI Proxy", version="0.1.0")
client = httpx.AsyncClient(timeout=15.0)


@app.on_event("shutdown")
async def cleanup_client():
    await client.aclose()


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


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


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Open WebUI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        --bg: #05060a;
        --panel: rgba(16, 18, 24, 0.9);
        --card: rgba(255, 255, 255, 0.04);
        --border: rgba(255, 255, 255, 0.08);
        --accent: #7dd3fc;
        --accent-strong: #22d3ee;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Inter", "SF Pro Display", system-ui, -apple-system, BlinkMacSystemFont,
          "Segoe UI", sans-serif;
        background: radial-gradient(1200px at 15% 20%, rgba(34, 211, 238, 0.18), transparent),
          radial-gradient(800px at 80% 0%, rgba(125, 211, 252, 0.22), transparent),
          linear-gradient(140deg, #05060a 0%, #0a0c12 60%, #05060a 100%);
        color: var(--text);
        display: flex;
        justify-content: center;
        padding: 32px 16px 48px;
      }
      main {
        width: min(1100px, 100%);
        backdrop-filter: blur(12px);
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 24px;
        box-shadow: var(--shadow);
      }
      header {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 20px;
      }
      h1 {
        margin: 0;
        font-size: 26px;
        letter-spacing: -0.02em;
      }
      .subtle {
        color: var(--muted);
        font-size: 15px;
        margin: 6px 0 0;
      }
      .badge {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(125, 211, 252, 0.16);
        color: var(--accent);
        border: 1px solid rgba(125, 211, 252, 0.3);
        font-weight: 600;
        font-size: 13px;
      }
      .controls {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
      }
      label {
        font-weight: 600;
        color: var(--text);
        font-size: 14px;
        margin-bottom: 6px;
        display: block;
      }
      select {
        width: 100%;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.02);
        color: var(--text);
        padding: 12px 14px;
        font-size: 15px;
        outline: none;
      }
      select:focus {
        border-color: rgba(125, 211, 252, 0.6);
        box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.15);
      }
      .status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        color: var(--muted);
        font-weight: 600;
        font-size: 13px;
      }
      .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.15);
      }
      .status.error .dot {
        background: #ef4444;
        box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.15);
      }
      .panel {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px;
      }
      #chat {
        min-height: 320px;
        max-height: 520px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 6px;
      }
      .placeholder {
        text-align: center;
        color: var(--muted);
        font-size: 14px;
        padding: 40px 0;
      }
      .message {
        display: flex;
        gap: 10px;
        align-items: flex-start;
      }
      .bubble {
        padding: 12px 14px;
        border-radius: 14px;
        background: var(--card);
        border: 1px solid var(--border);
        max-width: 85%;
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.5;
      }
      .role {
        min-width: 46px;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.04em;
        color: var(--muted);
        padding-top: 4px;
      }
      .assistant .bubble {
        background: linear-gradient(135deg, rgba(34, 211, 238, 0.16), rgba(125, 211, 252, 0.12));
        border-color: rgba(125, 211, 252, 0.35);
      }
      .composer {
        position: sticky;
        bottom: 0;
        margin-top: 18px;
        display: flex;
        gap: 12px;
        align-items: flex-end;
        flex-wrap: wrap;
      }
      textarea {
        flex: 1 1 420px;
        border-radius: 14px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.04);
        color: var(--text);
        padding: 12px 14px;
        font-size: 15px;
        min-height: 64px;
        max-height: 180px;
        resize: vertical;
        outline: none;
        line-height: 1.5;
      }
      textarea:focus {
        border-color: rgba(125, 211, 252, 0.6);
        box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.12);
      }
      button {
        padding: 14px 18px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, var(--accent-strong), #60a5fa);
        color: #0b0f17;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.08s ease, box-shadow 0.12s ease, opacity 0.2s;
        box-shadow: 0 10px 35px rgba(125, 211, 252, 0.25);
      }
      button:active {
        transform: translateY(1px);
      }
      button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        box-shadow: none;
      }
      details {
        margin-top: 18px;
      }
      summary {
        cursor: pointer;
        color: var(--text);
        font-weight: 700;
        margin-bottom: 8px;
      }
      pre {
        white-space: pre-wrap;
        word-break: break-word;
        margin: 0;
        background: #080b12;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
        max-height: 320px;
        overflow-y: auto;
        color: #d1d5db;
      }
      .footer-note {
        color: var(--muted);
        font-size: 12px;
        margin-top: 10px;
      }
      @media (max-width: 720px) {
        main {
          padding: 18px;
        }
        .bubble {
          max-width: 100%;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Open WebUI</h1>
          <p class="subtle">Conversational interface to Bedrock via the gateway.</p>
        </div>
        <div class="badge">Live · v0.2</div>
      </header>

      <div class="controls">
        <div>
          <label for="model">Model</label>
          <select id="model" aria-label="Choose a Bedrock model"></select>
        </div>
        <div class="status" id="status">
          <span class="dot"></span>
          <span id="status-text">Ready</span>
        </div>
      </div>

      <section class="panel" id="chat-panel" aria-live="polite">
        <div id="chat" role="log" aria-label="Conversation">
          <div class="placeholder" id="empty-state">
            No messages yet. Ask something to start the conversation.
          </div>
        </div>

        <div class="composer">
          <label for="prompt" style="display:none;">Message</label>
          <textarea
            id="prompt"
            rows="3"
            placeholder="Ask a question or press Shift+Enter for a new line..."
          ></textarea>
          <button id="run" type="button">Send</button>
        </div>
      </section>

      <details class="panel" open>
        <summary>Response details</summary>
        <pre id="output" aria-live="polite">Responses will appear here.</pre>
        <div class="footer-note">Raw gateway response for debugging.</div>
      </details>
    </main>

    <script>
      const modelsSelect = document.getElementById("model");
      const output = document.getElementById("output");
      const runButton = document.getElementById("run");
      const promptField = document.getElementById("prompt");
      const chatContainer = document.getElementById("chat");
      const emptyState = document.getElementById("empty-state");
      const statusPill = document.getElementById("status");
      const statusText = document.getElementById("status-text");
      const history = [];

      function renderChat() {
        chatContainer.innerHTML = "";
        const recent = history.slice(-50);
        if (!recent.length) {
          chatContainer.appendChild(emptyState);
        } else {
          recent.forEach((msg) => {
            const row = document.createElement("div");
            row.className = "message " + msg.role;

            const role = document.createElement("div");
            role.className = "role";
            role.textContent = msg.role === "user" ? "You" : "AI";

            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.textContent = msg.content || "";

            row.appendChild(role);
            row.appendChild(bubble);
            chatContainer.appendChild(row);
          });
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }

      function setStatus(message, isError = false) {
        statusText.textContent = message;
        statusPill.classList.toggle("error", isError);
      }

      async function loadModels() {
        try {
          setStatus("Loading models...");
          const response = await fetch("/api/models");
          const data = await response.json();
          const entries = data.models || data.modelSummaries || [];
          modelsSelect.innerHTML = "";

          entries.forEach((entry) => {
            const option = document.createElement("option");
            option.value = entry.modelId || entry.model_id || "";
            option.textContent =
              option.value || entry.name || "Unnamed model";
            modelsSelect.appendChild(option);
          });

          if (!entries.length) {
            const option = document.createElement("option");
            option.textContent = "No models found";
            option.disabled = true;
            modelsSelect.appendChild(option);
          }
          setStatus("Ready");
        } catch (err) {
          output.textContent = "Failed to load models: " + err.message;
          setStatus("Model load failed", true);
        }
      }

      async function runPrompt() {
        const modelId = modelsSelect.value;
        if (!modelId) {
          output.textContent = "Select a model before submitting.";
          setStatus("Select a model", true);
          return;
        }

        const userMessage = promptField.value.trim();
        if (!userMessage) {
          output.textContent = "Type a message before sending.";
          setStatus("Nothing to send", true);
          return;
        }

        history.push({ role: "user", content: userMessage });
        renderChat();
        promptField.value = "";

        runButton.disabled = true;
        runButton.textContent = "Sending...";
        setStatus("Waiting for the gateway...");
        output.textContent = "Awaiting response...";

        try {
          const response = await fetch("/api/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              modelId,
              messages: history,
            }),
          });

          if (!response.ok) {
            throw new Error(await response.text());
          }

          const data = await response.json();
          const text =
            data.body?.generation ||
            data.body?.output ||
            JSON.stringify(data.body || data, null, 2);
          history.push({ role: "assistant", content: text });
          renderChat();
          output.textContent = JSON.stringify(data, null, 2);
          setStatus("Ready");
        } catch (err) {
          output.textContent = "Request failed: " + err.message;
          setStatus("Request failed", true);
        } finally {
          runButton.disabled = false;
          runButton.textContent = "Send";
        }
      }

      runButton.addEventListener("click", runPrompt);
      promptField.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          runPrompt();
        }
      });
      loadModels();
    </script>
  </body>
</html>
"""
