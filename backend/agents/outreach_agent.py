import os
import logging
import json
from typing import Any

from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a copywriter for SkyBridge Jets, a UK-based private jet brokerage.
You write professional outreach messages to potential referral partners and UHNW contacts.

Tone rules (strict):
- Private aviation broker register. Professional and human. Not salesy.
- No hype. No superlatives. No desperation.
- No em dashes. No exclamation marks. No filler phrases like "I hope this finds you well".
- Keep it brief and direct.
- SkyBridge Jets arranges private jet charter for UHNW clients across the UK, Europe, and Middle East.

You must generate exactly 4 message variants plus a personalisation note.
Return valid JSON with these keys:
- linkedin_connection: under 300 characters, no hashtags, no exclamation marks
- linkedin_followup: 3-4 sentences assuming connection was accepted
- email_subject: concise email subject line
- email_body: 4-5 sentences with one clear call to action
- whatsapp_message: brief, conversational, no formal structure
- personalisation_note: 2-3 sentences explaining why SkyBridge Jets should contact this person
"""


class OutreachAgent(BaseAgent):
    name = "outreach"

    def __init__(self, db, search_id):
        super().__init__(db, search_id)
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for prospect in input_data:
            messages = await self._generate_outreach(prospect)
            prospect["outreach"] = messages
            results.append(prospect)

        logger.info(f"OutreachAgent generated messages for {len(results)} prospects")
        return results

    async def _generate_outreach(self, prospect: dict[str, Any]) -> dict[str, str]:
        if not self.client:
            return self._fallback_messages(prospect)

        try:
            user_prompt = (
                f"Generate outreach messages for this prospect:\n"
                f"Name: {prospect.get('full_name', 'Unknown')}\n"
                f"Title: {prospect.get('job_title', 'Unknown')}\n"
                f"Company: {prospect.get('company', 'Unknown')}\n"
                f"Location: {prospect.get('location', 'Unknown')}\n"
                f"Score: {prospect.get('lead_score', 0)}/100\n"
                f"Score breakdown: {json.dumps(prospect.get('score_breakdown', {}))}\n"
            )

            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as e:
            logger.error(f"Outreach generation failed for {prospect.get('full_name')}: {e}")
            return self._fallback_messages(prospect)

    def _fallback_messages(self, prospect: dict[str, Any]) -> dict[str, str]:
        name = prospect.get("full_name", "there")
        title = prospect.get("job_title", "")
        company = prospect.get("company", "")

        return {
            "linkedin_connection": (
                f"Hi {name}, I work with SkyBridge Jets arranging private aviation for UHNW clients. "
                f"Given your role{' at ' + company if company else ''}, thought it worth connecting."
            )[:300],
            "linkedin_followup": (
                f"Thanks for connecting, {name}. SkyBridge Jets is a UK-based private jet brokerage "
                f"working with UHNW clients and their advisors. "
                f"We often work with professionals in similar roles to yours and wanted to explore "
                f"whether there might be a fit for referral introductions. Happy to share more if useful."
            ),
            "email_subject": f"SkyBridge Jets — private aviation for your clients",
            "email_body": (
                f"Hi {name},\n\n"
                f"I am reaching out from SkyBridge Jets, a UK-based private jet brokerage. "
                f"We arrange charter flights for UHNW individuals and their representatives.\n\n"
                f"Given your role as {title}{' at ' + company if company else ''}, I thought there "
                f"might be a natural overlap. Many of our clients rely on trusted advisors like "
                f"yourself when arranging travel.\n\n"
                f"Would you be open to a brief call this week to explore whether a referral "
                f"partnership could work?\n\n"
                f"Best regards,\nSkyBridge Jets"
            ),
            "whatsapp_message": (
                f"Hi {name}, this is from SkyBridge Jets. We do private jet charter for UHNW clients. "
                f"Thought your role might overlap with what we do. Worth a quick chat?"
            ),
            "personalisation_note": (
                f"{name} holds the role of {title}{' at ' + company if company else ''}, "
                f"which suggests direct or indirect involvement in travel arrangements for "
                f"high-net-worth individuals. This makes them a strong potential referral partner "
                f"for SkyBridge Jets."
            ),
        }
