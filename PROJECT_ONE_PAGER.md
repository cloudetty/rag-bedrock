# One-Pager — Open WebUI + Bedrock on AWS

## What this is
A small AWS stack that runs Open WebUI on ECS Fargate, fronted by an ALB, with a private Bedrock gateway service that adapts OpenAI-style requests to Bedrock. CI builds and pushes images to ECR using GitHub OIDC (no static AWS keys).

## Core components (with links)
- **Networking + ALB:** VPC, public subnets, security groups, ALB + target group  
  - Terraform: [infra/network.tf](infra/network.tf)
- **Compute + Service Discovery:** ECS cluster, services, task definitions, Cloud Map  
  - Terraform: [infra/ecs.tf](infra/ecs.tf)
- **Persistence:** EFS for `/app/backend/data`  
  - Terraform: [infra/efs.tf](infra/efs.tf)
- **Secrets:** Shared API key for Open WebUI ↔ gateway  
  - Terraform: [infra/secrets.tf](infra/secrets.tf)
- **IAM:** ECS execution + task roles, GitHub Actions OIDC + role  
  - Terraform: [infra/iam.tf](infra/iam.tf), [infra/main.tf](infra/main.tf)
- **Images + CI:** ECR repos + GitHub Actions workflows  
  - Terraform: [infra/main.tf](infra/main.tf)  
  - Workflows: [.github/workflows/push-open-webui.yml](.github/workflows/push-open-webui.yml), [.github/workflows/push-bedrock-access-gateway.yml](.github/workflows/push-bedrock-access-gateway.yml)
- **Services:** Open WebUI app + Bedrock gateway  
  - Code: [services/open-webui/](services/open-webui/), [services/bedrock-gateway/](services/bedrock-gateway/)

## How it works (flow)
1) User hits ALB → Open WebUI service (ECS).  
2) Open WebUI calls `bedrock-gateway.internal` via Cloud Map.  
3) Gateway invokes Bedrock models.  
4) State (documents, chats) stored on EFS.

## Why these choices
- **Public subnets + no NAT:** lower cost; ECS tasks get public IPs for egress.  
- **Cloud Map:** stable private DNS between services.  
- **EFS:** persistent app data across ECS task restarts.  
- **OIDC for CI:** no long-lived AWS keys in GitHub.

## Cost profile (high-level)
- **Main cost drivers:** ALB hourly + LCU usage, ECS Fargate runtime, EFS storage, CloudWatch Logs, Bedrock inference.  
- **Low/no cost:** IAM roles, OIDC provider, VPC/subnets/SGs.  
- **ECR:** storage only; keep images pruned to stay cheap.

## Bring it back
- Apply Terraform in `infra/` and push to `main` to rebuild images.  
- More detail: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md), [README.md](README.md)

## Tear down
- Cost-cutting teardown steps: [CLOSE.md](CLOSE.md)
