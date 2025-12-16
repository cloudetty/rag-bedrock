resource "random_password" "openwebui_gateway_api_key" {
  length  = 32
  special = true
}

resource "random_password" "webui_secret_key" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "openwebui_gateway_api_key" {
  name        = "openwebui_gateway_api_key"
  description = "API key shared between Open WebUI and the Bedrock Access Gateway"

  tags = {
    Name    = "${local.project}-openwebui-gateway-api-key"
    Project = local.project
  }
}

resource "aws_secretsmanager_secret_version" "openwebui_gateway_api_key" {
  secret_id     = aws_secretsmanager_secret.openwebui_gateway_api_key.id
  secret_string = random_password.openwebui_gateway_api_key.result
}
