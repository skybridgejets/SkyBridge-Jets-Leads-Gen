import os
import logging
from typing import Any

import httpx
from openai import AsyncOpenAI

from backend.connectors.base_connector import BaseConnector
from backend.connectors.web_search_connector import WebSearchConnector

logger = logging.getLogger(__name__)


class ManualConnector(BaseConnector):
    name = "manual"

    def __init__(self):
        self.web_search = WebSearchConnector()
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def search(self, **kwargs) -> list[dict[str, Any]]:
        return []

    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        return None

    async def research_company(self, name_or_url: str = "", **kwargs) -> dict[str, Any] | None:
        if not name_or_url:
            return None

        search_results = await self.web_search.search(
            query=f"{name_or_url} company contacts leadership team",
            num_results=5,
        )

        if not search_results and not self.openai_client:
            return None

        snippets = "\n".join(
            f"- {r.get('title', '')}: {r.get('snippet', '')} ({r.get('url', '')})"
            for r in search_results
        )

        if not self.openai_client:
            return {
                "company_name": name_or_url,
                "search_results": search_results,
                "source": "manual_web_search",
            }

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a research assistant for a private jet brokerage. "
                            "Extract structured company and contact data from the provided search results. "
                            "Return JSON with keys: company_name, website, industry, location, "
                            "key_contacts (list of {name, title, email if found}), relevance_to_private_aviation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Research this company/URL: {name_or_url}\n\nSearch results:\n{snippets}",
                    },
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            import json
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            result["source"] = "manual_gpt4o"
            return result
        except Exception as e:
            logger.error(f"Manual research_company GPT call failed: {e}")
            return {
                "company_name": name_or_url,
                "search_results": search_results,
                "source": "manual_web_search",
                "error": str(e),
            }
