#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
CLUSTER="${ECS_CLUSTER:-rag-bedrock-ecs-cluster}"
SERVICES=(
  "${ECS_SERVICE_OPEN_WEBUI:-rag-bedrock-open-webui}"
  "${ECS_SERVICE_BEDROCK_GATEWAY:-rag-bedrock-bedrock-gateway}"
)
STATE_FILE="${ECS_STATE_FILE:-$(dirname "$0")/.ecs-service-counts.txt}"

declare -A desired_counts=()
if [[ -f "$STATE_FILE" ]]; then
  while IFS='=' read -r name count; do
    [[ -n "$name" ]] || continue
    desired_counts["$name"]="$count"
  done <"$STATE_FILE"
fi

for service in "${SERVICES[@]}"; do
  count="${desired_counts[$service]:-1}"
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$service" \
    --desired-count "$count" \
    --region "$REGION" >/dev/null
done

echo "Scaled ECS services using counts from ${STATE_FILE:-defaults}"
