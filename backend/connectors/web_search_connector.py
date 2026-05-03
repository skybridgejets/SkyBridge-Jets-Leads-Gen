import os
import logging
from typing import Any

import httpx

from backend.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)


class WebSearchConnector(BaseConnector):
    name = "web_search"

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_CSE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.serpapi_key = os.getenv("SERPAPI_KEY")

        if not self.google_api_key and not self.serpapi_key:
            logger.warning(
                "No search API keys set (GOOGLE_CSE_API_KEY/GOOGLE_CSE_ID or SERPAPI_KEY) "
                "— web search connector will return empty results"
            )

    async def search(self, query: str = "", num_results: int = 10, **kwargs) -> list[dict[str, Any]]:
        if self.google_api_key and self.google_cse_id:
            return await self._google_search(query, num_results)
        if self.serpapi_key:
            return await self._serpapi_search(query, num_results)
        logger.warning("No search API available — returning empty results")
        return []

    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        return None

    async def _google_search(self, query: str, num_results: int) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": self.google_api_key,
                        "cx": self.google_cse_id,
                        "q": query,
                        "num": min(num_results, 10),
                    },
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                return [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    for item in items
                ]
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

    async def _serpapi_search(self, query: str, num_results: int) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": self.serpapi_key,
                        "q": query,
                        "num": min(num_results, 10),
                        "engine": "google",
                    },
                )
                resp.raise_for_status()
                results = resp.json().get("organic_results", [])
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                    }
                    for r in results[:num_results]
                ]
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
