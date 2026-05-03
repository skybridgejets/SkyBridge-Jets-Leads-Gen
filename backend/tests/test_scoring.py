import pytest
from backend.agents.scoring_agent import ScoringAgent


class FakeDB:
    def add(self, obj): pass
    async def flush(self): pass
    async def execute(self, stmt): pass


def score_prospect(prospect: dict) -> tuple[int, dict]:
    agent = ScoringAgent.__new__(ScoringAgent)
    return agent._score_prospect(prospect)


class TestScoringAgent:
    def test_chief_of_staff_dubai_verified_email_scores_70_plus(self):
        prospect = {
            "job_title": "Chief of Staff",
            "location": "Dubai, UAE",
            "email": "chief@example.com",
            "email_verified": True,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert score >= 70, f"Expected >= 70 but got {score}. Breakdown: {breakdown}"
        assert "title_chief_estate" in breakdown
        assert "location_match" in breakdown
        assert "verified_email" in breakdown

    def test_family_office_london_uhnw_scores_80_plus(self):
        prospect = {
            "job_title": "Family Office Director",
            "location": "London, UK",
            "email": "fo@example.com",
            "email_verified": False,
            "raw_data": {"relevance_reason": "UHNW wealth management"},
        }
        score, breakdown = score_prospect(prospect)
        assert score >= 80, f"Expected >= 80 but got {score}. Breakdown: {breakdown}"
        assert "title_family_office" in breakdown
        assert "uhnw_relevance" in breakdown

    def test_unknown_title_unknown_location_no_email_scores_20_or_below(self):
        prospect = {
            "job_title": "Unknown Role",
            "location": "Unknown",
            "email": "",
            "email_verified": False,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert score <= 20, f"Expected <= 20 but got {score}. Breakdown: {breakdown}"

    def test_score_never_exceeds_100(self):
        prospect = {
            "job_title": "Family Office Chief of Staff Lifestyle Manager",
            "location": "Dubai, Monaco, London",
            "email": "test@example.com",
            "email_verified": True,
            "raw_data": {"relevance_reason": "UHNW luxury yacht travel real estate"},
        }
        score, breakdown = score_prospect(prospect)
        assert score <= 100, f"Score should not exceed 100 but got {score}"

    def test_score_never_goes_below_0(self):
        prospect = {
            "job_title": "intern junior trainee",
            "location": "Nowhere",
            "email": "",
            "email_verified": False,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert score >= 0, f"Score should not go below 0 but got {score}"

    def test_breakdown_contains_correct_keys_and_points(self):
        prospect = {
            "job_title": "Estate Manager",
            "location": "Geneva",
            "email": "em@example.com",
            "email_verified": True,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert "title_chief_estate" in breakdown
        assert breakdown["title_chief_estate"] == 35
        assert "location_match" in breakdown
        assert breakdown["location_match"] == 20
        assert "verified_email" in breakdown
        assert breakdown["verified_email"] == 15
        assert "total" in breakdown
        assert breakdown["total"] == score

    def test_pa_title_scoring(self):
        prospect = {
            "job_title": "PA to CEO",
            "location": "London",
            "email": "",
            "email_verified": False,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert "title_pa_ea" in breakdown
        assert breakdown["title_pa_ea"] == 30

    def test_luxury_concierge_scoring(self):
        prospect = {
            "job_title": "Luxury Concierge Manager",
            "location": "Monaco",
            "email": "concierge@example.com",
            "email_verified": False,
            "raw_data": {},
        }
        score, breakdown = score_prospect(prospect)
        assert "title_concierge_lifestyle" in breakdown

    def test_founder_scoring(self):
        prospect = {
            "job_title": "Founder and CEO",
            "location": "New York",
            "email": "founder@example.com",
            "email_verified": True,
            "raw_data": {"relevance_reason": "luxury yacht company"},
        }
        score, breakdown = score_prospect(prospect)
        assert "title_founder_ceo" in breakdown
        assert "location_match" in breakdown
