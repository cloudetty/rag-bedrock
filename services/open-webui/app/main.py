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
      body {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        min-height: 100vh;
        background: #0d1117;
        color: #c9d1d9;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 1.5rem;
      }
      main {
        width: min(800px, 100%);
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5);
      }
      label {
        display: block;
        margin-bottom: 0.75rem;
        font-weight: 600;
      }
      select,
      textarea {
        width: 100%;
        border-radius: 6px;
        border: 1px solid #30363d;
        background: #0d1117;
        color: #c9d1d9;
        padding: 0.75rem;
        font-size: 1rem;
        resize: vertical;
      }
      button {
        margin-top: 1rem;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        border: none;
        background: linear-gradient(135deg, #238636, #2ea043);
        color: white;
        font-weight: 600;
        cursor: pointer;
      }
      pre {
        white-space: pre-wrap;
        word-break: break-word;
        margin-top: 1rem;
        background: #0b1220;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        max-height: 320px;
        overflow-y: auto;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Open WebUI</h1>
      <p>Send prompts to Bedrock via the gateway to see model outputs.</p>
      <label for="model">Model</label>
      <select id="model" aria-label="Choose a Bedrock model"></select>

      <label for="prompt">Prompt</label>
      <textarea
        id="prompt"
        rows="6"
        placeholder="Write a short story or ask a question..."
      ></textarea>

      <button id="run" type="button">Submit</button>

      <pre id="output" aria-live="polite"></pre>
    </main>

    <script>
      const modelsSelect = document.getElementById("model");
      const output = document.getElementById("output");
      const runButton = document.getElementById("run");
      const promptField = document.getElementById("prompt");

      async function loadModels() {
        try {
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
        } catch (err) {
          output.textContent = "Failed to load models: " + err.message;
        }
      }

      async function runPrompt() {
        const modelId = modelsSelect.value;
        if (!modelId) {
          output.textContent = "Select a model before submitting.";
          return;
        }

        runButton.disabled = true;
        runButton.textContent = "Sending...";
        output.textContent = "Waiting for the gateway...";

        try {
          const response = await fetch("/api/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              modelId,
              prompt: promptField.value.trim() || "Hello from Open WebUI",
            }),
          });

          if (!response.ok) {
            throw new Error(await response.text());
          }

          const data = await response.json();
          output.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          output.textContent = "Request failed: " + err.message;
        } finally {
          runButton.disabled = false;
          runButton.textContent = "Submit";
        }
      }

      runButton.addEventListener("click", runPrompt);
      loadModels();
    </script>
  </body>
</html>
"""
