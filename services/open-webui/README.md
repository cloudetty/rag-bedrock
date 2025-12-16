# Open WebUI service

Minimal FastAPI app that serves a simple browser UI, forwards prompts to the Bedrock gateway, and displays model responses.

## Features
- `/` serves a tiny HTML/JS interface that lets you select a model, enter a prompt, and read the JSON response in-line.
- `/api/models` and `/api/completions` proxy requests to the gateway using `OPENAI_API_BASE_URL` + `OPENAI_API_KEY`.
- `/healthz` for ECS/ALB health checks.

## Required environment
- `OPENAI_API_BASE_URL` – usually `http://bedrock-gateway.internal:80/api/v1`.
- `OPENAI_API_KEY` – the same shared API key stored in Secrets Manager.
- `WEBUI_URL` and `WEBUI_SECRET_KEY` are provided for future features but are not required by this proxy.

## Building locally
```bash
docker build -t open-webui services/open-webui
docker run --rm \
  -e OPENAI_API_BASE_URL=http://localhost:8080 \
  -e OPENAI_API_KEY=secret \
  -p 8081:80 \
  open-webui
```

Then visit `http://localhost:8081` and enter `http://localhost:8080` as the backend gateway in the prompt UI.
