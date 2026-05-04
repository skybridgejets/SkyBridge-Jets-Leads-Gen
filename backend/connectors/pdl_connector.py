import os
import logging
from typing import Any

import httpx

from backend.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

PDL_BASE_URL = "https://api.peopledatalabs.com/v5"


class PDLConnector(BaseConnector):
    name = "pdl"

    def __init__(self):
        self.api_key = os.getenv("PDL_API_KEY")
        if not self.api_key:
            logger.warning("PDL_API_KEY not set — PDL connector will return empty results")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key or "",
        }

    async def search(self, **kwargs) -> list[dict[str, Any]]:
        result = await self.search_person(**kwargs)
        return [result] if result else []

    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        return await self.enrich_person(**kwargs)

    async def search_person(
        self,
        name: str = "",
        company: str = "",
        location: str = "",
        **kwargs,
    ) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                query_parts = []
                if name:
                    query_parts.append(f"name:{name}")
                if company:
                    query_parts.append(f"company:{company}")
                if location:
                    query_parts.append(f"location:{location}")

                params = {
                    "query": " AND ".join(query_parts),
                    "size": 1,
                }
                resp = await client.get(
                    f"{PDL_BASE_URL}/person/search",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("data", [])
                if not results:
                    return None
                p = results[0]
                return {
                    "name": p.get("full_name", ""),
                    "title": p.get("job_title", ""),
                    "company": p.get("job_company_name", ""),
                    "company_website": p.get("job_company_website", ""),
                    "email": p.get("work_email") or p.get("personal_emails", [None])[0] if p.get("personal_emails") else p.get("work_email", ""),
                    "linkedin_url": p.get("linkedin_url", ""),
                    "location": p.get("location_name", ""),
                    "source": "pdl",
                }
        except Exception as e:
            logger.error(f"PDL search_person failed: {e}")
            return None

    async def enrich_person(
        self,
        email: str = "",
        linkedin_url: str = "",
        **kwargs,
    ) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params: dict[str, str] = {}
                if email:
                    params["email"] = email
                if linkedin_url:
                    params["profile"] = linkedin_url

                if not params:
                    return None

                resp = await client.get(
                    f"{PDL_BASE_URL}/person/enrich",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") != 200:
                    return None
                return {
                    "name": data.get("full_name", ""),
                    "title": data.get("job_title", ""),
                    "company": data.get("job_company_name", ""),
                    "company_website": data.get("job_company_website", ""),
                    "email": data.get("work_email", ""),
                    "linkedin_url": data.get("linkedin_url", ""),
                    "location": data.get("location_name", ""),
                    "source": "pdl",
                }
        except Exception as e:
            logger.error(f"PDL enrich_person failed: {e}")
            return None
