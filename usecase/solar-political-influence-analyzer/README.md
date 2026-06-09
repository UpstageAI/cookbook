# Political Influence Network Analyzer with Solar-Pro2

A comprehensive AI-powered platform that analyzes and visualizes relationships between politicians, policies, industries, and companies using Upstage Solar-Pro2 LLM.

## Overview

This project demonstrates how to build a sophisticated political-economic analysis system using **Upstage Solar-Pro2** as the core intelligence engine. The system processes natural language queries about politicians or policies and generates structured influence network analysis with evidence-based connections.

### Key Features

- **Multi-Agent Research System**: Coordinated AI agents for parallel information gathering
- **4-Tier Relationship Analysis**: Politicians → Policies → Industries → Companies
- **Evidence-Based Connections**: All relationships backed by credible sources
- **Interactive Visualization**: D3.js-powered network graphs
- **Real-Time Stock Integration**: Live stock prices for identified companies
- **Korean Language Optimization**: Leverages Solar-Pro2's Korean capabilities

## Architecture

```
User Query → Solar-Pro2 Router → Multi-Agent Research System → Evidence Synthesis → Visualization
                ↓                        ↓                         ↓
        Intent Classification    Parallel Web Search      Structured Output
        Query Refinement        Content Summarization    Source Attribution
```

### Technology Stack

**AI Engine (Backend)**
- **Upstage Solar-Pro2**: Primary LLM for analysis and synthesis
- **LangGraph**: Multi-agent orchestration framework
- **FastAPI**: REST API server
- **Tavily API**: Real-time web search
- **Python 3.9+**

**Frontend**
- **Next.js 16**: React framework with SSR
- **TypeScript**: Type-safe development
- **D3.js**: Interactive graph visualization
- **Tailwind CSS**: Styling

**Infrastructure**
- **AWS ECS Fargate**: Container orchestration
- **AWS CloudFront + S3**: Static hosting and CDN
- **AWS DynamoDB**: Caching and rate limiting
- **GitHub Actions**: CI/CD pipeline

## Solar-Pro2 Integration

### Core Use Cases

#### 1. Intent Classification and Query Routing
```python
from langchain_upstage import ChatUpstage

router_llm = ChatUpstage(
    api_key=UPSTAGE_API_KEY,
    model="solar-pro2",
    temperature=0,
)

# Classifies user intent and routes to appropriate research workflow
def classify_query(user_input: str) -> str:
    prompt = f"""
    Analyze this query and classify the intent:
    Query: {user_input}
    
    Classifications:
    - relationship_analysis: User wants to understand political-economic connections
    - factual_question: User wants specific facts about a person/policy
    - general_inquiry: General questions not requiring deep research
    """
    return router_llm.invoke(prompt)
```

#### 2. Multi-Agent Research Coordination
```python
# Supervisor agent coordinates 3 specialized research agents
supervisor_model = ChatUpstage(
    api_key=os.getenv("UPSTAGE_API_KEY"), 
    model="solar-pro2", 
    temperature=0
)

class ResearchSupervisor:
    def coordinate_research(self, query: str):
        # Agent 1: Policy Analysis
        # Agent 2: Industry Impact Assessment  
        # Agent 3: Company Identification
        
        tasks = self.decompose_research_tasks(query)
        results = await self.execute_parallel_research(tasks)
        return self.synthesize_findings(results)
```

#### 3. Evidence Synthesis and Structured Output
```python
writer_model = ChatUpstage(
    api_key=os.getenv("UPSTAGE_API_KEY"), 
    model="solar-pro2", 
    temperature=0
).with_structured_output(InfluenceReport)

class InfluenceReport(BaseModel):
    report_title: str
    influence_chains: List[InfluenceChain]
    evidence_sources: List[EvidenceSource]
    
    class InfluenceChain(BaseModel):
        politician: str
        policy: str
        industry: str
        companies: List[str]
        evidence: str
```

#### 4. Content Summarization
```python
summarization_model = ChatUpstage(
    api_key=UPSTAGE_API_KEY,
    model="solar-pro2",
    temperature=0.0,
)

def summarize_webpage(content: str, query_context: str) -> Summary:
    """Summarizes web content in context of the research query"""
    prompt = f"""
    Summarize this content focusing on information relevant to: {query_context}
    
    Content: {content}
    
    Provide:
    1. Key findings related to the query
    2. Relevant quotes with context
    3. Credibility assessment
    """
    return summarization_model.invoke(prompt)
```

### Performance Optimizations

- **Temperature 0.0**: Ensures consistent, factual outputs
- **Structured Output**: Forces JSON schema compliance
- **Korean Optimization**: Leverages Solar-Pro2's Korean language strengths
- **Evidence Requirements**: Anti-hallucination constraints in prompts

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Upstage API Key
- Tavily API Key (optional, for enhanced search)

### 1. Clone Repository
```bash
git clone <repository-url>
cd solar-political-influence-analyzer
```

### 2. Backend Setup
```bash
cd src/ai-engine

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# UPSTAGE_API_KEY=your_upstage_api_key_here
# TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Frontend Setup
```bash
cd src/frontend

# Install dependencies
npm install --legacy-peer-deps

# Configure environment
cp .env.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd src/ai-engine
PYTHONPATH=src python src/deep_research/main.py
```

**Terminal 2 - Frontend:**
```bash
cd src/frontend
npm run dev
```

### 5. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"query": "이재명의 정책이 어떤 기업에 영향을 미치나요?"}'
```

### Check Job Status
```bash
curl "http://localhost:8000/job/{job_id}"
```

