# PIN - 정치테마주 관계도 분석 플랫폼

정치인 또는 정책을 입력하면 관련 정책, 산업군, 기업을 그래프로 시각화하여 보여주는 분석 플랫폼입니다.

## 📋 요구사항

- **Node.js**: v22.x 이상
- **패키지 매니저**: pnpm
- **Python**: 3.8 이상 (백엔드 서버용)

## 🚀 시작하기

### 1. 프론트엔드 설치 및 실행

\`\`\`bash
# 의존성 설치
pnpm install

# 프로덕션 빌드
pnpm build

# 개발 서버 실행 (포트 3000)
pnpm dev

# 프로덕션 서버 실행
pnpm start
\`\`\`

### 2. 백엔드 서버 실행

이 프로젝트는 두 개의 백엔드 서버가 필요합니다:

#### Mock Server (포트 8001)
\`\`\`bash
# 현재 레포지토리의 main.py 실행
python main.py
\`\`\`

#### Deep Research Server (포트 8000)
\`\`\`bash
# 별도 레포지토리의 deep research main.py 실행
cd /path/to/deep-research
python main.py
\`\`\`

### 3. 전체 시스템 구성

\`\`\`
프론트엔드 (localhost:3000)
    ↓
Mock Server (localhost:8001)
    ↓
Deep Research API (localhost:8000)
\`\`\`

## 🏗️ 프로젝트 구조

\`\`\`
├── app/                    # Next.js 앱 라우터
│   ├── page.tsx           # 메인 페이지 (입력 화면)
│   └── analysis/          # 분석 결과 페이지
├── components/            # React 컴포넌트
│   ├── relationship-graph.tsx  # 관계도 시각화
│   └── ui/               # UI 컴포넌트
├── lib/                  # 유틸리티 및 타입
├── public/              # 정적 파일
└── main.py             # FastAPI 백엔드 서버
\`\`\`

## 🔑 주요 기능

- **정치인/정책 검색**: 정치인 이름 또는 정책명을 입력하여 관련 정보 분석
- **관계도 시각화**: 입력 → 정책 → 산업군 → 기업의 4단계 관계를 그래프로 표시
- **상세 정보 제공**: 각 노드에 마우스를 올리면 상세한 근거 자료 및 출처 확인 가능
- **반응형 디자인**: 모바일 및 데스크톱 환경 모두 지원

## 🛠️ 기술 스택

- **Frontend**: Next.js 16, React 19, TypeScript
- **Styling**: Tailwind CSS v4
- **Backend**: FastAPI (Python)
- **AI Integration**: Upstage API

## 📝 API 엔드포인트

### POST /api/query
정치인 또는 정책에 대한 관계 분석 요청

**Request Body:**
\`\`\`json
{
  "query": "이재명"
}
\`\`\`

**Response:**
\`\`\`json
{
  "report_title": "...",
  "time_range": "...",
  "influence_chains": [...],
  "notes": "..."
}
\`\`\`

## 🤝 개발 가이드

### 환경 변수 설정

`.env.local` 파일을 생성하여 필요한 환경 변수를 설정하세요:

\`\`\`env
NEXT_PUBLIC_API_URL=http://localhost:8001
UPSTAGE_API_KEY=your_api_key_here
\`\`\`

### 빌드 및 배포

\`\`\`bash
# 프로덕션 빌드
pnpm build

# 빌드 결과물 실행
pnpm start
\`\`\`

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 👥 기여

버그 리포트 및 기능 제안은 Issues를 통해 제출해주세요.
