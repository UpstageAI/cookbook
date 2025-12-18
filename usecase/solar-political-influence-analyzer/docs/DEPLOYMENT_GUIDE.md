# 정치테마주 분석 PIN - 배포 가이드

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [아키텍처](#아키텍처)
3. [로컬 개발 환경 설정](#로컬-개발-환경-설정)
4. [AWS 인프라 구축](#aws-인프라-구축)
5. [프론트엔드 배포](#프론트엔드-배포)
6. [AI 엔진 배포](#ai-엔진-배포)
7. [도메인 설정](#도메인-설정)
8. [트러블슈팅](#트러블슈팅)

---

## 프로젝트 개요

**정치테마주 분석 PIN**은 정치인과 정책이 산업 및 기업에 미치는 영향을 분석하고 시각화하는 풀스택 애플리케이션입니다.

### 주요 기능
- 정치인/정책 검색 및 관계도 분석
- 정책 → 산업 → 기업 4단계 연결 시각화
- 실시간 주가 정보 제공
- 근거 기반 분석 (출처 제공)

### 기술 스택
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), LangGraph
- **AI**: Upstage Solar-Pro2, Tavily Search API
- **Infrastructure**: AWS (ECS Fargate, ALB, CloudFront, S3, DynamoDB)

---

## 아키텍처

```
사용자
  ↓
CloudFront (HTTPS, CDN)
  ├─ / → S3 (정적 웹사이트)
  ├─ /api/* → ALB → ECS Fargate (AI 엔진)
  ├─ /generate → ALB → ECS Fargate
  └─ /job/* → ALB → ECS Fargate
       ↓
   DynamoDB (캐싱)
       ↓
   외부 API (Upstage, Tavily, 네이버 주가)
```

### AWS 리소스
- **CloudFront**: `E1RLDWF8ZOYKW1` (d31ad140yvex7c.cloudfront.net)
- **S3**: `ups-t3-frontend-1763878138`
- **ALB**: `ups-t3-alb` (ups-t3-alb-984329148.ap-northeast-2.elb.amazonaws.com)
- **ECS Cluster**: `ups-t3-cluster`
- **ECS Service**: `ups-t3-service`
- **ECR**: `ups-t3-ai-engine`
- **DynamoDB**: `analysis_results`, `stock_prices`, `rate_limits`

---

## 로컬 개발 환경 설정

### 1. 필수 요구사항
- Node.js 18+
- Python 3.9+
- AWS CLI
- Docker (AI 엔진 배포용)

### 2. API 키 설정
```bash
# AI 엔진 API 키
cd src/ai-engine
cat > .env << EOF
UPSTAGE_API_KEY=your_upstage_api_key
TAVILY_API_KEY=your_tavily_api_key
EOF
```

### 3. 의존성 설치
```bash
# 프론트엔드
cd src/frontend
npm install --legacy-peer-deps

# AI 엔진
cd src/ai-engine
pip install -r requirements.txt
```

### 4. 로컬 서버 실행
```bash
# AI 엔진 (포트 8000)
cd src/ai-engine/deep_research
PYTHONPATH=src python main.py

# 프론트엔드 (포트 3000)
cd src/frontend
npm run dev
```

### 5. 로컬 접속
- Frontend: http://localhost:3000
- AI Engine: http://localhost:8000

---

## AWS 인프라 구축

### Step 1: AWS CLI 설정
```bash
aws configure
# Access Key ID: [YOUR_KEY]
# Secret Access Key: [YOUR_SECRET]
# Region: ap-northeast-2
# Output: json
```

### Step 2: DynamoDB 테이블 생성
```bash
# 분석 결과 캐시 (24시간 TTL)
aws dynamodb create-table \
  --region ap-northeast-2 \
  --table-name analysis_results \
  --attribute-definitions AttributeName=query_hash,AttributeType=S \
  --key-schema AttributeName=query_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 주가 정보 캐시 (5분 TTL)
aws dynamodb create-table \
  --region ap-northeast-2 \
  --table-name stock_prices \
  --attribute-definitions AttributeName=company_name,AttributeType=S \
  --key-schema AttributeName=company_name,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Rate Limiting (1분 TTL)
aws dynamodb create-table \
  --region ap-northeast-2 \
  --table-name rate_limits \
  --attribute-definitions AttributeName=ip_minute,AttributeType=S \
  --key-schema AttributeName=ip_minute,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Step 3: VPC 및 보안 그룹 생성
```bash
# VPC 생성
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region ap-northeast-2

# 서브넷 생성 (2개 AZ)
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone ap-northeast-2a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone ap-northeast-2c

# ALB 보안 그룹
aws ec2 create-security-group \
  --group-name ups-t3-alb-sg \
  --description "ALB Security Group" \
  --vpc-id vpc-xxx

# HTTP/HTTPS 허용
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS 보안 그룹
aws ec2 create-security-group \
  --group-name ups-t3-ecs-sg \
  --description "ECS Security Group" \
  --vpc-id vpc-xxx

# ALB에서만 접근 허용
aws ec2 authorize-security-group-ingress --group-id sg-yyy --protocol tcp --port 8000 --source-group sg-xxx
```

### Step 4: ALB 생성
```bash
# ALB 생성
aws elbv2 create-load-balancer \
  --name ups-t3-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --region ap-northeast-2

# Target Group 생성
aws elbv2 create-target-group \
  --name ups-t3-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip \
  --health-check-path /health \
  --region ap-northeast-2

# HTTP Listener 생성
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### Step 5: HTTPS 리스너 추가
```bash
# 자체 서명 인증서 생성
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=ups-t3-alb-984329148.ap-northeast-2.elb.amazonaws.com"

# ACM에 인증서 임포트
aws acm import-certificate \
  --certificate fileb://cert.pem \
  --private-key fileb://key.pem \
  --region ap-northeast-2

# HTTPS Listener 생성
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

---

## 프론트엔드 배포

### Step 1: S3 버킷 생성
```bash
BUCKET_NAME="ups-t3-frontend-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region ap-northeast-2

# 정적 웹사이트 호스팅 설정
aws s3 website s3://$BUCKET_NAME \
  --index-document index.html \
  --error-document 404.html

# 퍼블릭 읽기 권한
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::'$BUCKET_NAME'/*"
  }]
}'
```

### Step 2: 환경 변수 설정
```bash
cd src/frontend

# .env.production
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://d31ad140yvex7c.cloudfront.net
EOF
```

### Step 3: 빌드 및 배포
```bash
# 빌드
npm run build

# S3 업로드
aws s3 sync out/ s3://ups-t3-frontend-1763878138 --region ap-northeast-2 --delete
```

### Step 4: CloudFront 배포 생성
```bash
# CloudFront 배포 생성 (JSON 설정 필요)
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

**cloudfront-config.json 주요 설정:**
- Origins: S3 (정적 파일), ALB (API)
- Behaviors:
  - `/` → S3
  - `/api/*` → ALB
  - `/generate` → ALB
  - `/job/*` → ALB
- SSL Certificate: CloudFront 기본 인증서

### Step 5: 캐시 무효화
```bash
aws cloudfront create-invalidation \
  --distribution-id E1RLDWF8ZOYKW1 \
  --paths "/*"
```

---

## AI 엔진 배포

### Step 1: ECR 리포지토리 생성
```bash
aws ecr create-repository \
  --repository-name ups-t3-ai-engine \
  --region ap-northeast-2
```

### Step 2: Docker 이미지 빌드
```bash
cd src/ai-engine

# Dockerfile 생성
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "src/deep_research/main.py"]
EOF

# 빌드
docker build -t ups-t3-ai-engine .
```

### Step 3: ECR에 푸시
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com

# 태그 및 푸시
docker tag ups-t3-ai-engine:latest 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com/ups-t3-ai-engine:latest
docker push 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com/ups-t3-ai-engine:latest
```

### Step 4: ECS 클러스터 생성
```bash
aws ecs create-cluster --cluster-name ups-t3-cluster --region ap-northeast-2
```

### Step 5: Task Definition 생성
```bash
# task-definition.json
cat > task-definition.json << 'EOF'
{
  "family": "ups-t3-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "ups-t3-container",
    "image": "663120345697.dkr.ecr.ap-northeast-2.amazonaws.com/ups-t3-ai-engine:latest",
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "UPSTAGE_API_KEY", "value": "your_key"},
      {"name": "TAVILY_API_KEY", "value": "your_key"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/ups-t3",
        "awslogs-region": "ap-northeast-2",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }],
  "executionRoleArn": "arn:aws:iam::663120345697:role/ecsTaskExecutionRole"
}
EOF

aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 6: ECS Service 생성
```bash
aws ecs create-service \
  --cluster ups-t3-cluster \
  --service-name ups-t3-service \
  --task-definition ups-t3-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-yyy],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=ups-t3-container,containerPort=8000" \
  --region ap-northeast-2
```

---

## 도메인 설정

### Step 1: ACM 인증서 요청 (us-east-1)
```bash
aws acm request-certificate \
  --domain-name pinstock.site \
  --subject-alternative-names www.pinstock.site \
  --validation-method DNS \
  --region us-east-1
```

### Step 2: DNS 검증 레코드 확인
```bash
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:...:certificate/... \
  --region us-east-1 \
  --query 'Certificate.DomainValidationOptions[*].[DomainName,ResourceRecord.Name,ResourceRecord.Value]'
```

### Step 3: 가비아 DNS 설정
1. 가비아 로그인 → My가비아 → 서비스 관리
2. `pinstock.site` → DNS 정보 → DNS 관리
3. CNAME 레코드 추가 (인증서 검증용)
4. 인증서 검증 완료 대기 (5-30분)

### Step 4: CloudFront에 커스텀 도메인 추가
```bash
# CloudFront 설정 업데이트
aws cloudfront update-distribution \
  --id E1RLDWF8ZOYKW1 \
  --distribution-config file://cloudfront-config-with-domain.json
```

### Step 5: 가비아에 CNAME 레코드 추가
- 타입: `CNAME`
- 호스트: `@` (또는 `www`)
- 값: `d31ad140yvex7c.cloudfront.net`

---

## 트러블슈팅

### 1. Mixed Content 오류
**문제**: HTTPS 페이지에서 HTTP API 호출 차단

**해결**:
- ALB에 HTTPS 리스너 추가
- CloudFront를 통해 API 프록시
- 환경 변수를 HTTPS URL로 변경

### 2. 검색창 엔터 안 됨
**문제**: 서버 컴포넌트에서 폼 제출 불가

**해결**:
```tsx
'use client'
import { useRouter } from 'next/navigation'

const handleSubmit = (e: FormEvent) => {
  e.preventDefault()
  const query = formData.get('query')
  router.push(`/analysis?query=${encodeURIComponent(query)}`)
}
```

### 3. CloudFront 504 Timeout
**문제**: AI 분석 시간 초과 (60초 제한)

**해결**:
- Job 기반 비동기 처리 구현
- `/generate` (Job 생성) + `/job/{id}` (폴링)

### 4. ERR_CERT_AUTHORITY_INVALID
**문제**: 자체 서명 인증서 거부

**해결**:
- CloudFront를 통해 API 프록시
- CloudFront의 유효한 인증서 사용

### 5. CORS 오류
**문제**: 프론트엔드에서 API 호출 실패

**해결**:
```python
# FastAPI CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 유지보수

### 프론트엔드 재배포
```bash
cd src/frontend
npm run build
aws s3 sync out/ s3://ups-t3-frontend-1763878138 --region ap-northeast-2 --delete
aws cloudfront create-invalidation --distribution-id E1RLDWF8ZOYKW1 --paths "/*"
```

### AI 엔진 재배포
```bash
cd src/ai-engine
docker build -t ups-t3-ai-engine .
docker tag ups-t3-ai-engine:latest 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com/ups-t3-ai-engine:latest
docker push 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com/ups-t3-ai-engine:latest

# ECS 서비스 업데이트
aws ecs update-service \
  --cluster ups-t3-cluster \
  --service ups-t3-service \
  --force-new-deployment \
  --region ap-northeast-2
```

### 모니터링
```bash
# ECS 서비스 상태
aws ecs describe-services --cluster ups-t3-cluster --services ups-t3-service --region ap-northeast-2

# CloudWatch 로그
aws logs tail /ecs/ups-t3 --follow --region ap-northeast-2

# CloudFront 통계
aws cloudfront get-distribution --id E1RLDWF8ZOYKW1
```

---

## 비용 최적화

### 현재 예상 비용 (월간)
- **ECS Fargate**: ~$30 (1 Task, 1vCPU, 2GB)
- **ALB**: ~$20
- **CloudFront**: ~$5 (1GB 전송)
- **S3**: ~$1
- **DynamoDB**: ~$5 (On-Demand)
- **총 예상**: ~$60/월

### 절감 방안
1. ECS Task 개수 조정 (Auto Scaling)
2. CloudFront 캐싱 최적화
3. DynamoDB TTL 활용
4. S3 Lifecycle 정책

---

## 참고 자료
- [AWS ECS 문서](https://docs.aws.amazon.com/ecs/)
- [CloudFront 문서](https://docs.aws.amazon.com/cloudfront/)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
