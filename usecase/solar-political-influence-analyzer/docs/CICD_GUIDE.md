# CI/CD 가이드

## 개요

GitHub Actions를 사용한 자동 배포 파이프라인 구성 가이드입니다.

**CI/CD 플로우:**
```
코드 푸시 (GitHub)
    ↓
GitHub Actions 트리거
    ↓
Docker 이미지 빌드
    ↓
ECR에 푸시
    ↓
ECS 서비스 업데이트 (자동 배포)
```

---

## 사전 준비

### 1. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions

**필수 Secrets:**
- `AWS_ACCESS_KEY_ID`: AWS IAM 액세스 키
- `AWS_SECRET_ACCESS_KEY`: AWS IAM 시크릿 키

### 2. IAM 권한 설정

GitHub Actions에서 사용할 IAM 사용자에 다음 권한 필요:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ups-t3-frontend-*",
        "arn:aws:s3:::ups-t3-frontend-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Workflow 구성

### 1. Backend (AI Engine) 배포

**파일:** `.github/workflows/deploy-backend.yml`

**트리거 조건:**
- `main` 브랜치에 푸시
- `src/ai-engine/**` 경로 변경 시

**배포 단계:**
1. 코드 체크아웃
2. AWS 자격 증명 설정
3. ECR 로그인
4. Docker 이미지 빌드 및 푸시
5. ECS 서비스 강제 재배포
6. 서비스 안정화 대기

**사용 예시:**
```bash
# AI 엔진 코드 수정 후
git add src/ai-engine/
git commit -m "Update AI engine"
git push origin main

# GitHub Actions 자동 실행
# https://github.com/your-repo/actions
```

### 2. Frontend 배포

**파일:** `.github/workflows/deploy-frontend.yml`

**트리거 조건:**
- `main` 브랜치에 푸시
- `src/frontend/**` 경로 변경 시

**배포 단계:**
1. 코드 체크아웃
2. Node.js 설정
3. 의존성 설치
4. Next.js 빌드
5. S3에 업로드
6. CloudFront 캐시 무효화

**사용 예시:**
```bash
# 프론트엔드 코드 수정 후
git add src/frontend/
git commit -m "Update frontend UI"
git push origin main

# GitHub Actions 자동 실행
```

---

## 배포 모니터링

### GitHub Actions 로그 확인

1. GitHub 저장소 → Actions 탭
2. 실행 중인 워크플로우 클릭
3. 각 단계별 로그 확인

### ECS 배포 상태 확인

```bash
# ECS 서비스 상태
aws ecs describe-services \
  --cluster ups-t3-cluster \
  --services ups-t3-service \
  --region ap-northeast-2

# 최근 배포 이벤트
aws ecs describe-services \
  --cluster ups-t3-cluster \
  --services ups-t3-service \
  --query 'services[0].events[:5]' \
  --region ap-northeast-2
```

### CloudFront 무효화 상태 확인

```bash
aws cloudfront list-invalidations \
  --distribution-id E1RLDWF8ZOYKW1 \
  --max-items 5
```

---

## 롤백 전략

### Backend 롤백

**방법 1: 이전 이미지로 복원**
```bash
# ECR에서 이전 이미지 태그 확인
aws ecr describe-images \
  --repository-name ups-t3-ai-engine \
  --region ap-northeast-2

# Task Definition에서 이미지 변경
aws ecs update-service \
  --cluster ups-t3-cluster \
  --service ups-t3-service \
  --task-definition ups-t3-task:PREVIOUS_REVISION \
  --force-new-deployment
```

**방법 2: Git 커밋 되돌리기**
```bash
git revert HEAD
git push origin main
# GitHub Actions가 자동으로 이전 버전 배포
```

### Frontend 롤백

