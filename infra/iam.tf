data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.project}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_task_execution_secrets" {
  statement {
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue",
    ]

    resources = [
      aws_secretsmanager_secret.openwebui_gateway_api_key.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name   = "${local.project}-ecs-execution-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.ecs_task_execution_secrets.json
}

resource "aws_iam_role" "bedrock_gateway" {
  name               = "${local.project}-bedrock-gateway-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "bedrock_gateway" {
  statement {
    effect = "Allow"

    actions = [
      "bedrock:InvokeModel",
      "bedrock:GetModel",
      "bedrock:List*",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "bedrock_gateway" {
  name   = "${local.project}-bedrock-gateway-policy"
  role   = aws_iam_role.bedrock_gateway.id
  policy = data.aws_iam_policy_document.bedrock_gateway.json
}

resource "aws_iam_role" "open_webui" {
  name               = "${local.project}-open-webui-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "open_webui_logs" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup",
    ]

    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/open-webui*",
    ]
  }
}

resource "aws_iam_role_policy" "open_webui" {
  name   = "${local.project}-open-webui-logs"
  role   = aws_iam_role.open_webui.id
  policy = data.aws_iam_policy_document.open_webui_logs.json
}
