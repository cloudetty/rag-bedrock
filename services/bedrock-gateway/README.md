# Bedrock access gateway service

Proxy requests from Open WebUI to AWS Bedrock while guarding them with the shared API key.

## Features
- FastAPI app that exposes `/models` and `/api/v1/completions` behind `x-openwebui-api-key`.
- Calls `bedrock:list_models` and `bedrock-runtime:invoke_model` via `boto3`.
- Health endpoint at `/healthz` for ECS/ALB readiness checks.

## Required environment
- `OPENWEBUI_GATEWAY_API_KEY` – the secret stored in Secrets Manager and injected by Terraform.

## Building locally
```bash
docker build -t bedrock-gateway services/bedrock-gateway
docker run --rm -e OPENWEBUI_GATEWAY_API_KEY=secret -p 8080:80 bedrock-gateway
```

## Running in AWS
The Terraform configuration already injects the API key via Secrets Manager and runs the container on Fargate using the provided IAM role, so no additional setup is needed once the image is pushed to ECR.
