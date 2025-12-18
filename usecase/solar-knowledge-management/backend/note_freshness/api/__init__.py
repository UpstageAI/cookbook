"""External API clients for note freshness module."""

from .wikipedia import WikipediaClient
from .tavily import TavilyClient

__all__ = ["WikipediaClient", "TavilyClient"]
