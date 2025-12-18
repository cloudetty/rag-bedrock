#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
CLUSTER="${ECS_CLUSTER:-rag-bedrock-ecs-cluster}"
SERVICES=(
  "${ECS_SERVICE_OPEN_WEBUI:-rag-bedrock-open-webui}"
  "${ECS_SERVICE_BEDROCK_GATEWAY:-rag-bedrock-bedrock-gateway}"
)
STATE_FILE="${ECS_STATE_FILE:-$(dirname "$0")/.ecs-service-counts.txt}"

mkdir -p "$(dirname "$STATE_FILE")"
{
  for service in "${SERVICES[@]}"; do
    desired_count="$(
      aws ecs describe-services \
        --cluster "$CLUSTER" \
        --services "$service" \
        --region "$REGION" \
        --query 'services[0].desiredCount' \
        --output text
    )"
    echo "${service}=${desired_count}"
  done
} >"$STATE_FILE"

for service in "${SERVICES[@]}"; do
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$service" \
    --desired-count 0 \
    --region "$REGION" >/dev/null
done

echo "Scaled ECS services to 0 and saved counts to ${STATE_FILE}"
