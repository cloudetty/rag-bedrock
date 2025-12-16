terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "open_webui" {
  name                 = "open-webui"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "bedrock_gateway" {
  name                 = "bedrock-access-gateway"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

output "open_webui_repo_url" {
  value = aws_ecr_repository.open_webui.repository_url
}

output "bedrock_gateway_repo_url" {
  value = aws_ecr_repository.bedrock_gateway.repository_url
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-ecr-builder"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:cloudetty/rag-bedrock:*"
          }
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

data "aws_iam_policy_document" "github_actions_ecr" {
  statement {
    sid    = "AllowPushToRepo"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:CreateRepository",
      "ecr:DescribeRepositories",
      "ecr:GetAuthorizationToken",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [
      "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/*",
    ]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name   = "github-actions-ecr-policy"
  role   = aws_iam_role.github_actions.name
  policy = data.aws_iam_policy_document.github_actions_ecr.json
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}
