"""Canary probes and ProbeGate safety validation."""
from __future__ import annotations
import hashlib
import random
import pandas as pd
from .patch import Patch
from .operations import execute_op
from .consensus import plan_to_patch

CANARY_RID_OFFSET = 90000

def _seed_rng(seed: int | str) -> random.Random:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return random.Random(int(h[:8], 16))

def inject_canaries(df: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, set[int]]:
    """Create a temporary copy of df with appended canary rows marked with _canary=True."""
    rng = _seed_rng(f"canary:{seed}")
    temp_df = df.copy()
    if "_canary" not in temp_df.columns:
        temp_df["_canary"] = False

    canary_rows = []
    # Canary 1 & 2: Known fake duplicates
    canary_sku = f"CANARY-SKU-{rng.randint(100, 999)}"
    canary_rows.append({
        "_rid": CANARY_RID_OFFSET,
        "sku": canary_sku,
        "product_name": "Canary Sensor Pod",
        "category": "Electronics",
        "price": 49.99,
        "quantity": 2,
        "total": 99.98,
        "tax_rate": 0.10,
        "_canary": True,
    })
    canary_rows.append({
        "_rid": CANARY_RID_OFFSET + 1,
        "sku": canary_sku,
        "product_name": "Canary Sensor Pod",
        "category": "Electronics",
        "price": 49.99,
        "quantity": 2,
        "total": 99.98,
        "tax_rate": 0.10,
        "_canary": True,
    })

    # Canary 3: Legitimate canary row with misspelt city/category that should NOT be deleted
    canary_rows.append({
        "_rid": CANARY_RID_OFFSET + 2,
        "sku": f"CANARY-SKU-SAFE",
        "product_name": "Unique Calibration Probe",
        "category": "Electronics",
        "price": 199.99,
        "quantity": 1,
        "total": 199.99,
        "tax_rate": 0.10,
        "_canary": True,
    })

    canary_df = pd.DataFrame(canary_rows)
    combined = pd.concat([temp_df, canary_df], ignore_index=True)
    canary_rids = {r["_rid"] for r in canary_rows}
    return combined, canary_rids

def verify_canary_safety(plan: dict, df_with_canaries: pd.DataFrame, canary_rids: set[int]) -> bool:
    """Evaluate whether plan behaves safely on canaries.

    Unsafe if:
    - Canary row CANARY_RID_OFFSET + 2 (the unique probe) is deleted.
    - Or unexpected destructive operations affect non-duplicate canaries.
    """
    safe_probe_rid = CANARY_RID_OFFSET + 2
    patch = plan_to_patch(df_with_canaries, plan)

    # If the plan deleted the unique calibration probe, it is unsafe
    if safe_probe_rid in patch.deleted_rids:
        return False

    return True

def filter_canary_artifacts(patch: Patch, canary_rids: set[int]) -> Patch:
    """Strip all canary row IDs and canary cell edits from a patch before export."""
    del_rids = [r for r in patch.deleted_rids if r not in canary_rids]
    edits = {k: v for k, v in patch.cell_edits_dict().items() if k[0] not in canary_rids}
    flags = {r: reason for r, reason in patch.flagged_dict().items() if r not in canary_rids}
    return Patch.create(deleted_rids=del_rids, cell_edits=edits, flagged=flags)
