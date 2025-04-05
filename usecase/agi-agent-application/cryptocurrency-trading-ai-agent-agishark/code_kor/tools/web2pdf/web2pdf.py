import asyncio
from playwright.async_api import async_playwright
import os
import time
import nest_asyncio

# Jupyter/IPython 환경에서 asyncio 사용 가능하게 설정
nest_asyncio.apply()

async def _save_webpage_as_pdf(url: str) -> str:
    """
    웹페이지를 PDF로 저장하는 내부 비동기 함수

    Args:
        url (str): PDF로 저장할 웹페이지 URL

    Returns:
        str: 저장된 PDF 파일의 경로. 실패시 None.
    """
    try:
        # 출력 디렉토리 고정
        output_dir = 'tools/web2pdf/always_see_doc_storage'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 페이지 로드 및 대기
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('load')
            await page.wait_for_timeout(3000)
            
            # PDF 파일명 생성
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            domain = url.split('/')[2] if len(url.split('/')) > 2 else 'webpage'
            pdf_path = os.path.join(output_dir, f'{timestamp}_{domain}.pdf')
            
            # PDF로 저장
            await page.pdf(path=pdf_path)
            await browser.close()
            
            return pdf_path
                
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return None

def save_webpage_as_pdf(url: str) -> str:
    """
    웹페이지를 PDF로 저장하는 함수

    Args:
        url (str): PDF로 저장할 웹페이지 URL

    Returns:
        str: 저장된 PDF 파일의 경로. 실패시 None.

    Example:
        >>> pdf_path = save_webpage_as_pdf('https://example.com')
        >>> print(pdf_path)
        'always_see_doc_storage/20240220-123456_example.com.pdf'
    """
    return asyncio.get_event_loop().run_until_complete(_save_webpage_as_pdf(url))
