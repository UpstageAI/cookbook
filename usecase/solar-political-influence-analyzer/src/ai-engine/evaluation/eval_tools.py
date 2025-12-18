import asyncio
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

class URLScraper:
    """
    Playwright를 사용해 URL을 열고 텍스트를 긁어오는 도우미 클래스.

    - 평가 워크플로우에서:
        1) 딥리서치 결과 JSON에서 url 리스트 추출
        2) URLScraper.fetch_many(urls) 호출
        3) 반환된 text를 LLM-as-a-judge 프롬프트에 넣어
           Evidence Quality / Hallucination / URL Validity 평가에 사용
    """

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 20_000,
        wait_until: str = "domcontentloaded",
        max_chars: int = 50_000,
        user_agent: Optional[str] = None,
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.wait_until = wait_until
        self.max_chars = max_chars
        self.user_agent = user_agent or DEFAULT_UA

    async def _create_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=self.headless)
        return playwright, browser

    async def fetch_one(self, url: str) -> Dict[str, Any]:
        """
        단일 URL을 열고 내용을 가져온다.

        반환 형식:
        {
            "url": str,
            "ok": bool,                # 2xx~3xx 이면 True
            "status": Optional[int],   # HTTP status code
            "final_url": Optional[str],
            "title": Optional[str],
            "text": str,               # 정제된 본문 텍스트
            "error": Optional[str],
        }
        """
        playwright = None
        browser = None

        status: Optional[int] = None
        final_url: Optional[str] = None
        title: Optional[str] = None
        text: str = ""
        error: Optional[str] = None

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=self.headless)

            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()

            resp = None
            try:
                resp = await page.goto(
                    url,
                    wait_until=self.wait_until,
                    timeout=self.timeout_ms,
                )
            except PlaywrightTimeoutError:
                error = f"Timeout after {self.timeout_ms} ms"
            except Exception as e:
                error = f"{type(e).__name__}: {e}"

            if resp:
                status = resp.status
                final_url = resp.url

            # SPA / 동적 로딩 고려해서 약간 더 대기
            try:
                await page.wait_for_load_state("networkidle", timeout=2000)
            except Exception:
                pass

            # HTML 가져오기
            try:
                html = await page.content()
            except Exception:
                html = ""

            if not final_url:
                try:
                    final_url = page.url
                except Exception:
                    final_url = url

            soup = BeautifulSoup(html, "html.parser")

            # 비콘텐츠 영역 제거
            for tag in soup(
                ["script", "style", "header", "footer", "nav", "aside", "form", "iframe"]
            ):
                tag.decompose()

            main_content = soup.body
            target_soup = main_content if main_content else soup

            clean_text = target_soup.get_text(separator=" ", strip=True)
            clean_text = re.sub(r"\s+", " ", clean_text)

            # 로그인 페이지 처리 (대략적인 heuristic)
            if "로그인" in clean_text and "해주세요" in clean_text:
                text = "🔒 [접근 제한] 로그인 필요한 페이지입니다."
            else:
                text = clean_text[: self.max_chars]

            # title 추출
            try:
                title = await page.title()
            except Exception:
                title = None

            await context.close()

        finally:
            if browser is not None:
                await browser.close()
            if playwright is not None:
                await playwright.stop()

        return {
            "url": url,
            "ok": status is not None and 200 <= status < 400,
            "status": status,
            "final_url": final_url,
            "title": title,
            "text": text,
            "error": error,
        }

    async def fetch_many(self, urls: List[str], concurrency: int = 3) -> List[Dict[str, Any]]:
        """
        여러 URL을 병렬로 긁어오기.

        - concurrency: 동시에 몇 개까지 열지 (너무 크게 하면 사이트가 막거나 느려질 수 있음)
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _worker(u: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.fetch_one(u)

        tasks = [asyncio.create_task(_worker(u)) for u in urls]
        results = await asyncio.gather(*tasks)
        return results
