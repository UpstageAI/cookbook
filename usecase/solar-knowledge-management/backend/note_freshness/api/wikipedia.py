"""Wikipedia API client for searching and retrieving articles."""

import wikipedia
from typing import Optional, Dict, Any
from datetime import datetime


class WikipediaClient:
    """Client for Wikipedia API using wikipedia package."""

    def __init__(self, language: str = "ko"):
        """Initialize Wikipedia client.

        Args:
            language: Wikipedia language code (default: ko for Korean)
        """
        self.language = language
        wikipedia.set_lang(language)

    def search_and_get_summary(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Search for a keyword and get the summary of the top result.

        Args:
            keyword: Search keyword

        Returns:
            Dictionary with keyword, title, summary, url, and searched_at
        """
        result = {
            "keyword": keyword,
            "wiki_exists": False,
            "title": "",
            "summary": "Wikipedia에서 해당 키워드에 대한 문서 요약 정보를 찾지 못함",
            "url": "",
            "searched_at": datetime.now().isoformat(),
        }

        try:
            # Search for keyword (get top 1 result)
            page_titles = wikipedia.search(keyword, results=1)

            if not page_titles:
                print(f"문서 미존재: '{keyword}' 검색 결과가 없습니다.")
                return result

            page_title = page_titles[0]

            # Get page summary
            page_summary = wikipedia.summary(
                page_title, sentences=3, auto_suggest=False
            )

            # Get page for URL
            try:
                page = wikipedia.page(page_title, auto_suggest=False)
                url = page.url
            except Exception:
                url = f"https://{self.language}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

            # Update result
            result["wiki_exists"] = True
            result["title"] = page_title
            result["summary"] = page_summary
            result["url"] = url

            print(f"문서 존재: '{page_title}'")
            return result

        except wikipedia.exceptions.PageError:
            print(f"문서 미존재: '{keyword}' - 제목이 정확히 일치하는 문서가 없습니다.")
            return result
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"모호성: '{keyword}' - 여러 문서가 검색됨. 옵션: {e.options[:3]}")
            result["wiki_exists"] = True
            result["title"] = keyword
            result["summary"] = (
                f"모호성 해소 필요: 다음 중 하나를 선택해야 합니다: {e.options[:3]}"
            )
            result["url"] = (
                f"https://{self.language}.wikipedia.org/wiki/{keyword.replace(' ', '_')}"
            )
            return result
        except Exception as e:
            print(f"Wikipedia API 오류 발생: {e}")
            result["summary"] = f"Wikipedia API 처리 중 오류 발생: {e}"
            return result
