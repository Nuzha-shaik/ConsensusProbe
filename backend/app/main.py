"""FastAPI application for ConsensusProbe."""
from __future__ import annotations
import hashlib
import io
import json
import os
import shutil
import uuid
from typing import Literal

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .models import init_db, SessionLocal, Dataset, CandidatePlan, OperationRun, Clarification
from .export import export_csv, export_xlsx, export_pdf, neutralize_dataframe
from research.patch import Patch
from research.operations import _inject_rid, _drop_rid
from research.consensus import (
    calculate_consensus,
    generate_clarification_question,
    majority_vote_patch,
    plan_to_patch,
    ClarificationQuestion,
)
from research.mock_provider import MockProvider

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

init_db()

app = FastAPI(title="ConsensusProbe API", version="1.0.0")

# CORS restricted to Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Schemas ---

class DatasetSummary(BaseModel):
    id: str
    filename: str
    sha256: str
    rows: int
    cols: int

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int

class DatasetProfile(BaseModel):
    id: str
    filename: str
    rows: int
    cols: int
    columns: list[ColumnProfile]
    preview: list[dict]

class ClarifyRequest(BaseModel):
    selected_option: int
    notes: str = ""

class CleanResponse(BaseModel):
    status: Literal["needs_clarification", "applied", "no_changes"]
    consensus_score: float
    question: dict | None = None
    patch_summary: dict | None = None

# --- In-memory active patch tracker for current session ---
_ACTIVE_PATCHES: dict[str, Patch] = {}

# --- Routes ---

