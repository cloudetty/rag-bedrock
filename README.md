# rag-bedrock
This repository hosts the Terraform configuration that provisions the AWS ECR repositories used by the Open WebUI and Bedrock Access Gateway

## Continuous Integration

Terraform now creates an IAM role that GitHub Actions can assume using OIDC. Two workflows under `.github/workflows/` build and push the container images defined in `services/bedrock-gateway/Dockerfile` and `services/open-webui/Dockerfile` to the `bedrock-access-gateway` and `open-webui` ECR repositories, respectively.

Before pushing to `main`, configure these repository secrets:

- `AWS_REGION` (matches `infra/variables.tf`)
- `AWS_ACCOUNT_ID`
- `AWS_ROLE_TO_ASSUME` (the value of `github_actions_role_arn` from `terraform output`, so the workflow can assume the newly-created role)

Each workflow runs on pushes to `main` and tags the image with both the git SHA and `latest`. A successful run guarantees new tags appear in ECR for the two repositories.
