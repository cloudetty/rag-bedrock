import json
import logging
import os
from typing import List, Optional

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
    class ChatMessage(BaseModel):
        role: str = Field(..., description="Message role (user/assistant/system)")
        content: str = Field(..., description="Plain text content")

    modelId: str = Field(..., description="Bedrock model identifier (e.g., anthropic.claude-3-opus)")
    prompt: Optional[str] = Field(None, description="Prompt text to send to Bedrock")
    messages: Optional[List[ChatMessage]] = Field(
        None, description="Optional chat-style messages; if provided, overrides prompt"
    )
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

    filtered_models = []
    for model in models:
        outputs = model.get("outputModalities") or []
        inference = model.get("inferenceTypesSupported") or []
        if "TEXT" in outputs and "ON_DEMAND" in inference:
            filtered_models.append(model)

    return {
        "models": filtered_models or models,
        "nextToken": response.get("nextToken"),
    }


@app.post("/api/v1/completions", dependencies=[Depends(require_api_key)])
def invoke_completion(payload: CompletionRequest):
    if not payload.prompt and not payload.messages:
        raise HTTPException(status_code=400, detail="Provide either 'prompt' or 'messages'")

    def build_chat_like_prompt(messages: List[CompletionRequest.ChatMessage]) -> str:
        """Render chat turns into a plain prompt for models that don't support chat natively."""
        parts = []
        role_map = {"user": "User", "assistant": "Assistant", "system": "System"}
        for msg in messages:
            role = role_map.get(msg.role, msg.role)
            parts.append(f"{role}:\n{msg.content}")
        # Hint the model to continue as the assistant.
        parts.append("Assistant:")
        return "\n\n".join(parts)

    # Normalize prompt/messages for downstream models.
    if payload.messages:
        prompt_text = build_chat_like_prompt(payload.messages)
    else:
        prompt_text = payload.prompt or ""

    if payload.modelId.startswith(("anthropic.", "amazon.nova", "openai.")):
        # Use Bedrock chat schema.
        messages_payload = payload.messages or [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}],
            }
        ]

        if payload.messages:
            messages_payload = [
                {
                    "role": msg.role,
                    "content": [{"type": "text", "text": msg.content}],
                }
                for msg in payload.messages
            ]

        body_payload = {"messages": messages_payload}
    else:
        # Prompt-based schema for other models (e.g., Llama/Mistral/Qwen).
        body_payload = {"prompt": prompt_text}

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
        error_detail = exc.response.get("Error", {}).get("Message") if hasattr(exc, "response") else str(exc)
        raise HTTPException(
            status_code=502,
            detail=f"Bedrock invocation failed: {error_detail}",
        ) from exc

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
