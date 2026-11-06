import io
import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import (
    app,
    _ACTIVE_PATCHES,
    _PATCH_CACHE,
    get_active_patch,
    set_active_patch,
    patch_to_dict,
    patch_from_dict,
    PATCH_CACHE_MAX_SIZE,
)
from backend.app.models import SessionLocal
from research.patch import Patch

client = TestClient(app)

def test_h2_patch_persisted_in_db():
    # 1. Upload
    csv_data = "col1,col2\nA,1\nA,1\n"
    res = client.post(
        "/upload",
        files={"file": ("test_h2.csv", io.BytesIO(csv_data.encode()), "text/csv")},
    )
    dataset_id = res.json()["id"]

    # 2. Clean
    res_clean = client.post(f"/clean/{dataset_id}")
    assert res_clean.status_code == 200
    cdata = res_clean.json()
    if cdata["status"] == "needs_clarification":
        res_clarify = client.post(
            f"/clarify/{dataset_id}",
            json={"selected_option": 0, "notes": "Approved"},
        )
        assert res_clarify.status_code == 200

    # 3. Simulate process restart / new worker: clear memory caches completely
    _PATCH_CACHE.clear()
    _ACTIVE_PATCHES.clear()

    # 4. Verify get_active_patch restores from database
    db = SessionLocal()
    try:
        restored = get_active_patch(dataset_id, db)
        assert restored is not None
        assert isinstance(restored, Patch)
    finally:
        db.close()

def test_m10_patch_cache_eviction():
    _PATCH_CACHE.clear()
    p = Patch.create(deleted_rids=[1])

    # Fill beyond max size
    for i in range(PATCH_CACHE_MAX_SIZE + 5):
        set_active_patch(f"dataset_{i}", p)

    assert len(_PATCH_CACHE) <= PATCH_CACHE_MAX_SIZE
    assert "dataset_0" not in _PATCH_CACHE

def test_h6_clean_uses_mock_provider():
    # Dataset with duplicates and missing values
    csv_data = "sku,name,price\nS1,P1,10.0\nS1,P1,10.0\nS2,P2,\n"
    res = client.post(
        "/upload",
        files={"file": ("test_h6.csv", io.BytesIO(csv_data.encode()), "text/csv")},
    )
    dataset_id = res.json()["id"]
    res_clean = client.post(f"/clean/{dataset_id}")
    assert res_clean.status_code == 200
    data = res_clean.json()
    assert "status" in data
    assert "consensus_score" in data
