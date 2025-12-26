# Project Summary — Open WebUI + Bedrock on AWS (Terraform + GitHub CI/CD)

This document captures what was built, why each piece exists, and the cost profile so a mid-level engineer can quickly understand the system and the tradeoffs.

## Architecture at a glance
- Users access Open WebUI through an Application Load Balancer (ALB).
- Open WebUI runs on ECS (Fargate) with persistent storage on EFS.
- Open WebUI talks to a private Bedrock gateway service over Cloud Map service discovery.
- The Bedrock gateway invokes Amazon Bedrock models (e.g., Meta Llama 3).
- GitHub Actions builds Docker images and pushes them to ECR using OIDC, no long-lived AWS keys.

## Code and repo layout
- `infra/`: Terraform for all AWS resources.
- `services/open-webui/`: Open WebUI container build.
- `services/bedrock-gateway/`: Bedrock access gateway container build.
- `.github/workflows/`: CI workflows that build and push images to ECR.

## Components (what, why, cost)

### Networking and traffic
- **VPC + public subnets** (`infra/network.tf`)  
  - **What:** A dedicated VPC with two public subnets across AZs.  
  - **Why:** ECS services and the ALB need subnets; public subnets keep costs down by avoiding NAT.  
  - **Cost:** VPC/subnets are free; data transfer costs may apply.

- **Security groups** (`infra/network.tf`)  
  - **What:** SGs restricting inbound traffic to ALB and ECS services.  
  - **Why:** Enforce least-privilege network access.  
  - **Cost:** Free.

- **Application Load Balancer (ALB)** (`infra/network.tf`)  
  - **What:** Public ALB with HTTP listener and target group.  
  - **Why:** Provides a stable endpoint and health checks for Open WebUI.  
  - **Cost:** Hourly ALB fee + LCU usage (billable, usually a noticeable baseline cost).

### Compute and service discovery
- **ECS Cluster** (`infra/ecs.tf`)  
  - **What:** ECS cluster hosting Fargate services.  
  - **Why:** Orchestrates the Open WebUI and Bedrock gateway tasks.  
  - **Cost:** Cluster itself is free; Fargate tasks are billed by vCPU/GB-hours.

- **ECS Services + Task Definitions** (`infra/ecs.tf`)  
  - **What:** Two services:  
    - **Open WebUI** behind the ALB, with EFS mounted at `/app/backend/data`.  
    - **Bedrock gateway** private service, discovered via Cloud Map.  
  - **Why:** Clean separation of UI and Bedrock invocation; easier scaling and isolation.  
  - **Cost:** Fargate task runtime is billable; also CloudWatch Logs ingestion/storage.

- **Cloud Map namespace/service discovery** (`infra/ecs.tf`)  
  - **What:** Private namespace with service name `bedrock-gateway.internal`.  
  - **Why:** Let Open WebUI reach the gateway without hardcoding IPs.  
  - **Cost:** Low monthly cost per namespace + DNS queries.

### Storage and data
- **EFS file system + mount targets** (`infra/efs.tf`)  
  - **What:** Persistent storage for Open WebUI data.  
  - **Why:** Preserve chat history, documents, and settings across task restarts.  
  - **Cost:** EFS storage is billable per GB-month; mount targets are included.

### Secrets and IAM
- **Secrets Manager** (`infra/secrets.tf`)  
  - **What:** `openwebui_gateway_api_key` secret used by Open WebUI and the gateway.  
  - **Why:** Avoids hardcoding API keys in task definitions.  
  - **Cost:** Per-secret monthly fee + API call usage.

- **ECS execution role** (`infra/iam.tf`)  
  - **What:** Role for ECS to pull images and write logs.  
  - **Why:** Required for ECS Fargate tasks.  
  - **Cost:** Free.

- **ECS task roles** (`infra/iam.tf`)  
  - **What:**  
    - **Gateway role**: permission to invoke Bedrock models.  
    - **Open WebUI role**: minimal CloudWatch Logs access.  
  - **Why:** Least-privilege access per service.  
  - **Cost:** Free.

- **GitHub Actions OIDC provider + IAM role** (`infra/main.tf`)  
  - **What:** OIDC provider and role `github-actions-ecr-builder` that can push to ECR.  
  - **Why:** CI can push images without static AWS keys.  
  - **Cost:** Free.

### Container images and CI/CD
- **ECR repositories** (`infra/main.tf`)  
  - **What:** `open-webui` and `bedrock-access-gateway` image repos.  
  - **Why:** Store build artifacts for ECS tasks.  
  - **Cost:** Storage per GB-month; data transfer on pulls.

- **GitHub Actions workflows** (`.github/workflows/*.yml`)  
  - **What:** Build/push Docker images on `main` pushes, tag with git SHA + `latest`.  
  - **Why:** Automates deployment artifacts; no manual image builds.  
  - **Cost:** GitHub Actions minutes (GitHub-billed), plus ECR storage/transfer.

### Bedrock integration
- **Bedrock Access Gateway service** (`services/bedrock-gateway/`)  
  - **What:** A small gateway that normalizes OpenAI-style requests to Bedrock.  
  - **Why:** Open WebUI expects OpenAI-like endpoints; gateway bridges the API.  
  - **Cost:** Bedrock model inference is billed per token/usage.

- **Open WebUI service** (`services/open-webui/`)  
  - **What:** Web UI providing chat, model selection, and documents.  
  - **Why:** Simple, user-friendly interface for LLM workflows.  
  - **Cost:** Runs on Fargate + EFS storage + ALB.

## Operational notes
- NAT gateways were removed to reduce costs; ECS tasks use public IPs for egress.
- The ALB provides the only inbound path; ECS services are SG-restricted.
- Anthropic models remain blocked pending AWS use-case approval; Meta Llama 3 worked in smoke tests.

## Cost hotspots (where spend accumulates)
- **ALB:** always-on hourly charge + LCU usage.
- **ECS Fargate:** vCPU/GB-hours for each running task.
- **EFS:** storage per GB-month.
- **CloudWatch Logs:** ingestion + retention.
- **Bedrock:** usage-based, depends on token volume.

## Low-cost or free components
- IAM roles and OIDC provider.
- VPC, subnets, security groups (free).
- ECR when images are small and pruned regularly (storage only).

## How to bring it back
- Re-run Terraform in `infra/` to recreate infrastructure.
- Push to `main` to rebuild and push images to ECR via GitHub Actions.