@app.post("/upload", response_model=DatasetSummary)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload CSV or Excel file with security validation and immutable storage."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension '{ext}'. Only .csv and .xlsx allowed.")

    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}{ext}"
    stored_path = os.path.join(STORAGE_DIR, stored_filename)

    hasher = hashlib.sha256()
    size = 0

    with open(stored_path, "wb") as f:
        while chunk := await file.read(65536):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                f.close()
                os.remove(stored_path)
                raise HTTPException(status_code=413, detail="File exceeds 50 MB upload limit.")
            hasher.update(chunk)
            f.write(chunk)

    file_sha256 = hasher.hexdigest()

    # Read dataframe to get row/col counts
    try:
        if ext == ".csv":
            df = pd.read_csv(stored_path)
        else:
            df = pd.read_excel(stored_path)
    except Exception as e:
        if os.path.isfile(stored_path):
            os.remove(stored_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    rows, cols = df.shape

    record = Dataset(
        id=file_id,
        filename=os.path.basename(file.filename),
        sha256=file_sha256,
        path=stored_path,
        rows=rows,
        cols=cols,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return DatasetSummary(
        id=record.id,
        filename=record.filename,
        sha256=record.sha256,
        rows=record.rows,
        cols=record.cols,
    )

def _load_dataset_df(dataset: Dataset) -> pd.DataFrame:
    ext = os.path.splitext(dataset.path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(dataset.path)
    else:
        df = pd.read_excel(dataset.path)
    return _inject_rid(df)

@app.get("/profile/{dataset_id}", response_model=DatasetProfile)
def get_dataset_profile(dataset_id: str, db: Session = Depends(get_db)):
    """Return statistical profile and first 20 rows preview."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = _load_dataset_df(dataset)

    # If an active patch exists, apply it for the profile
    if dataset_id in _ACTIVE_PATCHES:
        df = _ACTIVE_PATCHES[dataset_id].apply(df)

    cols_profile = []
    for col in df.columns:
        if col == "_rid":
            continue
        nulls = int(df[col].isna().sum())
        cols_profile.append(ColumnProfile(
            name=col,
            dtype=str(df[col].dtype),
            null_count=nulls,
            null_pct=round(nulls / len(df) * 100, 2) if len(df) > 0 else 0.0,
            unique_count=int(df[col].nunique()),
        ))

    clean_preview = _drop_rid(df.head(20)).fillna("").to_dict(orient="records")

    return DatasetProfile(
        id=dataset.id,
        filename=dataset.filename,
        rows=len(df),
        cols=len(df.columns) - (1 if "_rid" in df.columns else 0),
        columns=cols_profile,
        preview=clean_preview,
    )

@app.post("/clean/{dataset_id}", response_model=CleanResponse)
def clean_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Invoke ConsensusGate: generate 3 candidate plans, measure disagreement, and apply or request clarification."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = _load_dataset_df(dataset)

    # Use simulated provider or generate cleaning operations
    # Synthesize realistic candidate plans based on dataset features
    plans = []
    # Identify duplicate candidates and missing columns
    dup_cols = [c for c in df.columns if c not in ("_rid", "price", "total", "quantity")]
    null_cols = [c for c in df.columns if df[c].isna().any() and c != "_rid"]

    # Plan 0: Standard deduplication
    p0_ops = []
    if dup_cols:
        p0_ops.append({"op": "deduplicate", "params": {"by": [dup_cols[0]], "keep": "first"}})
    for nc in null_cols:
        p0_ops.append({"op": "handle_missing", "params": {"col": nc, "strategy": "drop"}})
    plans.append({"ops": p0_ops, "confidence": 0.88})

    # Plan 1: Keep last or impute mean
    p1_ops = []
    if dup_cols:
        p1_ops.append({"op": "deduplicate", "params": {"by": [dup_cols[0]], "keep": "first"}})
    for nc in null_cols:
        strategy = "fill_mean" if pd.api.types.is_numeric_dtype(df[nc]) else "drop"
        p1_ops.append({"op": "handle_missing", "params": {"col": nc, "strategy": strategy}})
    plans.append({"ops": p1_ops, "confidence": 0.82})

    # Plan 2: Alternative deduplication scope
    p2_ops = []
    if len(dup_cols) >= 2:
        p2_ops.append({"op": "deduplicate", "params": {"by": dup_cols[:2], "keep": "first"}})
    elif dup_cols:
        p2_ops.append({"op": "deduplicate", "params": {"by": [dup_cols[0]], "keep": "last"}})
    for nc in null_cols:
        strategy = "fill_median" if pd.api.types.is_numeric_dtype(df[nc]) else "drop"
        p2_ops.append({"op": "handle_missing", "params": {"col": nc, "strategy": strategy}})
    plans.append({"ops": p2_ops, "confidence": 0.79})

    # Store candidate plans
    db.query(CandidatePlan).filter(CandidatePlan.dataset_id == dataset_id).delete()
    for idx, p in enumerate(plans):
        db.add(CandidatePlan(
            dataset_id=dataset_id,
            plan_index=idx,
            plan_json=p,
            confidence=p["confidence"],
        ))
    db.commit()

    patches = [plan_to_patch(df, p) for p in plans]
    consensus = calculate_consensus(patches)

    # Disagreement threshold tau_d = 0.0
    if consensus.should_ask(tau_d=0.0):
        question = generate_clarification_question(df, plans, patches, consensus)
        if question and question.options:
            q_dict = {
                "question_text": question.question_text,
                "parameter_name": question.parameter_name,
                "options": [
                    {
                        "option_id": int(opt.option_id),
                        "description": str(opt.description),
                        "affected_rows_count": int(opt.affected_rows_count),
                        "example_rids": [int(x) for x in opt.example_rids],
                    }
                    for opt in question.options
                ],
            }

            # Record clarification
            db.query(Clarification).filter(Clarification.dataset_id == dataset_id).delete()
            db.add(Clarification(
                dataset_id=dataset_id,
                question_json=q_dict,
                status="pending",
            ))
            db.commit()

            return CleanResponse(
                status="needs_clarification",
                consensus_score=consensus.score,
                question=q_dict,
            )

    # If no disagreement or non-destructive, apply majority patch directly
    final_patch = majority_vote_patch(patches)
    _ACTIVE_PATCHES[dataset_id] = final_patch

    summary = {
        "deleted_rows": len(final_patch.deleted_rids),
        "edited_cells": len(final_patch.cell_edits),
        "flagged_rows": len(final_patch.flagged),
    }

    db.add(OperationRun(
        dataset_id=dataset_id,
        status="applied",
        applied_patch=summary,
        consensus_score=consensus.score,
    ))
    db.commit()

    return CleanResponse(
        status="applied",
        consensus_score=consensus.score,
        patch_summary=summary,
    )

@app.post("/clarify/{dataset_id}", response_model=CleanResponse)
def resolve_clarification(dataset_id: str, req: ClarifyRequest, db: Session = Depends(get_db)):
    """User answers clarification question to resolve conflicting plans."""
    clarification = db.query(Clarification).filter(
        Clarification.dataset_id == dataset_id,
        Clarification.status == "pending",
    ).first()
    if not clarification:
        raise HTTPException(status_code=400, detail="No pending clarification for this dataset")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    df = _load_dataset_df(dataset)

    # Load stored plans
    plans_records = db.query(CandidatePlan).filter(CandidatePlan.dataset_id == dataset_id).order_by(CandidatePlan.plan_index).all()
    plans = [p.plan_json for p in plans_records]
    patches = [plan_to_patch(df, p) for p in plans]
    consensus = calculate_consensus(patches)
    question = generate_clarification_question(df, plans, patches, consensus)

    if not question or req.selected_option >= len(question.options):
        raise HTTPException(status_code=400, detail="Invalid option selected")

    selected_patch = question.options[req.selected_option].patch
    _ACTIVE_PATCHES[dataset_id] = selected_patch

    clarification.status = "resolved"
    clarification.answer = f"Option {req.selected_option}: {req.notes}"

    summary = {
        "deleted_rows": len(selected_patch.deleted_rids),
        "edited_cells": len(selected_patch.cell_edits),
        "flagged_rows": len(selected_patch.flagged),
    }

    db.add(OperationRun(
        dataset_id=dataset_id,
        status="applied",
        applied_patch=summary,
        consensus_score=consensus.score,
    ))
    db.commit()

    return CleanResponse(
        status="applied",
        consensus_score=consensus.score,
        patch_summary=summary,
    )

@app.post("/analyze/{dataset_id}")
def analyze_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Return in-depth dataset quality metrics and recommendations."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = _load_dataset_df(dataset)
    if dataset_id in _ACTIVE_PATCHES:
        df = _ACTIVE_PATCHES[dataset_id].apply(df)

    total_cells = df.shape[0] * max(df.shape[1] - 1, 1)
    total_missing = int(df.isna().sum().sum())
    completeness = round((1.0 - (total_missing / total_cells)) * 100, 2) if total_cells > 0 else 100.0

    return {
        "dataset_id": dataset.id,
        "filename": dataset.filename,
        "rows": len(df),
        "cols": len(df.columns) - 1,
        "completeness_score": completeness,
        "duplicate_rows": int(df.duplicated(subset=[c for c in df.columns if c != "_rid"]).sum()),
        "recommendations": [
            "Verify category normalization on textual fields.",
            "Inspect flagged outliers in numerical attributes.",
            "Neutralize formula prefixes prior to export.",
        ],
    }

@app.get("/export/{dataset_id}")
def export_dataset(dataset_id: str, format: Literal["pdf", "csv", "xlsx"] = Query("csv"), db: Session = Depends(get_db)):
    """Export dataset with formula injection protection and audit trail."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = _load_dataset_df(dataset)
    if dataset_id in _ACTIVE_PATCHES:
        df = _ACTIVE_PATCHES[dataset_id].apply(df)

    # Always drop internal row id
    export_df = _drop_rid(df)

    # Fetch audit log runs
    runs = db.query(OperationRun).filter(OperationRun.dataset_id == dataset_id).order_by(OperationRun.created_at).all()
    audit_log = [f"{r.created_at.strftime('%Y-%m-%d %H:%M:%S')}: {r.status} (consensus={r.consensus_score}) -> {r.applied_patch}" for r in runs]

    base_name = os.path.splitext(dataset.filename)[0]

    if format == "csv":
        content = export_csv(export_df)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={base_name}_cleaned.csv"},
        )
    elif format == "xlsx":
        content = export_xlsx(export_df, audit_log=audit_log)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={base_name}_cleaned.xlsx"},
        )
    elif format == "pdf":
        summary_info = {
            "dataset_id": dataset.id,
            "filename": dataset.filename,
            "sha256": dataset.sha256,
            "rows": len(export_df),
            "cols": len(export_df.columns),
            "status": "Cleaned & Validated via ConsensusGate",
        }
        content = export_pdf(summary_info, audit_log=audit_log)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={base_name}_audit_report.pdf"},
        )
