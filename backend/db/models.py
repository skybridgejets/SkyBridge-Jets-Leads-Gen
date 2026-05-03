import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Search(Base):
    __tablename__ = "searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    location = Column(Text)
    persona = Column(Text)
    industry = Column(Text)
    prospect_count = Column(Integer, default=20)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id"), nullable=False)
    agent_name = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    output_summary = Column(Text)
    error_message = Column(Text)


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    website = Column(Text)
    industry = Column(Text)
    location = Column(Text)
    source_url = Column(Text)
    source_type = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    full_name = Column(Text)
    job_title = Column(Text)
    company = Column(Text)
    company_website = Column(Text)
    location = Column(Text)
    linkedin_url = Column(Text)
    email = Column(Text)
    email_verified = Column(Boolean, default=False)
    source_url = Column(Text)
    source_type = Column(Text)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class EnrichmentLog(Base):
    __tablename__ = "enrichment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False)
    connector = Column(Text, nullable=False)
    fields_added = Column(ARRAY(String))
    success = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False)
    total_score = Column(Integer, nullable=False)
    score_breakdown = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False)
    linkedin_connection = Column(Text)
    linkedin_followup = Column(Text)
    email_subject = Column(Text)
    email_body = Column(Text)
    whatsapp_message = Column(Text)
    personalisation_note = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"), nullable=False)
    data_source = Column(Text)
    confidence_level = Column(String(10))
    email_verified = Column(Boolean, default=False)
    source_type = Column(String(10))
    flags = Column(ARRAY(String))
