from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import asyncio
import time
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_first_spt_con_text(query: str) -> Optional[str]:
    """네이버에서 주가 정보를 크롤링합니다."""
    print(f"[DEBUG] Fetching stock data for: {query}")
    url = "https://search.naver.com/search.naver"
    params = {
        "where": "nexearch",
        "sm": "tab_hty.top",
        "ssc": "tab.nx.all",
        "query": f"{query} 주가",
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        print(f"[DEBUG] Request successful for: {query}")

        soup = BeautifulSoup(res.text, "html.parser")

        # .spt_con.dw 또는 .spt_con.up 중 첫 번째
        block = soup.select_one(".spt_con.dw, .spt_con.up")
        if not block:
            print(f"[DEBUG] No stock block found for: {query}")
            return None

        text = " ".join(block.stripped_strings)
        print(f"[DEBUG] Stock data found: {text}")
        return text
    except Exception as e:
        print(f"[ERROR] Error fetching stock data for {query}: {e}")
        return None

def parse_stock_data(text: str) -> dict:
    """
    주가 텍스트를 파싱합니다.
    예: "지수 476 전일대비 상승 1 (+0.21%)"
    예: "KRX 장마감 지수 310,500 전일대비 하락 11,000 (-3.42%) 2025.11.21."
    """
    if not text:
        return {"error": "데이터를 찾지 못했습니다."}
    
    print(f"[DEBUG] Parsing stock data: {text}")
    
    try:
        # "지수" 다음의 숫자 추출 (쉼표 포함 가능)
        price_match = re.search(r'지수\s+([\d,]+)', text)
        if not price_match:
            print("[DEBUG] Price pattern not found")
            return {"error": "데이터를 찾지 못했습니다."}
        
        price = price_match.group(1).replace(',', '')
        
        # 상승/하락 판단
        is_up = '상승' in text
        is_down = '하락' in text
        
        if not (is_up or is_down):
            print("[DEBUG] Direction (상승/하락) not found")
            return {"error": "데이터를 찾지 못했습니다."}
        
        direction = "상승" if is_up else "하락"
        
        # 변동 금액 추출
        change_match = re.search(r'(상승|하락)\s+([\d,]+)', text)
        change = change_match.group(2).replace(',', '') if change_match else "0"
        
        # 변동률 추출
        percent_match = re.search(r'$$([+-]?[\d.]+)%$$', text)
        change_percent = percent_match.group(1) if percent_match else "0"
        
        result = {
            "price": price,
            "direction": direction,
            "change": change,
            "change_percent": change_percent,
            "raw_text": text
        }
        print(f"[DEBUG] Parsed result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Error parsing stock data: {e}")
        return {"error": "데이터를 찾지 못했습니다."}

last_request_time = 0
REQUEST_INTERVAL = 1.0  # 1초 간격

# 1. API 라우트들을 먼저 정의합니다.
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    query: str

class StockPriceRequest(BaseModel):
    company: str

@app.post("/api/stock-price")
async def get_stock_price(request: StockPriceRequest):
    """특정 기업의 주가 정보를 가져옵니다."""
    global last_request_time
    
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    if time_since_last_request < REQUEST_INTERVAL:
        wait_time = REQUEST_INTERVAL - time_since_last_request
        print(f"[DEBUG] Rate limiting: waiting {wait_time:.2f}s before request")
        await asyncio.sleep(wait_time)
    
    last_request_time = time.time()
    
    try:
        print(f"[DEBUG] Stock price request received for: {request.company}")
        
        # 회사 이름에서 괄호 안의 내용 제거 (예: "KEPCO (한국전력)" -> "KEPCO")
        company_name = re.sub(r'\s*$$[^)]*$$', '', request.company).strip()
        print(f"[DEBUG] Cleaned company name: {company_name}")
        
        # 주가 정보 크롤링
        stock_text = get_first_spt_con_text(company_name)
        
        if stock_text is None:
            print(f"[DEBUG] No stock data found for: {company_name}")
            return {"error": "데이터를 찾지 못했습니다."}
        
        # 텍스트 파싱
        parsed_data = parse_stock_data(stock_text)
        print(f"[DEBUG] Returning parsed data: {parsed_data}")
        
        return parsed_data
    except Exception as e:
        print(f"[ERROR] Error in stock price endpoint: {e}")
        return {"error": "검색도중 에러가 났습니다."}

@app.post("/api/generate")
async def proxy_generate(request: QueryRequest):
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request to the deep research service running on port 8000
            response = await client.post(
                "http://127.0.0.1:8000/generate",
                json={"query": request.query},
                timeout=600.0  # Increased timeout for deep research
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Error communicating with deep research service: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Deep research service error: {exc.response.text}")

# ... 여기에 기존 백엔드 로직 추가 ...

# 2. Next.js 빌드 결과물('out' 폴더)이 있는지 확인
# 주의: 실제 실행 전 'npm run build'를 통해 out 폴더가 생성되어 있어야 합니다.
build_dir = os.path.join(os.getcwd(), "out")

if os.path.exists(build_dir):
    # 3. 정적 파일 마운트 (_next 폴더 등)
    # Next.js의 정적 자산들은 주로 _next 경로 아래에 있습니다.
    app.mount("/_next", StaticFiles(directory=os.path.join(build_dir, "_next")), name="next")
    
    # 4. 루트 경로 및 기타 정적 파일 서빙
    # SPA(Single Page Application)처럼 동작하게 하려면 404 발생 시 index.html을 반환하거나
    # 특정 경로에 맞는 html을 반환해야 합니다.
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 요청된 파일이 실제로 존재하면 그 파일을 반환 (예: favicon.ico, robots.txt)
        file_path = os.path.join(build_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Try appending .html
        html_path = os.path.join(build_dir, full_path + ".html")
        if os.path.exists(html_path) and os.path.isfile(html_path):
            return FileResponse(html_path)
            
        if full_path == "" or full_path == "/":
             index_path = os.path.join(build_dir, "index.html")
             if os.path.exists(index_path):
                return FileResponse(index_path)

        # 존재하지 않는 경로라면 index.html 반환 (Client-side Routing 지원)
        # 혹은 특정 페이지(analysis.html 등)로 매핑 로직 추가 가능
        index_path = os.path.join(build_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
            
        return HTTPException(status_code=404, detail="File not found and index.html not available")

else:
    print("Warning: 'out' directory not found. Run 'npm run build' first.")

if __name__ == "__main__":
    import uvicorn
    print("Server running at: http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
