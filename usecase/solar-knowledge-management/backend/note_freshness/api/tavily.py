"""Tavily Search API client."""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..config import Config


class TavilyClient:
    """Client for Tavily Search API."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily client.

        Args:
            api_key: Tavily API key (defaults to Config.TAVILY_API_KEY)
        """
        self.api_key = api_key or Config.TAVILY_API_KEY
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required")

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Search using Tavily API.

        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            max_results: Maximum number of results
            include_answer: Include AI-generated answer
            include_raw_content: Include raw page content

        Returns:
            Search results dictionary or None on error
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.BASE_URL, json=payload)
                response.raise_for_status()
                data = response.json()

                return {
                    "query": query,
                    "results": data.get("results", []),
                    "answer": data.get("answer", ""),
                    "searched_at": datetime.now().isoformat(),
                }
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during Tavily search: {e}")
            return None
        except Exception as e:
            print(f"Error during Tavily search: {e}")
            return None

    def search_and_parse(
        self, query: str, max_results: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Search and parse results for freshness check.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            Parsed search results with query, results, and searched_at
        """
        result = self.search(query, max_results=max_results)
        if not result:
            return None

        # Parse and limit results
        parsed_results = []
        for item in result.get("results", [])[:max_results]:
            parsed_results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date", ""),
                }
            )

        return {
            "query": query,
            "results": parsed_results,
            "searched_at": result["searched_at"],
        }
