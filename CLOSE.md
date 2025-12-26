# Project Closeout (Destroy AWS Resources, Keep CI Working)

This repo uses Terraform in `infra/` with a local state file. The steps below destroy the billable AWS resources while keeping ECR and the GitHub Actions IAM role intact so CI can still push images.

## Preconditions
- You have AWS credentials that can destroy the stack in `us-east-1`.
- You understand this is destructive (EFS data, ECS services, ALB, and Secrets Manager entries will be deleted).
- ECR repos and the GitHub Actions IAM role/OIDC provider will be preserved for CI.

## Preserve CI resources in state
1) Change into the Terraform directory:
```bash
cd infra
```

2) Initialize Terraform (if not already initialized on this machine):
```bash
terraform init
```

3) Remove ECR and GitHub Actions IAM resources from Terraform state so they are not destroyed:
```bash
terraform state rm \
  aws_ecr_repository.open_webui \
  aws_ecr_repository.bedrock_gateway \
  aws_iam_openid_connect_provider.github_actions \
  aws_iam_role.github_actions \
  aws_iam_role_policy.github_actions_ecr
```

## Destroy AWS resources
1) Destroy the entire stack that is still tracked in state:
```bash
terraform destroy -auto-approve
```

## Remove local Terraform state files
From the repo root, delete the local state files:
```bash
rm -f infra/terraform.tfstate infra/terraform.tfstate.backup
```

Optional cleanup if you want a completely fresh Terraform working directory:
```bash
rm -rf infra/.terraform
rm -f infra/.terraform.lock.hcl
```

## Notes
- CI stays functional because the ECR repos and GitHub Actions IAM role are preserved.
- The preserved resources are now unmanaged by Terraform. If you want Terraform to manage them again later, re-import them or re-apply and recreate them.
