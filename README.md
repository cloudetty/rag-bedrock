# rag-bedrock
This repository hosts the Terraform configuration that provisions the AWS ECR repositories used by the Open WebUI and Bedrock Access Gateway

## Continuous Integration

Terraform now creates an IAM role that GitHub Actions can assume using OIDC. Two workflows under `.github/workflows/` build and push the container images defined in `services/bedrock-gateway/Dockerfile` and `services/open-webui/Dockerfile` to the `bedrock-access-gateway` and `open-webui` ECR repositories, respectively.

Before pushing to `main`, configure these repository secrets:

- `AWS_REGION` (matches `infra/variables.tf`)
- `AWS_ACCOUNT_ID`
- `AWS_ROLE_TO_ASSUME` (the value of `github_actions_role_arn` from `terraform output`, so the workflow can assume the newly-created role)

Each workflow runs on pushes to `main` and tags the image with both the git SHA and `latest`. A successful run guarantees new tags appear in ECR for the two repositories.

## Services

- `services/bedrock-gateway` now contains a FastAPI + `boto3` application (`app/main.py`) that authenticates using `OPENWEBUI_GATEWAY_API_KEY`, lists Bedrock models (`/models`), and implements `/api/v1/completions` to invoke Bedrock models via `bedrock-runtime`.
- `services/open-webui` now hosts a FastAPI proxy that serves a tiny HTML/JS UI (`app/main.py`) and forwards `/api/models` and `/api/completions` to the gateway while reusing `OPENAI_API_BASE_URL`/`OPENAI_API_KEY`.
- Both services expose `/healthz` for ECS health checks, and their Dockerfiles now build from `python:3.11-slim` so the ECS tasks serve actual application code instead of placeholder `busybox` commands.

## Smoke test

`tests/smoke_test.py` is a py script you can run after the ALB is healthy:

```bash
python -m pip install -r tests/requirements.txt
python tests/smoke_test.py --url http://<alb-dns>
```

It verifies `/healthz`, fetches `/api/models`, and submits a prompt to `/api/completions` so you can confirm Milestone 9 without manually poking the UI.

## Networking & load balancer

Terraform now provisions the VPC that will host ECS, including two public subnets (used by both the ALB and the services), and security groups that enforce the ALB → Open WebUI → Bedrock gateway flow described in the plan. NAT gateways were removed to cut costs; tasks now use public IPs for egress while inbound remains SG-restricted.

The ALB lives in the public subnets and already exposes a placeholder HTTP listener so it can be tested before services are attached; the DNS name and security group IDs are available via the new Terraform outputs.

## Persistence

Terraform now creates an Encrypted EFS filesystem dedicated to Open WebUI storage, along with the security group and mount targets inside the private subnets. The new outputs include the filesystem and access point IDs so ECS task definitions can mount `/app/backend/data` through the access point once the service is deployed.

## Secrets & IAM

Terraform now defines the random `openwebui_gateway_api_key` in Secrets Manager plus the ECS execution role and dedicated task roles for the Bedrock gateway (Bedrock invoke permissions) and Open WebUI (CloudWatch Logs). Those ARNs are exported so deployments or ECS task definitions can consume them directly.

## Bedrock gateway service

Terraform now creates the ECS cluster plus the Bedrock Access Gateway task definition/service. The service runs in the private subnets, registers with the `internal` Cloud Map namespace as `bedrock-gateway`, and pulls the image that GitHub populates in ECR. It is wired to the new secret so the gateway exposes `OPENWEBUI_GATEWAY_API_KEY` for Open WebUI to consume, and CloudWatch logs retain the container output.

## Open WebUI behind the ALB

Terraform now defines the Open WebUI task definition and service as well, including the EFS volume mounted at `/app/backend/data`, the secrets/env vars (`OPENAI_API_BASE_URL`, `OPENAI_API_KEY`, `WEBUI_URL`, `WEBUI_SECRET_KEY`), and CloudWatch logging. The service runs in the private subnets, registers with the ALB target group, and the listener now forwards traffic to that target group so the UI is reachable via the ALB DNS name (`WEBUI_URL`).
