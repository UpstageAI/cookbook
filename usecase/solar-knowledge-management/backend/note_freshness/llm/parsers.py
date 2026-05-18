"""Parsers for LLM responses."""

import json
import re
from typing import List, Optional, Dict, Any


class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def parse_extraction_result(result: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Parse information extraction result to get keywords and queries.

        Args:
            result: Raw extraction result from API

        Returns:
            Tuple of (info_keyword list, info_query list)
        """
        info_keyword = []
        info_query = []

        if not result:
            return info_keyword, info_query

        # Try to extract from various possible formats
        if isinstance(result, dict):
            # Direct extraction
            if "info_keyword" in result:
                kw = result["info_keyword"]
                info_keyword = kw if isinstance(kw, list) else [kw]

            if "info_query" in result:
                q = result["info_query"]
                info_query = q if isinstance(q, list) else [q]

            # Try nested structure
            if "extraction" in result:
                return ResponseParser.parse_extraction_result(result["extraction"])

        return info_keyword, info_query

    @staticmethod
    def parse_wiki_content(content: str) -> str:
        """Parse Wikipedia content for markdown format."""
        # Clean up content
        content = re.sub(r"\[\[([^\]|]+)\|?[^\]]*\]\]", r"\1", content)
        return content.strip()

    @staticmethod
    def parse_tavily_results(results: List[dict]) -> List[dict]:
        """Parse Tavily search results.

        Args:
            results: Raw Tavily results

        Returns:
            List of parsed result dictionaries
        """
        parsed = []
        for result in results[:3]:  # Limit to top 3 results
            parsed.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0),
                }
            )
        return parsed

    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from a response."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None
