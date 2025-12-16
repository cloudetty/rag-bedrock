# Project Plan & State — Open WebUI + Bedrock (Terraform + GitHub CI/CD)

## Current state (important for next steps)
- AWS: region `us-east-1`, account `425176714222`.
- Terraform applied: ECR repos `open-webui` and `bedrock-access-gateway`; GitHub OIDC provider; IAM role `github-actions-ecr-builder` with ECR push perms (`github_actions_role_arn` output).
- GitHub repo secrets set: `AWS_REGION=us-east-1`, `AWS_ACCOUNT_ID=425176714222`, `AWS_ROLE_TO_ASSUME=arn:aws:iam::425176714222:role/github-actions-ecr-builder`.
- Workflows: `.github/workflows/push-bedrock-access-gateway.yml` and `push-open-webui.yml` build/push placeholder images from `services/*/Dockerfile` to ECR on pushes to `main` (tags: git SHA + `latest`). OIDC permissions fixed; ECR auth/push succeeded after adding `GetAuthorizationToken` and `BatchGetImage`.
- Terraform IAM policy now allows ECR token on `*` and push actions (incl. `BatchGetImage`) on the two repos.

## Milestones (from user plan)
- Milestone 0 — Decisions and prerequisites  
  - Pick AWS region (done: us-east-1); ensure Bedrock model access; repo created.
- Milestone 1 — Repo structure  
  - Folders: `/infra`, `/services/open-webui`, `/services/bedrock-gateway`, `/.github/workflows`; add `.gitignore`. (done)
- Milestone 2 — Container registry (ECR)  
  - Terraform: create ECR repos `open-webui`, `bedrock-access-gateway`; output URLs. (done)
- Milestone 3 — CI: build & push images (GitHub → ECR)  
  - Create GitHub Actions role (OIDC); workflows to build/push both images; verify tags in ECR. (done with placeholders)
- Milestone 4 — Network + load balancer  
  - Terraform: VPC (2 public + 2 private), ALB in public, SGs; ALB inbound 80 (443 later); Open WebUI only from ALB SG; gateway only from Open WebUI SG.
- Milestone 5 — Persistence for Open WebUI  
  - Terraform: EFS + mount targets (+ optional access point); mount path `/app/backend/data`.
- Milestone 6 — Secrets + IAM  
  - Secrets Manager: `openwebui_gateway_api_key` (random); IAM: ECS task execution role (ECR + logs); gateway task role (Bedrock invoke); Open WebUI task role (logs/minimal).
- Milestone 7 — ECS deploy: Bedrock Access Gateway (private service)  
  - ECS cluster, Cloud Map namespace (e.g., `internal`); task def uses ECR image + API key from Secrets Manager + IAM role; service in private subnets (no public IP).
- Milestone 8 — ECS deploy: Open WebUI (behind ALB)  
  - Task def mounts EFS to `/app/backend/data`; env vars:  
    - `OPENAI_API_BASE_URL=http://bedrock-gateway.internal:80/api/v1`  
    - `OPENAI_API_KEY` from Secrets Manager (same key)  
    - `WEBUI_URL=http://<ALB-DNS>` (later https)  
    - `WEBUI_SECRET_KEY` random  
  - ECS service in private subnets; ALB target group + listener rules.
- Milestone 9 — Wire up model + smoke test  
  - Confirm models list via gateway; send prompt; verify response.
- Milestone 10 — RAG: “Doc Detective” (Random PDFs)  
  - Enable Open WebUI Documents; upload PDFs; ask questions w/ citations and a “not found” test.
- Milestone 11 — HTTPS + domain (optional)  
  - Route53 to ALB; ACM cert; ALB 443 → Open WebUI; update `WEBUI_URL` to https.
- Milestone 12 — Ops basics  
  - CloudWatch logs; ECS autoscaling (optional); healthcheck page note; cost sanity (ALB + ECS + EFS).

## Notes for agents
- Use Terraform in `/infra`; provider lockfile present. Run `terraform init` if needed, then `terraform apply -auto-approve`.
- Use existing IAM role output for GitHub CI: `terraform output github_actions_role_arn`.
- Workflows rely on repo secrets already set; keep `permissions` (id-token write, contents read) intact.
- Placeholder Dockerfiles are simple `busybox` echoes; replace with real builds when ready.
