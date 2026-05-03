import os
import logging
from typing import Any

import httpx

from backend.connectors.base_connector import BaseConnector

logger = logging.getLogger(__name__)

HUNTER_BASE_URL = "https://api.hunter.io/v2"


class HunterConnector(BaseConnector):
    name = "hunter"

    def __init__(self):
        self.api_key = os.getenv("HUNTER_API_KEY")
        if not self.api_key:
            logger.warning("HUNTER_API_KEY not set — Hunter connector will return empty results")

    async def search(self, **kwargs) -> list[dict[str, Any]]:
        return await self.domain_search(**kwargs)

    async def enrich(self, **kwargs) -> dict[str, Any] | None:
        result = await self.email_finder(**kwargs)
        return result

    async def domain_search(self, domain: str = "", **kwargs) -> list[dict[str, Any]]:
        if not self.api_key or not domain:
            return []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{HUNTER_BASE_URL}/domain-search",
                    params={"domain": domain, "api_key": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                emails = data.get("data", {}).get("emails", [])
                return [
                    {
                        "email": e.get("value", ""),
                        "first_name": e.get("first_name", ""),
                        "last_name": e.get("last_name", ""),
                        "position": e.get("position", ""),
                        "confidence": e.get("confidence", 0),
                        "source": "hunter",
                    }
                    for e in emails
                ]
        except Exception as e:
            logger.error(f"Hunter domain_search failed: {e}")
            return []

    async def email_finder(
        self,
        domain: str = "",
        first_name: str = "",
        last_name: str = "",
        **kwargs,
    ) -> dict[str, Any] | None:
        if not self.api_key or not domain:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params: dict[str, str] = {
                    "domain": domain,
                    "api_key": self.api_key,
                }
                if first_name:
                    params["first_name"] = first_name
                if last_name:
                    params["last_name"] = last_name

                resp = await client.get(
                    f"{HUNTER_BASE_URL}/email-finder",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                if not data or not data.get("email"):
                    return None
                return {
                    "email": data.get("email", ""),
                    "confidence": data.get("confidence", 0),
                    "source": "hunter",
                }
        except Exception as e:
            logger.error(f"Hunter email_finder failed: {e}")
            return None

    async def email_verifier(self, email: str = "", **kwargs) -> dict[str, Any] | None:
        if not self.api_key or not email:
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{HUNTER_BASE_URL}/email-verifier",
                    params={"email": email, "api_key": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                return {
                    "email": email,
                    "valid": data.get("result") == "deliverable",
                    "confidence": data.get("score", 0),
                    "source": "hunter",
                }
        except Exception as e:
            logger.error(f"Hunter email_verifier failed: {e}")
            return None
