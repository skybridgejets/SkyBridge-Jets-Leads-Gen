import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.connectors.apollo_connector import ApolloConnector
from backend.connectors.web_search_connector import WebSearchConnector

logger = logging.getLogger(__name__)

UHNW_KEYWORDS = [
    "private aviation", "luxury travel", "family office",
    "wealth management", "concierge", "estate management",
    "luxury real estate", "yacht", "private jet",
]


class SourceFinderAgent(BaseAgent):
    name = "source_finder"

    async def execute(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        location = input_data.get("location", "")
        persona = input_data.get("persona", "")
        industry = input_data.get("industry", "")
        prospect_count = input_data.get("prospect_count", 20)

        companies: list[dict[str, Any]] = []

        apollo = ApolloConnector()
        locations = [l.strip() for l in location.split(",") if l.strip()] if location else [""]

        for loc in locations:
            keywords = list(UHNW_KEYWORDS)
            if industry:
                keywords.insert(0, industry)
            if persona:
                keywords.insert(0, persona)

            apollo_orgs = await apollo.search_organizations(
                location=loc,
                keywords=keywords[:5],
                limit=min(prospect_count * 2, 50),
            )
            for org in apollo_orgs:
                companies.append(org)

            if len(companies) >= prospect_count * 2:
                break

        web_search = WebSearchConnector()
        if web_search.is_enabled():
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
