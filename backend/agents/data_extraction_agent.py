import logging
import re
from typing import Any

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DataExtractionAgent(BaseAgent):
    name = "data_extraction"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalised: list[dict[str, Any]] = []

        for raw in input_data:
            prospect = self._normalise(raw)
            if prospect.get("full_name") or prospect.get("company"):
                normalised.append(prospect)

        logger.info(f"DataExtractionAgent normalised {len(normalised)} prospects")
        return normalised

    def _normalise(self, raw: dict[str, Any]) -> dict[str, Any]:
        full_name = self._clean(raw.get("name") or raw.get("full_name") or "")
        job_title = self._clean(raw.get("title") or raw.get("job_title") or "")
        company = self._clean(raw.get("company") or raw.get("company_name") or "")
        company_website = self._clean_url(raw.get("company_website") or raw.get("website") or "")
        location = self._clean(raw.get("location") or "")
        linkedin_url = self._clean_url(raw.get("linkedin_url") or "")
        email = self._clean_email(raw.get("email") or "")
        source_url = self._clean_url(raw.get("source_url") or "")
        source_type = raw.get("source") or raw.get("source_type") or "unknown"

        missing_fields = []
        if not full_name:
            missing_fields.append("full_name")
        if not job_title:
            missing_fields.append("job_title")
        if not email:
            missing_fields.append("email")

        return {
            "full_name": full_name,
            "job_title": job_title,
            "company": company,
            "company_website": company_website,
            "location": location,
            "linkedin_url": linkedin_url,
            "email": email,
            "email_verified": False,
            "source_url": source_url,
            "source_type": source_type,
            "raw_data": raw,
            "missing_fields": missing_fields,
        }

    def _clean(self, value: str) -> str:
        return " ".join(value.strip().split())

    def _clean_url(self, value: str) -> str:
        value = value.strip()
        if value and not value.startswith("http"):
            value = "https://" + value
        return value if value and value != "https://" else ""

    def _clean_email(self, value: str) -> str:
        value = value.strip().lower()
        if value and re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            return value
        return ""
