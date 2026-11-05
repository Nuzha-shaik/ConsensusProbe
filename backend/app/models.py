"""SQLAlchemy models and database setup for ConsensusProbe backend."""
from __future__ import annotations
import datetime
import os
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./consensusprobe.db")

# For SQLite, enable check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    path = Column(String(512), nullable=False)
    rows = Column(Integer, nullable=False)
    cols = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    plans = relationship("CandidatePlan", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("OperationRun", back_populates="dataset", cascade="all, delete-orphan")
    clarifications = relationship("Clarification", back_populates="dataset", cascade="all, delete-orphan")

class CandidatePlan(Base):
    __tablename__ = "candidate_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    plan_index = Column(Integer, nullable=False)
    plan_json = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)

    dataset = relationship("Dataset", back_populates="plans")

class OperationRun(Base):
    __tablename__ = "operation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    status = Column(String(50), nullable=False)  # applied, pending_clarification
    applied_patch = Column(JSON, nullable=True)
    consensus_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="runs")

class Clarification(Base):
    __tablename__ = "clarifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    question_json = Column(JSON, nullable=False)
    answer = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")  # pending, resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="clarifications")

def init_db():
    Base.metadata.create_all(bind=engine)
