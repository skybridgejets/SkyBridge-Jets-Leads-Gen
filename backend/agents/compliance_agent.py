import logging
from typing import Any

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseAgent):
    name = "compliance"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for prospect in input_data:
            compliance = self._assess_compliance(prospect)
            prospect["compliance"] = compliance
            results.append(prospect)

        logger.info(f"ComplianceAgent assessed {len(results)} prospects")
        return results

    def _assess_compliance(self, prospect: dict[str, Any]) -> dict[str, Any]:
        source_type = (prospect.get("source_type") or "unknown").lower()
        email = prospect.get("email") or ""
        email_verified = prospect.get("email_verified", False)
        flags: list[str] = []

        if source_type in ("api", "apollo", "pdl", "hunter"):
            mapped_source_type = "api"
        elif source_type in ("web_search", "google", "serpapi"):
            mapped_source_type = "public"
        elif source_type == "manual":
            mapped_source_type = "manual"
        else:
            mapped_source_type = "public"
            flags.append("source_type_undetermined")

        if email_verified and mapped_source_type == "api":
            confidence_level = "high"
        elif mapped_source_type == "api" and not email_verified:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        if not email:
            flags.append("no_email_found")
        if not prospect.get("full_name"):
            flags.append("missing_full_name")
        if mapped_source_type == "public" and email:
            flags.append("email_from_public_source_verify_lawful_basis")
        if source_type == "unknown":
            flags.append("source_undetermined")

        return {
            "data_source": prospect.get("source_type") or "unknown",
            "confidence_level": confidence_level,
            "email_verified": email_verified,
            "source_type": mapped_source_type,
            "flags": flags,
        }
