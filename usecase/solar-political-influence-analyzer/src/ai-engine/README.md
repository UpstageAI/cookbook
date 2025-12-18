# Upstage_team3_deep_research

# 🧠 Deep Research Agent
AI 기반 **정치–정책–산업–기업 영향 체인 분석 시스템**  
FastAPI + LangGraph + Upstage Solar 객체 출력 기반 구조화 리서치

---

## 🚀 Features
- 자연어로 질의하면 **정책 → 산업 → 기업 → 영향 체인**을 자동 탐지
- Tavily 검색 + Upstage Solar 모델 기반 **근거 중심 리서치**
- 모든 결과를 **InfluenceReport(JSON)** 형태로 반환  
- Docker 기반으로 쉽게 실행 가능

---

# 🛠️ Requirements
- Docker Desktop
- .env 파일 설정

`.env` 예시:
```

UPSTAGE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here

````

---

# 🏗️ Docker Build

프로젝트 루트에서 실행:

```bash
docker build -t deep-research .
````

---

# ▶️ Run (with env file)

```bash
docker run -p 8000:8000 --env-file .env deep-research
```

---

# 🌐 API Docs

브라우저에서 접속:

```
http://localhost:8000/docs
```

Swagger UI에서 API 테스트 가능.

---

# 📡 API 사용 예시

---

## 1) 🔍 기본 POST 요청 (curl)

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
        "query": "문재인 정부의 에너지 정책"
      }'
```

---

## 💡 예상 출력(JSON 구조)

```json
{
  "report_title": "문재인 정부의 정치·경제·기업 영향 분석",
  "time_range": "2017–2025",
  "influence_chains": [
    {
      "politician": "문재인",
      "policy": "재생에너지 확대 정책",
      "industry_or_sector": "태양광 산업",
      "companies": ["한국동서발전", "한국남동발전"],
      "impact_description": "보조금 확대의 영향으로 시장 점유율 증가 및 산업 규제 변화",
      "evidence": [
        {
          "source_title": "정부주도 태양광 정책 수혜기업",
          "url": "https://www.skyedaily.com/news/news_spot.html?ID=83547"
        }
      ]
    }
  ],
  "notes": "직접적인 로비 증거는 없음."
}
```

---

# 📁 프로젝트 구조

```
.
├── src/deep_research/
│   ├── research_agent_full.py
│   ├── multi_agent_supervisor.py
│   ├── state_scope.py
│   ├── utils.py
│   └── ...
├── pyproject.toml
├── Dockerfile
├── uv.lock
├── README.md
├── main.py   ← FastAPI 엔트리포인트
└── .env
```

---

# 🧪 테스트 시나리오

### 1) 도커 빌드

```bash
docker build -t deep-research .
```

### 2) 도커 실행

```bash
docker run -p 8000:8000 --env-file .env deep-research
```

### 3) curl 테스트

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"query": "윤석열 정부의 반도체 정책 영향"}'
```

### 4) JSON 출력 확인

Swagger UI에서도 확인 가능
[http://localhost:8000/docs](http://localhost:8000/docs)

---
