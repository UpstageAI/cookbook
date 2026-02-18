import asyncio
from playwright.async_api import async_playwright
import os
import time
import nest_asyncio

# Configure asyncio to work in Jupyter/IPython environments
nest_asyncio.apply()

async def _save_webpage_as_pdf(url: str) -> str:
    """
    Internal asynchronous function to save a webpage as PDF

    Args:
        url (str): URL of the webpage to save as PDF

    Returns:
        str: Path to the saved PDF file. None if failed.
    """
    try:
        # Fixed output directory
        output_dir = 'tools/web2pdf/always_see_doc_storage'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load page and wait
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('load')
            await page.wait_for_timeout(3000)
            
            # Generate PDF filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            domain = url.split('/')[2] if len(url.split('/')) > 2 else 'webpage'
            pdf_path = os.path.join(output_dir, f'{timestamp}_{domain}.pdf')
            
            # Save as PDF
            await page.pdf(path=pdf_path)
            await browser.close()
            
            return pdf_path
                
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return None

def save_webpage_as_pdf(url: str) -> str:
    """
    Function to save a webpage as PDF

    Args:
        url (str): URL of the webpage to save as PDF

    Returns:
        str: Path to the saved PDF file. None if failed.

    Example:
        >>> pdf_path = save_webpage_as_pdf('https://example.com')
        >>> print(pdf_path)
        'always_see_doc_storage/20240220-123456_example.com.pdf'
    """
    return asyncio.get_event_loop().run_until_complete(_save_webpage_as_pdf(url))
