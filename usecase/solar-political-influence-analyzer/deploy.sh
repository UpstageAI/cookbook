#!/bin/bash

# 배포 스크립트
set -e

echo "🚀 수동 배포 시작..."

# AWS 설정
AWS_REGION="ap-northeast-2"
ECR_REPOSITORY="ups-t3-ai-engine"
ECS_CLUSTER="ups-t3-cluster"
ECS_SERVICE="ups-t3-service"

# ECR 로그인
echo "📦 ECR 로그인 중..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

# ECR URI 가져오기
ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)
IMAGE_TAG=$(git rev-parse --short HEAD)

echo "🔨 Docker 이미지 빌드 중..."
cd src/ai-engine
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_URI:latest

echo "⬆️  ECR에 푸시 중..."
docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:latest

echo "🔄 ECS 서비스 업데이트 중..."
aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service $ECS_SERVICE \
  --force-new-deployment \
  --region $AWS_REGION

echo "⏳ 배포 완료 대기 중..."
aws ecs wait services-stable \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --region $AWS_REGION

echo "✅ 배포 완료!"
echo "이미지: $ECR_URI:$IMAGE_TAG"
