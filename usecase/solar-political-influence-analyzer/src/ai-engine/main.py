import os
import json
import asyncio
import uuid
import re
import urllib.request
import urllib.parse
from typing import Dict
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from deep_research.research_agent_full import deep_researcher_builder
from pydantic import BaseModel
from fastapi import HTTPException
from deep_research.router import router_builder

load_dotenv()

app = FastAPI(title="Deep Research Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for ALB"""
    return {"status": "healthy", "service": "deep-research"}

class QueryRequest(BaseModel):
    query: str

class StockRequest(BaseModel):
    company: str

checkpointer = InMemorySaver()
full_agent = router_builder.compile(checkpointer=checkpointer)

# Job 저장소 (메모리)
jobs: Dict[str, dict] = {}


async def run_agent(query: str):
    """에이전트를 실행하고 결과(JSON) 반환"""
    thread = {"configurable": {"thread_id": str(uuid.uuid4()), "recursion_limit": 10}}
    result = await full_agent.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config=thread
    )
    data = result.get("final_report", {})
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    return json_str


@app.post("/generate")
async def generate_report(request: QueryRequest, background_tasks: BackgroundTasks):
    """POST /generate { "query": "도널드 트럼프" } - Job ID 반환"""
    query = request.query

    if not query:
        raise HTTPException(400, "query field is required")

    # Job ID 생성
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "processing",
        "query": query,
        "result": None,
        "error": None
    }
    
    # 백그라운드에서 실행
    background_tasks.add_task(process_job, job_id, query)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """GET /job/{job_id} - Job 상태 확인"""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    return jobs[job_id]

async def process_job(job_id: str, query: str):
    """백그라운드에서 AI 분석 실행"""
    try:
        result = await run_agent(query)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = json.loads(result)
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/stock-price")
async def get_stock_price(request: StockRequest):
    """POST /stock-price { "company": "삼성전자" }"""
    company = request.company
    
    if not company:
        raise HTTPException(400, "company field is required")
    
    try:
        stock_data = get_stock_price_sync(company)
        return stock_data
    except Exception as e:
        return {
            'company': company,
            'error': f'주가 정보를 가져올 수 없습니다: {str(e)}'
        }

def get_stock_price_sync(company: str) -> dict:
    """네이버에서 주가 정보 크롤링"""
    try:
        company_name = re.sub(r'\s*\([^)]*\)', '', company).strip()
        
        url = "https://search.naver.com/search.naver"
        params = {
            "where": "nexearch",
            "sm": "tab_hty.top",
            "ssc": "tab.nx.all",
            "query": f"{company_name} 주가"
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # .spt_con.dw 또는 .spt_con.up 패턴 찾기
        spt_con_pattern = r'<[^>]*class="[^"]*spt_con[^"]*(?:dw|up)[^"]*"[^>]*>([^<]*(?:<[^>]*>[^<]*)*)</[^>]*>'
        spt_match = re.search(spt_con_pattern, html)
        
        if not spt_match:
            # 대체 패턴: 지수 직접 찾기
            price_pattern = r'지수\s+([\d,]+)'
            direction_pattern = r'(상승|하락)\s+([\d,]+)'
            percent_pattern = r'\(([+-]?[\d.]+)%\)'
            
            price_match = re.search(price_pattern, html)
            direction_match = re.search(direction_pattern, html)
            percent_match = re.search(percent_pattern, html)
            
            if price_match:
                price = price_match.group(1).replace(',', '')
                direction = direction_match.group(1) if direction_match else '보합'
                change = direction_match.group(2).replace(',', '') if direction_match else '0'
                change_percent = percent_match.group(1) if percent_match else '0'
                
                return {
                    'company': company,
                    'price': price,
                    'direction': direction,
                    'change': change,
                    'change_percent': change_percent
                }
        else:
            # spt_con 블록에서 데이터 추출
            text = re.sub(r'<[^>]*>', ' ', spt_match.group(1)).strip()
            text = ' '.join(text.split())
            
            # "지수" 다음의 숫자 추출
            price_match = re.search(r'지수\s+([\d,]+)', text)
            if not price_match:
                return {'company': company, 'error': '데이터를 찾지 못했습니다.'}
            
            price = price_match.group(1).replace(',', '')
            
            # 상승/하락 판단
            is_up = '상승' in text
            is_down = '하락' in text
            
            if not (is_up or is_down):
                return {'company': company, 'error': '데이터를 찾지 못했습니다.'}
            
            direction = '상승' if is_up else '하락'
            
            # 변동 금액 추출
            change_match = re.search(r'(상승|하락)\s+([\d,]+)', text)
            change = change_match.group(2).replace(',', '') if change_match else '0'
            
            # 변동률 추출
            percent_match = re.search(r'\(([+-]?[\d.]+)%\)', text)
            change_percent = percent_match.group(1) if percent_match else '0'
            
            return {
                'company': company,
                'price': price,
                'direction': direction,
                'change': change,
                'change_percent': change_percent
            }
        
        return {'company': company, 'error': '데이터를 찾지 못했습니다.'}
            
    except Exception as e:
        return {
            'company': company,
            'error': f'검색도중 에러가 났습니다: {str(e)}'
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
