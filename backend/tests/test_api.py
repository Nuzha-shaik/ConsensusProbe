"""Integration tests for ConsensusProbe FastAPI backend."""
import hashlib
import io
import os
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, STORAGE_DIR
from backend.app.export import neutralize_cell, neutralize_dataframe

client = TestClient(app)

def test_formula_injection_neutralization():
    assert neutralize_cell("=1+1") == "'=1+1"
    assert neutralize_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert neutralize_cell("-danger") == "'-danger"
    assert neutralize_cell("@alert") == "'@alert"
    assert neutralize_cell("normal text") == "normal text"
    assert neutralize_cell(123) == 123

def test_upload_invalid_extension():
    fake_py = io.BytesIO(b"print('hello')")
    response = client.post(
        "/upload",
        files={"file": ("malicious.py", fake_py, "text/x-python")},
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]

def test_full_pipeline_upload_clean_clarify_export():
    # 1. Create a synthetic dirty CSV
    csv_content = (
        "sku,product_name,category,price\n"
        "SKU-1,Laptop Pro,Electronics,999.0\n"
        "SKU-1,Laptop Pro,Electronics,999.0\n"  # Duplicate row
        "SKU-2,=SUM(A1:A2),Office,25.0\n"      # Formula injection attempt
        "SKU-3,Mouse,Electronics,\n"           # Missing value
    )
    raw_bytes = csv_content.encode("utf-8")
    initial_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # 2. Upload
    res_upload = client.post(
        "/upload",
        files={"file": ("test_inventory.csv", io.BytesIO(raw_bytes), "text/csv")},
    )
    assert res_upload.status_code == 200
    data = res_upload.json()
    dataset_id = data["id"]
    assert data["sha256"] == initial_sha256
    assert data["rows"] == 4
    assert data["cols"] == 4

    # Verify original file on disk is immutable and matches initial_sha256
    stored_path = os.path.join(STORAGE_DIR, f"{dataset_id}.csv")
    with open(stored_path, "rb") as f:
        stored_sha = hashlib.sha256(f.read()).hexdigest()
    assert stored_sha == initial_sha256

    # 3. Profile
    res_profile = client.get(f"/profile/{dataset_id}")
    assert res_profile.status_code == 200
    pdata = res_profile.json()
    assert pdata["rows"] == 4
    assert len(pdata["columns"]) == 4

    # 4. Analyze
    res_analyze = client.post(f"/analyze/{dataset_id}")
    assert res_analyze.status_code == 200
    adata = res_analyze.json()
    assert adata["completeness_score"] > 0
    assert adata["duplicate_rows"] == 1

    # 5. Clean
    res_clean = client.post(f"/clean/{dataset_id}")
    assert res_clean.status_code == 200
    cdata = res_clean.json()
    assert cdata["status"] in ("needs_clarification", "applied")

    # If needs_clarification, answer it
    if cdata["status"] == "needs_clarification":
        res_clarify = client.post(
            f"/clarify/{dataset_id}",
            json={"selected_option": 0, "notes": "Approved default option"},
        )
        assert res_clarify.status_code == 200
        assert res_clarify.json()["status"] == "applied"

    # 6. Export CSV
    res_export_csv = client.get(f"/export/{dataset_id}?format=csv")
    assert res_export_csv.status_code == 200
    exported_csv = res_export_csv.content.decode("utf-8")
    # Verify formula injection was neutralized
    assert "'=SUM(A1:A2)" in exported_csv

    # 7. Export XLSX
    res_export_xlsx = client.get(f"/export/{dataset_id}?format=xlsx")
    assert res_export_xlsx.status_code == 200
    assert len(res_export_xlsx.content) > 0

    # 8. Export PDF
    res_export_pdf = client.get(f"/export/{dataset_id}?format=pdf")
    assert res_export_pdf.status_code == 200
    assert res_export_pdf.content.startswith(b"%PDF")

    # 9. Verify original file hash has NOT changed (immutability check)
    with open(stored_path, "rb") as f:
        post_export_sha = hashlib.sha256(f.read()).hexdigest()
    assert post_export_sha == initial_sha256
