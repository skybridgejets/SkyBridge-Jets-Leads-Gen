import os
import logging
from typing import Any

import httpx

from backend.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/v1"


class ApolloConnector(BaseConnector):
    name = "apollo"

    def __init__(self):
        self.api_key = os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            logger.warning("APOLLO_API_KEY not set — Apollo connector will return empty results")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key or "",
        }

    async def search(self, **kwargs) -> list[dict[str, Any]]:
        return await self.search_people(**kwargs)

    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        return await self.enrich_person(**kwargs)

    async def search_organizations(
        self,
        location: str = "",
        keywords: list[str] | None = None,
        limit: int = 25,
        **kwargs,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                payload: dict[str, Any] = {
                    "per_page": min(limit, 100),
                    "page": 1,
                }
                if location:
                    payload["organization_locations"] = [location]
                if keywords:
                    payload["q_organization_keyword_tags"] = keywords

                resp = await client.post(
                    f"{APOLLO_BASE_URL}/organizations/search",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                orgs = data.get("organizations", [])
                return [
                    {
                        "company_name": o.get("name", ""),
                        "website": o.get("website_url", ""),
                        "source_url": o.get("website_url", ""),
                        "industry": o.get("industry", ""),
                        "location": f"{o.get('city', '')}, {o.get('country', '')}".strip(", "),
                        "relevance_reason": f"Apollo org: {o.get('industry', '')}",
                        "source": "apollo",
                    }
                    for o in orgs
                ]
        except Exception as e:
            logger.error(f"Apollo search_organizations failed: {e}")
            return []

    async def search_people(
        self,
        title: str = "",
        location: str = "",
        industry: str = "",
        limit: int = 25,
        **kwargs,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                payload: dict[str, Any] = {
                    "per_page": min(limit, 100),
                    "page": 1,
                }
                if title:
                    payload["person_titles"] = [t.strip() for t in title.split(",")]
                if location:
                    payload["person_locations"] = [location]
                if industry:
                    payload["organization_industry_tag_ids"] = [industry]

                resp = await client.post(
                    f"{APOLLO_BASE_URL}/mixed_people/search",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                people = data.get("people", [])
                return [
                    {
                        "name": p.get("name", ""),
                        "title": p.get("title", ""),
                        "company": p.get("organization", {}).get("name", "") if p.get("organization") else "",
                        "company_website": p.get("organization", {}).get("website_url", "") if p.get("organization") else "",
                        "email": p.get("email", ""),
                        "linkedin_url": p.get("linkedin_url", ""),
                        "location": (
                            f"{p.get('city', '')}, {p.get('country', '')}".strip(", ")
                        ),
                        "source": "apollo",
                    }
                    for p in people
                ]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403 or "not accessible" in str(e.response.text):
                logger.warning("Apollo people search not available on current plan — skipping")
            else:
                logger.error(f"Apollo search_people failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Apollo search_people failed: {e}")
            return []

    async def enrich_person(
        self,
        name: str = "",
        company: str = "",
        email: str = "",
        **kwargs,
    ) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                payload: dict[str, Any] = {}
                if email:
                    payload["email"] = email
                if name:
                    parts = name.split(" ", 1)
                    payload["first_name"] = parts[0]
                    payload["last_name"] = parts[1] if len(parts) > 1 else ""
                if company:
                    payload["organization_name"] = company

                resp = await client.post(
                    f"{APOLLO_BASE_URL}/people/match",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                person = data.get("person", {})
                if not person:
                    return None
                return {
                    "name": person.get("name", ""),
                    "title": person.get("title", ""),
                    "company": person.get("organization", {}).get("name", "") if person.get("organization") else "",
                    "company_website": person.get("organization", {}).get("website_url", "") if person.get("organization") else "",
                    "email": person.get("email", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "location": f"{person.get('city', '')}, {person.get('country', '')}".strip(", "),
                    "source": "apollo",
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403 or "not accessible" in str(e.response.text):
                logger.warning("Apollo people match not available on current plan — skipping")
            else:
                logger.error(f"Apollo enrich_person failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Apollo enrich_person failed: {e}")
            return None

    async def enrich_company(self, domain: str = "", **kwargs) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{APOLLO_BASE_URL}/organizations/enrich",
                    headers=self._headers(),
                    params={"domain": domain},
                )
                resp.raise_for_status()
                data = resp.json()
                org = data.get("organization", {})
                if not org:
                    return None
                return {
                    "name": org.get("name", ""),
                    "website": org.get("website_url", ""),
                    "industry": org.get("industry", ""),
                    "location": f"{org.get('city', '')}, {org.get('country', '')}".strip(", "),
                    "source": "apollo",
                }
        except Exception as e:
            logger.error(f"Apollo enrich_company failed: {e}")
            return None
