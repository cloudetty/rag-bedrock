# Open WebUI service

FastAPI app that serves a polished browser chat UI, forwards prompts to the Bedrock gateway, and displays model responses.

## Features
- `/` serves a clean chat interface with model selection, system prompt, temperature control, and transcript export.
- `/api/models` and `/api/completions` proxy requests to the gateway using `OPENAI_API_BASE_URL` + `OPENAI_API_KEY`.
- `/healthz` for ECS/ALB health checks.

## Required environment
- `OPENAI_API_BASE_URL` – Bedrock gateway base URL (example: `http://bedrock-gateway.internal:80`).
- `OPENAI_API_KEY` – the shared API key stored in Secrets Manager.

## Optional configuration
- `APP_TITLE` – header/title text.
- `APP_TAGLINE` – short subtitle in the header.
- `DEFAULT_SYSTEM_PROMPT` – prefilled system prompt for new sessions.
- `PREFERRED_MODEL_IDS` – comma-separated model ID hints used for the recommended sort order.

## Building locally
```bash
docker build -t open-webui services/open-webui
docker run --rm \
  -e OPENAI_API_BASE_URL=http://localhost:8080 \
  -e OPENAI_API_KEY=secret \
  -p 8081:80 \
  open-webui
```

Then visit `http://localhost:8081`.
