"""Data models for the note freshness check module."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class FreshnessMetadata:
    """Represents metadata for freshness checking.

    Attributes:
        info_keyword: Keywords for Wikipedia search
        info_query: Query strings for Tavily search
        wiki_searched_at: Timestamp of last Wikipedia search
        tavily_searched_at: Timestamp of last Tavily search
    """

    info_keyword: List[str] = field(default_factory=list)
    info_query: List[str] = field(default_factory=list)
    wiki_searched_at: Optional[str] = None
    tavily_searched_at: Optional[str] = None

    def to_yaml_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        result = {}
        if self.info_keyword:
            result["info_keyword"] = self.info_keyword
        if self.info_query:
            result["info_query"] = self.info_query
        if self.wiki_searched_at:
            result["wiki_searched_at"] = self.wiki_searched_at
        if self.tavily_searched_at:
            result["tavily_searched_at"] = self.tavily_searched_at
        return result


@dataclass
class WikiSearchResult:
    """Wikipedia search result.

    Attributes:
        keyword: Search keyword used
        title: Article title
        summary: Article summary
        url: Article URL
        searched_at: Search timestamp
    """

    keyword: str
    title: str
    summary: str
    url: str
    searched_at: str


@dataclass
class TavilySearchResult:
    """Tavily search result.

    Attributes:
        query: Search query used
        results: List of search result items
        searched_at: Search timestamp
    """

    query: str
    results: List[dict]
    searched_at: str


@dataclass
class DescriptionTemplate:
    """Template for information extraction description.

    Attributes:
        name: Template name
        description: Template description for UI
        content: The actual description content for API
    """

    name: str
    description: str
    content: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DescriptionTemplate":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            content=data.get("content", ""),
        )
