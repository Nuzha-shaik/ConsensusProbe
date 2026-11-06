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
    # H5: clone an existing row to avoid hardcoded schema assumptions
    if len(temp_df) == 0:
        return temp_df, set()
    base_row = temp_df.iloc[rng.randint(0, len(temp_df) - 1)].to_dict()

    # Canary 1 & 2: Known fake duplicates — same content, same RID range
    canary_sku = f"CANARY-SKU-{rng.randint(100, 999)}"
    for i in range(2):
        row = dict(base_row)
        row["_rid"] = CANARY_RID_OFFSET + i
        row["_canary"] = True
        if "sku" in row:
            row["sku"] = canary_sku
        if "product_name" in row:
            row["product_name"] = "Canary Sensor Pod"
        canary_rows.append(row)

    # Canary 3: Unique probe row that should NOT be deleted
    safe_row = dict(base_row)
    safe_row["_rid"] = CANARY_RID_OFFSET + 2
    safe_row["_canary"] = True
    if "sku" in safe_row:
        safe_row["sku"] = "CANARY-SKU-SAFE"
    if "product_name" in safe_row:
        safe_row["product_name"] = "Unique Calibration Probe"
    canary_rows.append(safe_row)

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