### Expected Output Structure
```json
{
  "status": "completed",
  "result": {
    "report_title": "이재명 정치경제 영향 분석",
    "influence_chains": [
      {
        "politician": "이재명",
        "policy": "기본소득 정책",
        "industry": "핀테크",
        "companies": ["카카오페이", "토스"],
        "evidence": "기본소득 정책 시행 시 디지털 결제 시스템 수요 증가 예상..."
      }
    ],
    "evidence_sources": [
      {
        "title": "기본소득 정책과 핀테크 산업",
        "url": "https://example.com/news",
        "summary": "정책 분석 보고서에 따르면..."
      }
    ]
  }
}
```

## Code Structure & Flow

### 1. Request Processing Flow
```
User Query → FastAPI Endpoint → Router Agent → Research Coordination
```

### 2. Multi-Agent Research System
```python
# src/ai-engine/src/deep_research/multi_agent_supervisor.py
class ResearchSupervisor:
    def __init__(self):
        self.agents = {
            'policy_analyst': PolicyAnalysisAgent(),
            'industry_expert': IndustryAnalysisAgent(), 
            'company_researcher': CompanyResearchAgent()
        }
    
    async def coordinate_research(self, query: str):
        # Decompose query into specialized research tasks
        tasks = self.create_research_tasks(query)
        
        # Execute research in parallel
        results = await asyncio.gather(*[
            agent.research(task) for agent, task in tasks.items()
        ])
        
        # Synthesize findings using Solar-Pro2
        return self.synthesize_results(results)
```

### 3. Evidence Collection & Validation
```python
# src/ai-engine/src/deep_research/utils.py
async def search_and_summarize(query: str) -> List[Summary]:
    """
    1. Performs web search via Tavily API
    2. Scrapes relevant URLs with Playwright
    3. Summarizes content using Solar-Pro2
    4. Validates evidence quality
    """
    search_results = await tavily_search(query)
    summaries = []
    
    for url in search_results.urls:
        content = await scrape_webpage(url)
        summary = await summarization_model.ainvoke({
            "content": content,
            "query_context": query
        })
        summaries.append(summary)
    
    return summaries
```

### 4. Structured Output Generation
```python
# src/ai-engine/src/deep_research/research_agent_full.py
def generate_influence_report(research_data: dict) -> InfluenceReport:
    """
    Uses Solar-Pro2 with structured output to ensure consistent JSON format
    """
    writer_prompt = f"""
    Based on the research findings, create a comprehensive influence analysis:
    
    Research Data: {research_data}
    
    Requirements:
    - All connections must be evidence-based
    - Include source citations
    - Focus on publicly traded companies
    - Maintain political neutrality
    """
    
    return writer_model.invoke(writer_prompt)
```

## Key Functions Documentation

### Core Research Functions

#### `deep_researcher_builder()`
**Location**: `src/ai-engine/src/deep_research/research_agent_full.py`
**Purpose**: Builds the complete research workflow using LangGraph
**Returns**: Compiled LangGraph workflow for end-to-end analysis

#### `router_builder.compile()`
**Location**: `src/ai-engine/src/deep_research/router.py`  
**Purpose**: Routes queries to appropriate research workflows based on intent
**Key Logic**: Uses Solar-Pro2 to classify query type and select processing path

#### `search_and_summarize()`
**Location**: `src/ai-engine/src/deep_research/utils.py`
**Purpose**: Performs web search and content summarization
**Process**: 
1. Tavily API search → 2. Content scraping → 3. Solar-Pro2 summarization

#### `coordinate_research()`
**Location**: `src/ai-engine/src/deep_research/multi_agent_supervisor.py`
**Purpose**: Orchestrates parallel research across specialized agents
**Agents**: Policy Analyst, Industry Expert, Company Researcher

### API Endpoints

#### `POST /generate`
**Purpose**: Initiates new analysis job
**Input**: `{"query": "politician or policy name"}`
**Output**: `{"job_id": "uuid", "status": "processing"}`

#### `GET /job/{job_id}`
**Purpose**: Retrieves analysis results
**Output**: Complete influence network analysis with evidence

## Deployment

### Production Deployment (AWS)

The project includes complete AWS infrastructure setup:

1. **ECS Fargate**: Containerized backend deployment
2. **S3 + CloudFront**: Static frontend hosting with CDN
3. **Application Load Balancer**: API traffic routing
4. **DynamoDB**: Results caching and rate limiting

### CI/CD Pipeline

GitHub Actions workflows automatically deploy on push to main:
- `.github/workflows/deploy-backend.yml`: Backend deployment
- `.github/workflows/deploy-frontend.yml`: Frontend deployment

## Performance & Scalability

### Optimization Features
- **Result Caching**: 24-hour TTL in DynamoDB
- **Rate Limiting**: Prevents API abuse
- **Parallel Processing**: Multi-agent concurrent research
- **CDN Distribution**: Global content delivery

### Monitoring
- **Health Checks**: `/health` endpoint for load balancer
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging for debugging

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **Upstage**: Solar-Pro2 LLM API providing Korean-optimized language understanding
- **Tavily**: Real-time web search capabilities
- **LangGraph**: Multi-agent orchestration framework
- **AWS**: Cloud infrastructure and services

---

## Support

For questions or issues:
1. Check the [API Documentation](http://localhost:8000/docs) 
2. Review [troubleshooting guide](#troubleshooting)
3. Open an issue on GitHub

This project demonstrates the power of Solar-Pro2 for complex, multi-step analysis tasks requiring Korean language understanding and structured output generation.