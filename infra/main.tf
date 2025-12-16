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
