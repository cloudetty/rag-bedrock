data "aws_availability_zones" "available" {}

locals {
  project = "rag-bedrock"
  azs     = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "${local.project}-vpc"
    Project = local.project
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name    = "${local.project}-igw"
    Project = local.project
  }
}

resource "aws_subnet" "public" {
  count                   = length(local.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name    = "${local.project}-public-${count.index + 1}"
    Project = local.project
  }
}

resource "aws_subnet" "private" {
  count             = length(local.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(local.azs))
  availability_zone = local.azs[count.index]

  tags = {
    Name    = "${local.project}-private-${count.index + 1}"
    Project = local.project
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name    = "${local.project}-public-rt"
    Project = local.project
  }
}

resource "aws_route_table_association" "public" {
  count          = length(local.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "alb" {
  vpc_id = aws_vpc.main.id

  name        = "${local.project}-alb-sg"
  description = "Allow HTTP traffic from the internet to the ALB"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${local.project}-alb-sg"
    Project = local.project
  }
}

resource "aws_security_group" "open_webui" {
  vpc_id = aws_vpc.main.id

  name        = "${local.project}-open-webui-sg"
  description = "Allows Open WebUI tasks to receive traffic from the ALB"

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${local.project}-open-webui-sg"
    Project = local.project
  }
}

resource "aws_security_group" "bedrock_gateway" {
  vpc_id = aws_vpc.main.id

  name        = "${local.project}-bedrock-gateway-sg"
  description = "Allows Bedrock gateway tasks to receive traffic from Open WebUI"

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.open_webui.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${local.project}-bedrock-gateway-sg"
    Project = local.project
  }
}

resource "aws_lb" "webui" {
  name               = "${local.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  idle_timeout = 60

  tags = {
    Name    = "${local.project}-alb"
    Project = local.project
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.webui.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.open_webui.arn
  }
}
