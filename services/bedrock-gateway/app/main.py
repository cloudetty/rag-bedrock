import json
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)

API_KEY_ENV = "OPENWEBUI_GATEWAY_API_KEY"
api_key = os.environ.get(API_KEY_ENV)

if not api_key:
    raise RuntimeError(f"{API_KEY_ENV} is required to run the gateway")

bedrock_client = boto3.client("bedrock")
runtime_client = boto3.client("bedrock-runtime")

app = FastAPI(title="Bedrock Access Gateway", version="0.1.0")


def require_api_key(x_api_key: str = Header(..., alias="x-openwebui-api-key")):
    if x_api_key != api_key:
        logging.warning("Rejected request with invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


class CompletionRequest(BaseModel):
    modelId: str = Field(..., description="Bedrock model identifier (e.g., anthropic.claude-3-opus)")
    prompt: str = Field(..., description="Prompt text to send to Bedrock")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional temperature hint")


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/models", dependencies=[Depends(require_api_key)])
def list_models():
    try:
        response = bedrock_client.list_foundation_models()
    except ClientError as exc:
        logging.exception("Bedrock list_foundation_models failed")
        raise HTTPException(status_code=502, detail="Bedrock list models failed") from exc

    models = response.get("modelSummaries") or response.get("models") or []
    return {"models": models, "nextToken": response.get("nextToken")}


@app.post("/api/v1/completions", dependencies=[Depends(require_api_key)])
def invoke_completion(payload: CompletionRequest):
    body_payload = {"input": payload.prompt}
    if payload.temperature is not None:
        body_payload["temperature"] = payload.temperature

    try:
        response = runtime_client.invoke_model(
            modelId=payload.modelId,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body_payload).encode("utf-8"),
        )
    except ClientError as exc:
        logging.exception("Bedrock invoke_model failed")
        raise HTTPException(status_code=502, detail="Bedrock invocation failed") from exc

    streaming_body = response.get("body")
    if streaming_body is None:
        raise HTTPException(status_code=502, detail="Bedrock response missing payload")

    body_bytes = streaming_body.read()
    streaming_body.close()
    raw_body = body_bytes.decode("utf-8")

    try:
        parsed_body = json.loads(raw_body)
    except json.JSONDecodeError:
        parsed_body = {"output": raw_body}

    return JSONResponse(
        content={
            "modelId": payload.modelId,
            "body": parsed_body,
            "metadata": {
                "contentType": response.get("contentType"),
                "modelId": payload.modelId,
            },
        }
    )
