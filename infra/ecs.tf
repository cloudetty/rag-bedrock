resource "aws_ecs_cluster" "main" {
  name = "${local.project}-ecs-cluster"

  tags = {
    Name    = "${local.project}-ecs-cluster"
    Project = local.project
  }
}

resource "aws_service_discovery_private_dns_namespace" "internal" {
  name = "internal"
  vpc  = aws_vpc.main.id

  tags = {
    Name    = "${local.project}-internal-namespace"
    Project = local.project
  }
}

resource "aws_cloudwatch_log_group" "bedrock_gateway" {
  name              = "/ecs/bedrock-gateway"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "open_webui" {
  name              = "/ecs/open-webui"
  retention_in_days = 30
}

resource "aws_service_discovery_service" "bedrock_gateway" {
  name = "bedrock-gateway"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.internal.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  depends_on = [aws_service_discovery_private_dns_namespace.internal]
}

resource "aws_ecs_task_definition" "bedrock_gateway" {
  family                   = "${local.project}-bedrock-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.bedrock_gateway.arn

  container_definitions = jsonencode([
    {
      name  = "bedrock-gateway"
      image = "${aws_ecr_repository.bedrock_gateway.repository_url}:latest"
      user  = "0"

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.bedrock_gateway.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "bedrock-gateway"
        }
      }

      secrets = [
        {
          name      = "OPENWEBUI_GATEWAY_API_KEY"
          valueFrom = aws_secretsmanager_secret.openwebui_gateway_api_key.arn
        }
      ]
    }
  ])
}

resource "aws_ecs_service" "bedrock_gateway" {
  name             = "${local.project}-bedrock-gateway"
  cluster          = aws_ecs_cluster.main.id
  desired_count    = 1
  launch_type      = "FARGATE"
  task_definition  = aws_ecs_task_definition.bedrock_gateway.arn
  platform_version = "1.4.0"
  force_new_deployment = true

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.bedrock_gateway.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.bedrock_gateway.arn
  }

  depends_on = [
    aws_service_discovery_service.bedrock_gateway
  ]
}

resource "aws_ecs_task_definition" "open_webui" {
  family                   = "${local.project}-open-webui"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.open_webui.arn

  volume {
    name = "open-webui-data"

    efs_volume_configuration {
      file_system_id = aws_efs_file_system.open_webui.id

      authorization_config {
        access_point_id = aws_efs_access_point.open_webui.id
        iam             = "ENABLED"
      }

      transit_encryption = "ENABLED"
    }
  }

  container_definitions = jsonencode([
    {
      name  = "open-webui"
      image = "${aws_ecr_repository.open_webui.repository_url}:latest"
      user  = "0"

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.open_webui.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "open-webui"
        }
      }

      environment = [
        {
          name  = "OPENAI_API_BASE_URL"
          value = "http://bedrock-gateway.internal"
        },
        {
          name  = "WEBUI_URL"
          value = format("http://%s", aws_lb.webui.dns_name)
        },
        {
          name  = "WEBUI_SECRET_KEY"
          value = random_password.webui_secret_key.result
        }
      ]

      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openwebui_gateway_api_key.arn
        }
      ]

      mountPoints = [
        {
          containerPath = "/app/backend/data"
          sourceVolume  = "open-webui-data"
        }
      ]
    }
  ])
}

resource "aws_lb_target_group" "open_webui" {
  name        = "${local.project}-open-webui-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/healthz"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 15
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_ecs_service" "open_webui" {
  name             = "${local.project}-open-webui"
  cluster          = aws_ecs_cluster.main.id
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"
  task_definition  = aws_ecs_task_definition.open_webui.arn
  force_new_deployment = true

  load_balancer {
    target_group_arn = aws_lb_target_group.open_webui.arn
    container_name   = "open-webui"
    container_port   = 80
  }

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.open_webui.id]
    assign_public_ip = true
  }
}
