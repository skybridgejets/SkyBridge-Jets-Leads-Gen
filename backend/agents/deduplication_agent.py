import logging
from typing import Any

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DeduplicationAgent(BaseAgent):
    name = "deduplication"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not input_data:
            return []

        deduplicated = self._deduplicate(input_data)
        logger.info(
            f"DeduplicationAgent: {len(input_data)} -> {len(deduplicated)} prospects "
            f"({len(input_data) - len(deduplicated)} duplicates removed)"
        )
        return deduplicated

    def _deduplicate(self, prospects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen_emails: dict[str, int] = {}
        seen_linkedin: dict[str, int] = {}
        seen_name_company: dict[str, int] = {}
        result: list[dict[str, Any]] = list(prospects)
        to_remove: set[int] = set()

        for i, p in enumerate(result):
            if i in to_remove:
                continue

            email = (p.get("email") or "").strip().lower()
            linkedin = (p.get("linkedin_url") or "").strip().lower()
            name = self._normalise_name(p.get("full_name") or "")
            company = (p.get("company") or "").strip().lower()
            name_company_key = f"{name}||{company}" if name and company else ""

            if email and email in seen_emails:
                existing_idx = seen_emails[email]
                loser = self._pick_loser(result[existing_idx], p, existing_idx, i)
                to_remove.add(loser)
                if loser == existing_idx:
                    seen_emails[email] = i
            elif email:
                seen_emails[email] = i

            if linkedin and linkedin in seen_linkedin:
                existing_idx = seen_linkedin[linkedin]
                if existing_idx not in to_remove and i not in to_remove:
                    loser = self._pick_loser(result[existing_idx], p, existing_idx, i)
                    to_remove.add(loser)
                    if loser == existing_idx:
                        seen_linkedin[linkedin] = i
            elif linkedin:
                seen_linkedin[linkedin] = i

            if name_company_key and name_company_key in seen_name_company:
                existing_idx = seen_name_company[name_company_key]
                if existing_idx not in to_remove and i not in to_remove:
                    existing_email = (result[existing_idx].get("email") or "").strip().lower()
                    if email and existing_email and email != existing_email:
                        pass
                    else:
                        loser = self._pick_loser(result[existing_idx], p, existing_idx, i)
                        to_remove.add(loser)
                        if loser == existing_idx:
                            seen_name_company[name_company_key] = i
            elif name_company_key:
                seen_name_company[name_company_key] = i

        return [p for i, p in enumerate(result) if i not in to_remove]

    def _pick_loser(self, a: dict[str, Any], b: dict[str, Any], idx_a: int, idx_b: int) -> int:
        count_a = self._field_count(a)
        count_b = self._field_count(b)
        if count_a >= count_b:
            return idx_b
        return idx_a

    def _field_count(self, prospect: dict[str, Any]) -> int:
        fields = [
            "full_name", "job_title", "company", "company_website",
            "location", "linkedin_url", "email", "source_url",
        ]
        return sum(1 for f in fields if prospect.get(f))

    def _normalise_name(self, name: str) -> str:
        return " ".join(name.strip().lower().split())
