import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import (
    Search, Prospect, Company, EnrichmentLog, LeadScore,
    OutreachMessage, ComplianceFlag,
)
from backend.agents.source_finder_agent import SourceFinderAgent
from backend.agents.prospect_discovery_agent import ProspectDiscoveryAgent
from backend.agents.data_extraction_agent import DataExtractionAgent
from backend.agents.enrichment_agent import EnrichmentAgent
from backend.agents.deduplication_agent import DeduplicationAgent
from backend.agents.scoring_agent import ScoringAgent
from backend.agents.outreach_agent import OutreachAgent
from backend.agents.compliance_agent import ComplianceAgent

logger = logging.getLogger(__name__)


async def run_pipeline(search_id: uuid.UUID, db: AsyncSession):
    logger.info(f"Starting pipeline for search {search_id}")

    await db.execute(
        update(Search).where(Search.id == search_id).values(status="running")
    )
    await db.commit()

    from sqlalchemy import select
    result = await db.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one()

    search_params = {
        "location": search.location or "",
        "persona": search.persona or "",
        "industry": search.industry or "",
        "prospect_count": search.prospect_count or 20,
        "query": search.query or "",
    }

    pipeline_data = None

    # Agent 1: Source Finder
    try:
        agent = SourceFinderAgent(db, search_id)
        pipeline_data = await agent.run(search_params)
        await db.commit()
    except Exception as e:
        logger.error(f"Source Finder failed: {e}")
        await db.commit()
        pipeline_data = []

    # Agent 2: Prospect Discovery
    try:
        agent = ProspectDiscoveryAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Prospect Discovery failed: {e}")
        await db.commit()
        if not pipeline_data:
            pipeline_data = []

    # Agent 3: Data Extraction
    try:
        agent = DataExtractionAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Data Extraction failed: {e}")
        await db.commit()

    # Agent 4: Enrichment
    try:
        agent = EnrichmentAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        await db.commit()

    # Agent 5: Deduplication
    try:
        agent = DeduplicationAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Deduplication failed: {e}")
        await db.commit()

    # Agent 6: Scoring
    try:
        agent = ScoringAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        await db.commit()

    # Agent 7: Outreach
    try:
        agent = OutreachAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Outreach failed: {e}")
        await db.commit()

    # Agent 8: Compliance
    try:
        agent = ComplianceAgent(db, search_id)
        pipeline_data = await agent.run(pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Compliance failed: {e}")
        await db.commit()

    # Persist results to database
    try:
        await _persist_results(db, search_id, pipeline_data or [])
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to persist results for search {search_id}: {e}")
        await db.rollback()
        # Retry with individual inserts to save what we can
        try:
            await _persist_results_safe(db, search_id, pipeline_data or [])
            await db.commit()
        except Exception as e2:
            logger.error(f"Safe persist also failed for search {search_id}: {e2}")
            await db.rollback()

    await db.execute(
        update(Search).where(Search.id == search_id).values(status="complete")
    )
    await db.commit()
    logger.info(f"Pipeline complete for search {search_id}: {len(pipeline_data or [])} prospects")


async def _persist_results(
    db: AsyncSession,
    search_id: uuid.UUID,
    prospects: list[dict],
):
    for p_data in prospects:
        company_id = None
        if p_data.get("company"):
            company = Company(
                name=p_data.get("company", ""),
                website=p_data.get("company_website", ""),
                location=p_data.get("location", ""),
                source_url=p_data.get("source_url", ""),
                source_type=p_data.get("source_type", ""),
            )
            db.add(company)
            await db.flush()
            company_id = company.id

        prospect = Prospect(
            search_id=search_id,
            company_id=company_id,
            full_name=p_data.get("full_name", ""),
            job_title=p_data.get("job_title", ""),
            company=p_data.get("company", ""),
            company_website=p_data.get("company_website", ""),
            location=p_data.get("location", ""),
            linkedin_url=p_data.get("linkedin_url", ""),
            email=p_data.get("email", ""),
            email_verified=p_data.get("email_verified", False),
            source_url=p_data.get("source_url", ""),
            source_type=p_data.get("source_type", ""),
            raw_data=p_data.get("raw_data"),
        )
        db.add(prospect)
        await db.flush()

        # Save enrichment logs
        for log in p_data.get("enrichment_logs", []):
            enrichment_log = EnrichmentLog(
                prospect_id=prospect.id,
                connector=log.get("connector", ""),
                fields_added=log.get("fields_added", []),
                success=log.get("success", False),
            )
            db.add(enrichment_log)

        # Save lead score
        if "lead_score" in p_data:
            lead_score = LeadScore(
                prospect_id=prospect.id,
                total_score=p_data["lead_score"],
                score_breakdown=p_data.get("score_breakdown", {}),
            )
            db.add(lead_score)

        # Save outreach messages
        outreach = p_data.get("outreach", {})
        if outreach:
            outreach_msg = OutreachMessage(
                prospect_id=prospect.id,
                linkedin_connection=outreach.get("linkedin_connection", ""),
                linkedin_followup=outreach.get("linkedin_followup", ""),
                email_subject=outreach.get("email_subject", ""),
                email_body=outreach.get("email_body", ""),
                whatsapp_message=outreach.get("whatsapp_message", ""),
                personalisation_note=outreach.get("personalisation_note", ""),
            )
            db.add(outreach_msg)

        # Save compliance flags
        compliance = p_data.get("compliance", {})
        if compliance:
            comp_flag = ComplianceFlag(
                prospect_id=prospect.id,
                data_source=compliance.get("data_source", ""),
                confidence_level=compliance.get("confidence_level", "low"),
                email_verified=compliance.get("email_verified", False),
                source_type=compliance.get("source_type", "public"),
                flags=compliance.get("flags", []),
            )
            db.add(comp_flag)

    await db.flush()


async def _persist_results_safe(
    db: AsyncSession,
    search_id: uuid.UUID,
    prospects: list[dict],
):
    saved = 0
    for p_data in prospects:
        try:
            company_id = None
            if p_data.get("company"):
                company = Company(
                    name=p_data.get("company", ""),
                    website=p_data.get("company_website", ""),
                    location=p_data.get("location", ""),
                    source_url=p_data.get("source_url", ""),
                    source_type=p_data.get("source_type", ""),
                )
                db.add(company)
                await db.flush()
                company_id = company.id

            prospect = Prospect(
                search_id=search_id,
                company_id=company_id,
                full_name=p_data.get("full_name", ""),
                job_title=p_data.get("job_title", ""),
                company=p_data.get("company", ""),
                company_website=p_data.get("company_website", ""),
                location=p_data.get("location", ""),
                linkedin_url=p_data.get("linkedin_url", ""),
                email=p_data.get("email", ""),
                email_verified=p_data.get("email_verified", False),
                source_url=p_data.get("source_url", ""),
                source_type=p_data.get("source_type", ""),
                raw_data=p_data.get("raw_data"),
            )
            db.add(prospect)
            await db.flush()

            if "lead_score" in p_data:
                lead_score = LeadScore(
                    prospect_id=prospect.id,
                    total_score=p_data["lead_score"],
                    score_breakdown=p_data.get("score_breakdown", {}),
                )
                db.add(lead_score)

            outreach = p_data.get("outreach", {})
            if outreach:
                outreach_msg = OutreachMessage(
                    prospect_id=prospect.id,
                    linkedin_connection=outreach.get("linkedin_connection", ""),
                    linkedin_followup=outreach.get("linkedin_followup", ""),
                    email_subject=outreach.get("email_subject", ""),
                    email_body=outreach.get("email_body", ""),
                    whatsapp_message=outreach.get("whatsapp_message", ""),
                    personalisation_note=outreach.get("personalisation_note", ""),
                )
                db.add(outreach_msg)

            compliance = p_data.get("compliance", {})
            if compliance:
                comp_flag = ComplianceFlag(
                    prospect_id=prospect.id,
                    data_source=compliance.get("data_source", ""),
                    confidence_level=compliance.get("confidence_level", "low")[:10],
                    email_verified=compliance.get("email_verified", False),
                    source_type=compliance.get("source_type", "public")[:10],
                    flags=compliance.get("flags", []),
                )
                db.add(comp_flag)

            await db.flush()
            saved += 1
        except Exception as e:
            logger.error(f"Failed to save prospect {p_data.get('full_name', '?')}: {e}")
            await db.rollback()

    logger.info(f"Safe persist saved {saved}/{len(prospects)} prospects")
