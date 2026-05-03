import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.connectors.web_search_connector import WebSearchConnector

logger = logging.getLogger(__name__)


class SourceFinderAgent(BaseAgent):
    name = "source_finder"

    async def execute(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        location = input_data.get("location", "")
        persona = input_data.get("persona", "")
        industry = input_data.get("industry", "")
        prospect_count = input_data.get("prospect_count", 20)

        web_search = WebSearchConnector()
        companies: list[dict[str, Any]] = []

        queries = self._build_queries(location, persona, industry)

        for query in queries:
            results = await web_search.search(query=query, num_results=10)
            for result in results:
                companies.append({
                    "company_name": result.get("title", ""),
                    "website": result.get("url", ""),
                    "source_url": result.get("url", ""),
                    "relevance_reason": result.get("snippet", ""),
                })

            if len(companies) >= prospect_count * 2:
                break

        logger.info(f"SourceFinderAgent found {len(companies)} companies")
        return companies

    def _build_queries(self, location: str, persona: str, industry: str) -> list[str]:
        queries = []
        locations = [l.strip() for l in location.split(",") if l.strip()] if location else [""]
        personas = [p.strip() for p in persona.split(",") if p.strip()] if persona else [""]

        for loc in locations:
            for p in personas:
                parts = []
                if p:
                    parts.append(p)
                if industry:
                    parts.append(industry)
                if loc:
                    parts.append(loc)
                parts.append("UHNW private aviation luxury")
                queries.append(" ".join(parts))

        if not queries:
            queries = ["UHNW private aviation luxury travel companies"]

        return queries[:5]
