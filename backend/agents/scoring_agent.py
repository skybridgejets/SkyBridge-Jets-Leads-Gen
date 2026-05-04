import logging
from typing import Any

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

UHNW_LOCATIONS = {"london", "dubai", "monaco", "geneva", "riyadh", "new york"}

UHNW_INDUSTRIES = {"yacht", "luxury travel", "luxury real estate"}

UHNW_KEYWORDS = [
    "uhnw", "ultra high net worth", "high net worth", "hnw",
    "private wealth", "wealth management", "family office",
    "private client", "billionaire", "millionaire",
]

WEAK_SIGNALS = [
    "intern", "junior", "trainee", "volunteer", "student",
    "freelance", "part-time", "contractor",
]


class ScoringAgent(BaseAgent):
    name = "scoring"

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []

        for prospect in input_data:
            score, breakdown = self._score_prospect(prospect)
            prospect["lead_score"] = score
            prospect["score_breakdown"] = breakdown
            scored.append(prospect)

        scored.sort(key=lambda p: p.get("lead_score", 0), reverse=True)
        logger.info(f"ScoringAgent scored {len(scored)} prospects")
        return scored

    def _score_prospect(self, prospect: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        title = (prospect.get("job_title") or "").lower()
        location = (prospect.get("location") or "").lower()
        email = prospect.get("email") or ""
        email_verified = prospect.get("email_verified", False)
        raw_data = prospect.get("raw_data") or {}
        notes = (raw_data.get("relevance_reason") or raw_data.get("raw_snippet") or "").lower()

        score = 0
        breakdown: dict[str, Any] = {}

        if "family office" in title:
            breakdown["title_family_office"] = 40
            score += 40
        elif "chief of staff" in title or "estate manager" in title:
            breakdown["title_chief_estate"] = 35
            score += 35
        elif self._matches_any(title, ["personal assistant", " pa ", "executive assistant", " ea "]) or title.startswith("pa ") or title.endswith(" pa") or title == "pa" or title.startswith("ea ") or title.endswith(" ea") or title == "ea":
            breakdown["title_pa_ea"] = 30
            score += 30
        elif "luxury concierge" in title or "lifestyle manager" in title:
            breakdown["title_concierge_lifestyle"] = 30
            score += 30
        elif "founder" in title or "ceo" in title:
            breakdown["title_founder_ceo"] = 25
            score += 25

        all_text = f"{title} {notes}"
        if any(kw in all_text for kw in UHNW_KEYWORDS):
            breakdown["uhnw_relevance"] = 25
            score += 25

        industry_text = f"{title} {(prospect.get('company') or '').lower()} {notes}"
        if any(ind in industry_text for ind in UHNW_INDUSTRIES):
            breakdown["industry_match"] = 20
            score += 20

        if any(loc in location for loc in UHNW_LOCATIONS):
            breakdown["location_match"] = 20
            score += 20

        if email and email_verified:
            breakdown["verified_email"] = 15
            score += 15

        if any(sig in title for sig in WEAK_SIGNALS):
            breakdown["weak_relevance"] = -20
            score -= 20

        if not breakdown or (len(breakdown) == 1 and "weak_relevance" in breakdown):
            if not any(k in breakdown for k in [
                "title_family_office", "title_chief_estate", "title_pa_ea",
                "title_concierge_lifestyle", "title_founder_ceo",
                "uhnw_relevance", "industry_match",
            ]):
                breakdown["no_role_fit"] = -30
                score -= 30

        score = max(0, min(100, score))
        breakdown["total"] = score
        return score, breakdown

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        return any(p in text for p in patterns)
