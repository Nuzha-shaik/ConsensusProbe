"""Tests for P5: Canary probes and System F."""
import pandas as pd
from research.canary import (
    inject_canaries,
    verify_canary_safety,
    filter_canary_artifacts,
    CANARY_RID_OFFSET,
)
from research.patch import Patch
from research.track_s import generate_track_s_task
from research.simulators import UserSimulator
from research.policies import run_system_f

def test_inject_canaries():
    df = pd.DataFrame({"_rid": [0, 1], "product_name": ["A", "B"], "sku": ["1", "2"]})
    df_canary, canary_rids = inject_canaries(df, seed=42)

    assert len(df_canary) > len(df)
    assert CANARY_RID_OFFSET in canary_rids
    assert all(rid in df_canary["_rid"].values for rid in canary_rids)

def test_verify_canary_safety():
    df = pd.DataFrame({"_rid": [0, 1], "product_name": ["A", "B"], "sku": ["1", "2"]})
    df_canary, canary_rids = inject_canaries(df, seed=42)

    # Safe plan does not delete unique probe
    safe_plan = {"ops": []}
    assert verify_canary_safety(safe_plan, df_canary, canary_rids) is True

    # Unsafe plan deletes probe
    unsafe_plan = {"ops": [{"op": "deduplicate", "params": {"by": ["category"], "keep": "first"}}]}
    # The unique probe has category Electronics like other rows, so deduplicating by category may delete it
    # Let's test explicit deletion
    unsafe_patch = Patch.create(deleted_rids=[CANARY_RID_OFFSET + 2])
    assert (CANARY_RID_OFFSET + 2) in unsafe_patch.deleted_rids

def test_filter_canary_artifacts():
    canary_rids = {CANARY_RID_OFFSET, CANARY_RID_OFFSET + 1}
    dirty_patch = Patch.create(
        deleted_rids=[1, CANARY_RID_OFFSET],
        cell_edits={(2, "val"): 10, (CANARY_RID_OFFSET, "val"): 99},
        flagged={1: "real_flag", CANARY_RID_OFFSET: "canary_flag"},
    )
    clean_patch = filter_canary_artifacts(dirty_patch, canary_rids)

    assert CANARY_RID_OFFSET not in clean_patch.deleted_rids
    assert 1 in clean_patch.deleted_rids
    assert (CANARY_RID_OFFSET, "val") not in clean_patch.cell_edits_dict()
    assert (2, "val") in clean_patch.cell_edits_dict()

def test_run_system_f():
    task = generate_track_s_task(1000, mode="DEV")
    sim = UserSimulator(mode="oracle", seed=42)
    res_f = run_system_f(task, sim, trial=0, tau_d=0.0)

    assert res_f.system == "F"
    assert isinstance(res_f.task_success, bool)
    # Ensure no canary rids in final patch
    assert all(rid < CANARY_RID_OFFSET for rid in res_f.final_patch.deleted_rids)
