"""
Models — SQLAlchemy ORM models for local persistence.

Used for local development with SQLite. In production, Firestore
handles persistence and this module serves as a schema reference.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class AuditRecord(Base):
    """Stores completed audit metadata and results."""

    __tablename__ = "audit_records"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, nullable=False)
    sensitive_attrs = Column(JSON, nullable=False)
    target_column = Column(String, nullable=False)
    fairness_score = Column(Integer)
    risk_level = Column(String)
    status = Column(String, default="queued")
    result_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ReportRecord(Base):
    """Stores generated AI reports."""

    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    audit_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    generated_by = Column(String, default="gemini")
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(database_url: str = "sqlite:///./fairsight.db"):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str = "sqlite:///./fairsight.db"):
    engine = get_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