**방법 1: S3 버전 관리 활용**
```bash
# S3 버전 관리 활성화 필요
aws s3api list-object-versions \
  --bucket ups-t3-frontend-1763878138 \
  --prefix index.html

# 이전 버전 복원
aws s3api copy-object \
  --copy-source ups-t3-frontend-1763878138/index.html?versionId=VERSION_ID \
  --bucket ups-t3-frontend-1763878138 \
  --key index.html
```

**방법 2: Git 커밋 되돌리기**
```bash
git revert HEAD
git push origin main
```

---

## 환경별 배포

### Development 환경

**브랜치:** `develop`

```yaml
# .github/workflows/deploy-dev.yml
on:
  push:
    branches:
      - develop

env:
  ECS_CLUSTER: ups-t3-dev-cluster
  S3_BUCKET: ups-t3-frontend-dev
```

### Staging 환경

**브랜치:** `staging`

```yaml
# .github/workflows/deploy-staging.yml
on:
  push:
    branches:
      - staging

env:
  ECS_CLUSTER: ups-t3-staging-cluster
  S3_BUCKET: ups-t3-frontend-staging
```

### Production 환경

**브랜치:** `main`

**수동 승인 추가:**
```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://d31ad140yvex7c.cloudfront.net
    # GitHub에서 수동 승인 필요
```

---

## 트러블슈팅

### 1. ECR 푸시 실패

**문제:** `denied: Your authorization token has expired`

**해결:**
```bash
# ECR 로그인 재시도
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin 663120345697.dkr.ecr.ap-northeast-2.amazonaws.com
```

### 2. ECS 배포 타임아웃

**문제:** 서비스 안정화 대기 시간 초과

**해결:**
```bash
# 헬스체크 로그 확인
aws ecs describe-tasks \
  --cluster ups-t3-cluster \
  --tasks $(aws ecs list-tasks --cluster ups-t3-cluster --service ups-t3-service --query 'taskArns[0]' --output text)

# CloudWatch 로그 확인
aws logs tail /ecs/ups-t3 --follow
```

### 3. S3 업로드 권한 오류

**문제:** `Access Denied`

**해결:**
```bash
# IAM 정책 확인
aws iam get-user-policy \
  --user-name github-actions-user \
  --policy-name S3AccessPolicy

# 버킷 정책 확인
aws s3api get-bucket-policy --bucket ups-t3-frontend-1763878138
```

### 4. CloudFront 캐시 무효화 실패

**문제:** 무효화 요청 실패

**해결:**
```bash
# 배포 상태 확인
aws cloudfront get-distribution --id E1RLDWF8ZOYKW1

# 수동 무효화
aws cloudfront create-invalidation \
  --distribution-id E1RLDWF8ZOYKW1 \
  --paths "/*"
```

---

## 성능 최적화

### 1. Docker 빌드 캐싱

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v2

- name: Build and push
  uses: docker/build-push-action@v4
  with:
    context: ./src/ai-engine
    push: true
    tags: ${{ steps.login-ecr.outputs.registry }}/ups-t3-ai-engine:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 2. npm 캐싱

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '18'
    cache: 'npm'
    cache-dependency-path: src/frontend/package-lock.json
```

### 3. 병렬 배포

```yaml
jobs:
  deploy-backend:
    # Backend 배포
  
  deploy-frontend:
    # Frontend 배포
    # Backend와 독립적으로 실행
```

---

## 보안 권장사항

### 1. Secrets 관리
- GitHub Secrets에 민감 정보 저장
- 로그에 Secrets 노출 방지
- 정기적으로 액세스 키 교체

### 2. 최소 권한 원칙
- IAM 사용자에 필요한 최소 권한만 부여
- 리소스별 세분화된 권한 설정

### 3. 브랜치 보호
```bash
# main 브랜치 보호 규칙 설정
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
```

---

## 참고 자료

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [AWS ECR 문서](https://docs.aws.amazon.com/ecr/)
- [AWS ECS 문서](https://docs.aws.amazon.com/ecs/)
- [CloudFront 무효화](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_CreateInvalidation.html)
