import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.connectors.apollo_connector import ApolloConnector
from backend.connectors.web_search_connector import WebSearchConnector

logger = logging.getLogger(__name__)

TARGET_TITLES = [
    "PA", "EA", "Chief of Staff", "Estate Manager",
    "Family Office", "Founder", "CEO",
    "Concierge Manager", "Lifestyle Manager",
    "Yacht Broker", "Luxury Travel Advisor", "Real Estate Agent",
]


class ProspectDiscoveryAgent(BaseAgent):
    name = "prospect_discovery"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        apollo = ApolloConnector()
        web_search = WebSearchConnector()
        prospects: list[dict[str, Any]] = []

        title_query = ", ".join(TARGET_TITLES[:6])

        apollo_results = await apollo.search_people(
            title=title_query,
            limit=50,
        )
        for person in apollo_results:
            prospects.append({
                "name": person.get("name", ""),
                "title": person.get("title", ""),
                "company": person.get("company", ""),
                "company_website": person.get("company_website", ""),
                "email": person.get("email", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "location": person.get("location", ""),
                "source": "apollo",
            })

        if web_search.is_enabled():
            for company_info in input_data[:20]:
                company_name = company_info.get("company_name", "")
                if not company_name:
                    continue

                search_results = await web_search.search(
                    query=f'"{company_name}" team leadership chief staff PA estate manager',
                    num_results=3,
                )
                for result in search_results:
                    prospects.append({
                        "name": "",
                        "title": "",
                        "company": company_name,
                        "company_website": company_info.get("website", ""),
                        "source_url": result.get("url", ""),
                        "source": "web_search",
                        "raw_snippet": result.get("snippet", ""),
                    })

        # If no people from Apollo and no web search, create prospect stubs from companies
        if not prospects and input_data:
            for company_info in input_data[:20]:
                company_name = company_info.get("company_name", "")
                if not company_name:
                    continue
                prospects.append({
                    "name": "",
                    "title": "",
                    "company": company_name,
                    "company_website": company_info.get("website", ""),
                    "source_url": company_info.get("source_url", ""),
                    "source": company_info.get("source", "apollo"),
                    "location": company_info.get("location", ""),
                    "industry": company_info.get("industry", ""),
                })

        logger.info(f"ProspectDiscoveryAgent found {len(prospects)} raw prospects")
        return prospects
