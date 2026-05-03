import pytest
from backend.agents.deduplication_agent import DeduplicationAgent


def deduplicate(prospects: list[dict]) -> list[dict]:
    agent = DeduplicationAgent.__new__(DeduplicationAgent)
    return agent._deduplicate(prospects)


class TestDeduplicationAgent:
    def test_same_email_produces_one_record(self):
        prospects = [
            {
                "full_name": "John Smith",
                "email": "john@example.com",
                "job_title": "CEO",
                "company": "Acme",
                "company_website": "acme.com",
                "location": "London",
                "linkedin_url": "",
                "source_url": "",
            },
            {
                "full_name": "John Smith",
                "email": "john@example.com",
                "job_title": "CEO",
                "company": "Acme Inc",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 1
        # Record with more fields should win
        assert result[0]["company"] == "Acme"

    def test_same_linkedin_produces_one_record(self):
        prospects = [
            {
                "full_name": "Jane Doe",
                "email": "",
                "job_title": "PA",
                "company": "BigCo",
                "company_website": "",
                "location": "",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "source_url": "",
            },
            {
                "full_name": "Jane Doe",
                "email": "jane@bigco.com",
                "job_title": "Personal Assistant",
                "company": "BigCo",
                "company_website": "bigco.com",
                "location": "Dubai",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "source_url": "https://source.com",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 1
        # Record with more fields should win
        assert result[0]["email"] == "jane@bigco.com"

    def test_same_name_company_different_emails_both_kept(self):
        prospects = [
            {
                "full_name": "Alice Brown",
                "email": "alice@work.com",
                "job_title": "Estate Manager",
                "company": "Luxury Estates",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
            {
                "full_name": "Alice Brown",
                "email": "alice@personal.com",
                "job_title": "Estate Manager",
                "company": "Luxury Estates",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 2

    def test_record_with_more_fields_wins(self):
        prospects = [
            {
                "full_name": "Bob Wilson",
                "email": "bob@test.com",
                "job_title": "",
                "company": "",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
            {
                "full_name": "Bob Wilson",
                "email": "bob@test.com",
                "job_title": "Chief of Staff",
                "company": "Wilson Group",
                "company_website": "wilsongroup.com",
                "location": "London",
                "linkedin_url": "https://linkedin.com/in/bobwilson",
                "source_url": "https://source.com",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 1
        assert result[0]["job_title"] == "Chief of Staff"
        assert result[0]["company"] == "Wilson Group"

    def test_empty_list_returns_empty(self):
        result = deduplicate([])
        assert result == []

    def test_single_record_returns_same(self):
        prospects = [
            {
                "full_name": "Solo Person",
                "email": "solo@test.com",
                "job_title": "CEO",
                "company": "Solo Inc",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 1
        assert result[0]["full_name"] == "Solo Person"

    def test_three_duplicates_same_email_produces_one(self):
        prospects = [
            {
                "full_name": "Triple",
                "email": "triple@test.com",
                "job_title": "",
                "company": "",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
            {
                "full_name": "Triple Person",
                "email": "triple@test.com",
                "job_title": "CEO",
                "company": "TripleCo",
                "company_website": "",
                "location": "",
                "linkedin_url": "",
                "source_url": "",
            },
            {
                "full_name": "Triple Person",
                "email": "triple@test.com",
                "job_title": "CEO",
                "company": "TripleCo",
                "company_website": "triple.com",
                "location": "London",
                "linkedin_url": "https://linkedin.com/in/triple",
                "source_url": "https://source.com",
            },
        ]
        result = deduplicate(prospects)
        assert len(result) == 1
        assert result[0]["company_website"] == "triple.com"
