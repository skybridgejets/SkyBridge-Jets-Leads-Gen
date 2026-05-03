import uuid
import csv
import io
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db, init_db, async_session
from backend.db.models import (
    Search, AgentRun, Prospect, LeadScore, OutreachMessage,
    ComplianceFlag, EnrichmentLog,
)
from backend.orchestrator.pipeline import run_pipeline
from backend.connectors.manual_connector import ManualConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="SkyBridge Jets Lead Generation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class SearchCreate(BaseModel):
    query: str
    location: Optional[str] = None
    persona: Optional[str] = None
    industry: Optional[str] = None
    prospect_count: int = 20


class ManualResearchRequest(BaseModel):
    name_or_url: str


# --- Background task runner ---

async def _run_pipeline_bg(search_id: uuid.UUID):
    async with async_session() as db:
        try:
            await run_pipeline(search_id, db)
        except Exception as e:
            logger.error(f"Pipeline failed for search {search_id}: {e}")
            from sqlalchemy import update
            await db.execute(
                update(Search).where(Search.id == search_id).values(status="failed")
            )
            await db.commit()


# --- Endpoints ---

@app.post("/api/searches")
async def create_search(body: SearchCreate, db: AsyncSession = Depends(get_db)):
    search = Search(
        query=body.query,
        location=body.location,
        persona=body.persona,
        industry=body.industry,
        prospect_count=body.prospect_count,
        status="pending",
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    asyncio.create_task(_run_pipeline_bg(search.id))

    return {
        "id": str(search.id),
        "status": search.status,
        "query": search.query,
        "created_at": search.created_at.isoformat() if search.created_at else None,
    }


@app.get("/api/searches")
async def list_searches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Search).order_by(Search.created_at.desc()))
    searches = result.scalars().all()
    response = []
    for s in searches:
        prospect_count_result = await db.execute(
            select(func.count(Prospect.id)).where(Prospect.search_id == s.id)
        )
        actual = prospect_count_result.scalar() or 0
        response.append({
            "id": str(s.id),
            "query": s.query,
            "location": s.location,
            "persona": s.persona,
            "industry": s.industry,
            "prospect_count": s.prospect_count,
            "actual_prospects": actual,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return response


@app.get("/api/searches/{search_id}")
async def get_search(search_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    prospect_count_result = await db.execute(
        select(func.count(Prospect.id)).where(Prospect.search_id == search_id)
    )
    prospect_count = prospect_count_result.scalar() or 0

    return {
        "id": str(search.id),
        "query": search.query,
        "location": search.location,
        "persona": search.persona,
        "industry": search.industry,
        "prospect_count": search.prospect_count,
        "actual_prospects": prospect_count,
        "status": search.status,
        "created_at": search.created_at.isoformat() if search.created_at else None,
    }


@app.get("/api/searches/{search_id}/runs")
async def get_search_runs(search_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.search_id == search_id)
        .order_by(AgentRun.started_at)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(run.id),
            "agent_name": run.agent_name,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "output_summary": run.output_summary,
            "error_message": run.error_message,
        }
        for run in runs
    ]


@app.get("/api/prospects")
async def list_prospects(
    search_id: Optional[uuid.UUID] = None,
    score_min: Optional[int] = None,
    location: Optional[str] = None,
    persona: Optional[str] = None,
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Prospect)

    if search_id:
        query = query.where(Prospect.search_id == search_id)
    if location:
        query = query.where(Prospect.location.ilike(f"%{location}%"))
    if persona:
        query = query.where(Prospect.job_title.ilike(f"%{persona}%"))
    if source:
        query = query.where(Prospect.source_type == source)

    result = await db.execute(query)
    prospects = result.scalars().all()

    response = []
    for p in prospects:
        score_result = await db.execute(
            select(LeadScore).where(LeadScore.prospect_id == p.id)
        )
        score = score_result.scalar_one_or_none()

        if score_min is not None and (not score or score.total_score < score_min):
            continue

        response.append({
            "id": str(p.id),
            "full_name": p.full_name,
            "job_title": p.job_title,
            "company": p.company,
            "location": p.location,
            "email": p.email,
            "email_verified": p.email_verified,
            "linkedin_url": p.linkedin_url,
            "source_type": p.source_type,
            "score": score.total_score if score else None,
            "search_id": str(p.search_id),
        })

    response.sort(key=lambda x: x.get("score") or 0, reverse=True)
    return response


@app.get("/api/prospects/{prospect_id}")
async def get_prospect(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    score_result = await db.execute(
        select(LeadScore).where(LeadScore.prospect_id == prospect_id)
    )
    score = score_result.scalar_one_or_none()

    outreach_result = await db.execute(
        select(OutreachMessage).where(OutreachMessage.prospect_id == prospect_id)
    )
    outreach = outreach_result.scalar_one_or_none()

    compliance_result = await db.execute(
        select(ComplianceFlag).where(ComplianceFlag.prospect_id == prospect_id)
    )
    compliance = compliance_result.scalar_one_or_none()

    enrichment_result = await db.execute(
        select(EnrichmentLog).where(EnrichmentLog.prospect_id == prospect_id)
    )
    enrichment_logs = enrichment_result.scalars().all()

    return {
        "id": str(prospect.id),
        "full_name": prospect.full_name,
        "job_title": prospect.job_title,
        "company": prospect.company,
        "company_website": prospect.company_website,
        "location": prospect.location,
        "linkedin_url": prospect.linkedin_url,
        "email": prospect.email,
        "email_verified": prospect.email_verified,
        "source_url": prospect.source_url,
        "source_type": prospect.source_type,
        "raw_data": prospect.raw_data,
        "search_id": str(prospect.search_id),
        "score": {
            "total": score.total_score,
            "breakdown": score.score_breakdown,
        } if score else None,
        "outreach": {
            "linkedin_connection": outreach.linkedin_connection,
            "linkedin_followup": outreach.linkedin_followup,
            "email_subject": outreach.email_subject,
            "email_body": outreach.email_body,
            "whatsapp_message": outreach.whatsapp_message,
            "personalisation_note": outreach.personalisation_note,
        } if outreach else None,
        "compliance": {
            "data_source": compliance.data_source,
            "confidence_level": compliance.confidence_level,
            "email_verified": compliance.email_verified,
            "source_type": compliance.source_type,
            "flags": compliance.flags,
        } if compliance else None,
        "enrichment_logs": [
            {
                "connector": log.connector,
                "fields_added": log.fields_added,
                "success": log.success,
            }
            for log in enrichment_logs
        ],
    }


@app.get("/api/outreach/{prospect_id}")
async def get_outreach(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OutreachMessage).where(OutreachMessage.prospect_id == prospect_id)
    )
    outreach = result.scalar_one_or_none()
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach messages not found")

    return {
        "prospect_id": str(prospect_id),
        "linkedin_connection": outreach.linkedin_connection,
        "linkedin_followup": outreach.linkedin_followup,
        "email_subject": outreach.email_subject,
        "email_body": outreach.email_body,
        "whatsapp_message": outreach.whatsapp_message,
        "personalisation_note": outreach.personalisation_note,
    }


@app.get("/api/export/{search_id}")
async def export_csv(search_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prospect).where(Prospect.search_id == search_id)
    )
    prospects = result.scalars().all()

    if not prospects:
        raise HTTPException(status_code=404, detail="No prospects found for this search")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Name", "Title", "Company", "Location", "Email", "Email Verified",
        "LinkedIn URL", "Score", "Score Breakdown", "Personalisation Note",
        "LinkedIn Connection", "LinkedIn Followup", "Email Subject", "Email Body",
        "WhatsApp Message", "Confidence Level", "Source Type", "Compliance Flags",
    ])

    for prospect in prospects:
        score_result = await db.execute(
            select(LeadScore).where(LeadScore.prospect_id == prospect.id)
        )
        score = score_result.scalar_one_or_none()

        outreach_result = await db.execute(
            select(OutreachMessage).where(OutreachMessage.prospect_id == prospect.id)
        )
        outreach = outreach_result.scalar_one_or_none()

        compliance_result = await db.execute(
            select(ComplianceFlag).where(ComplianceFlag.prospect_id == prospect.id)
        )
        compliance = compliance_result.scalar_one_or_none()

        import json
        writer.writerow([
            prospect.full_name,
            prospect.job_title,
            prospect.company,
            prospect.location,
            prospect.email,
            prospect.email_verified,
            prospect.linkedin_url,
            score.total_score if score else "",
            json.dumps(score.score_breakdown) if score else "",
            outreach.personalisation_note if outreach else "",
            outreach.linkedin_connection if outreach else "",
            outreach.linkedin_followup if outreach else "",
            outreach.email_subject if outreach else "",
            outreach.email_body if outreach else "",
            outreach.whatsapp_message if outreach else "",
            compliance.confidence_level if compliance else "",
            compliance.source_type if compliance else "",
            ", ".join(compliance.flags) if compliance and compliance.flags else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=skybridge_prospects_{search_id}.csv"},
    )


@app.post("/api/manual")
async def manual_research(body: ManualResearchRequest, db: AsyncSession = Depends(get_db)):
    connector = ManualConnector()
    result = await connector.research_company(name_or_url=body.name_or_url)

    if not result:
        raise HTTPException(status_code=404, detail="No data found for the given input")

    return result


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SkyBridge Jets Lead Generation API"}
