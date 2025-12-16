import argparse
import os
import sys

import httpx
import json


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url.rstrip("/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a smoke test against the Open WebUI ALB endpoint")
    parser.add_argument(
        "--url",
        help="Base URL of the Open WebUI service (default: WEBUI_URL env or http://localhost:8081)",
    )
    parser.add_argument("--prompt", default="Hello from the smoke test", help="Prompt to send")
    parser.add_argument("--model-id", help="Use a specific Bedrock model ID instead of the first one")
    return parser.parse_args()


def main():
    args = parse_args()
    base_url = args.url or os.environ.get("WEBUI_URL") or "http://localhost:8081"
    base_url = normalize_url(base_url)

    try:
        with httpx.Client(timeout=20.0) as client:
            print(f"Running health check against {base_url}/healthz")
            resp = client.get(f"{base_url}/healthz")
            resp.raise_for_status()
            print("→ Health check ok")

            print("Fetching model list…")
            resp = client.get(f"{base_url}/api/models")
            resp.raise_for_status()
            models_data = resp.json()
            models = models_data.get("models") or models_data.get("modelSummaries") or []

            if not models:
                raise RuntimeError("no models were returned from the gateway")

            model_id = args.model_id or models[0].get("modelId") or models[0].get("model_id")
            if not model_id:
                raise RuntimeError("unable to determine a model ID from the list response")

            print(f"Selected model: {model_id}")
            payload = {"modelId": model_id, "prompt": args.prompt}

            print("Sending completion request…")
            resp = client.post(f"{base_url}/api/completions", json=payload)
            resp.raise_for_status()
            completion = resp.json()

            print("Received completion:")
            print(json.dumps(completion, indent=2))
            print("")
            print("Smoke test succeeded")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
