import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.connectors.apollo_connector import ApolloConnector
from backend.connectors.pdl_connector import PDLConnector
from backend.connectors.hunter_connector import HunterConnector

logger = logging.getLogger(__name__)


class EnrichmentAgent(BaseAgent):
    name = "enrichment"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        apollo = ApolloConnector()
        pdl = PDLConnector()
        hunter = HunterConnector()

        enriched: list[dict[str, Any]] = []
        enrichment_logs: list[dict[str, Any]] = []

        for prospect in input_data:
            logs: list[dict[str, Any]] = []

            apollo_data = await apollo.enrich_person(
                name=prospect.get("full_name", ""),
                company=prospect.get("company", ""),
                email=prospect.get("email", ""),
            )
            if apollo_data:
                fields_added = self._merge(prospect, apollo_data)
                logs.append({
                    "connector": "apollo",
                    "fields_added": fields_added,
                    "success": bool(fields_added),
                })

            pdl_data = await pdl.enrich_person(
                email=prospect.get("email", ""),
                linkedin_url=prospect.get("linkedin_url", ""),
            )
            if pdl_data:
                fields_added = self._merge(prospect, pdl_data)
                logs.append({
                    "connector": "pdl",
                    "fields_added": fields_added,
                    "success": bool(fields_added),
                })

            domain = self._extract_domain(prospect.get("company_website", ""))
            if domain:
                name_parts = prospect.get("full_name", "").split(" ", 1)
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                hunter_result = await hunter.email_finder(
                    domain=domain,
                    first_name=first_name,
                    last_name=last_name,
                )
                if hunter_result and hunter_result.get("email"):
                    fields_added = self._merge(prospect, {"email": hunter_result["email"]})
                    logs.append({
                        "connector": "hunter",
                        "fields_added": fields_added,
                        "success": True,
                    })

                    if prospect.get("email"):
                        verification = await hunter.email_verifier(email=prospect["email"])
                        if verification and verification.get("valid"):
                            prospect["email_verified"] = True

            prospect["enrichment_logs"] = logs
            enriched.append(prospect)

        logger.info(f"EnrichmentAgent enriched {len(enriched)} prospects")
        return enriched

    def _merge(self, prospect: dict[str, Any], new_data: dict[str, Any]) -> list[str]:
        fields_added = []
        merge_fields = [
            "full_name", "name", "job_title", "title", "company",
            "company_website", "location", "linkedin_url", "email",
        ]
        field_map = {"name": "full_name", "title": "job_title"}

        for field in merge_fields:
            target_field = field_map.get(field, field)
            new_value = new_data.get(field)
            if new_value and not prospect.get(target_field):
                prospect[target_field] = new_value
                fields_added.append(target_field)
        return fields_added

    def _extract_domain(self, url: str) -> str:
        if not url:
            return ""
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        return url.split("/")[0]
