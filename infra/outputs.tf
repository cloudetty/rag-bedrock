output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "alb_dns_name" {
  value = aws_lb.webui.dns_name
}

output "alb_arn" {
  value = aws_lb.webui.arn
}

output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "open_webui_security_group_id" {
  value = aws_security_group.open_webui.id
}

output "bedrock_gateway_security_group_id" {
  value = aws_security_group.bedrock_gateway.id
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "bedrock_gateway_service_id" {
  value = aws_ecs_service.bedrock_gateway.id
}

output "bedrock_gateway_service_discovery_name" {
  value = aws_service_discovery_service.bedrock_gateway.name
}

output "service_discovery_namespace_id" {
  value = aws_service_discovery_private_dns_namespace.internal.id
}

output "open_webui_target_group_arn" {
  value = aws_lb_target_group.open_webui.arn
}

output "gateway_api_key_secret_arn" {
  value = aws_secretsmanager_secret.openwebui_gateway_api_key.arn
}

output "ecs_task_execution_role_arn" {
  value = aws_iam_role.ecs_task_execution.arn
}

output "bedrock_gateway_task_role_arn" {
  value = aws_iam_role.bedrock_gateway.arn
}

output "open_webui_task_role_arn" {
  value = aws_iam_role.open_webui.arn
}

output "efs_file_system_id" {
  value = aws_efs_file_system.open_webui.id
}

output "efs_access_point_id" {
  value = aws_efs_access_point.open_webui.id
}
