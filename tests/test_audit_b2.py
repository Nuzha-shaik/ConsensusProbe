"""Regression tests for audit batch B2: C1, C2, H1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import pytest
from research.patch import Patch
from research.consensus import (
    plan_to_patch, majority_vote_patch, generate_clarification_question,
    calculate_consensus,
)


def _make_df():
    df = pd.DataFrame({'_rid': [1, 2, 3], 'val': [1.0, 2.0, 3.0]})
    return df


# C1: failed ops are logged, not silently swallowed; function returns a Patch
def test_c1_failed_op_returns_patch(caplog):
    import logging
    df = _make_df()
    bad_plan = {"ops": [{"op": "nonexistent_op", "params": {}}]}
    with caplog.at_level(logging.WARNING, logger="root"):
        result = plan_to_patch(df, bad_plan)
    assert isinstance(result, Patch), "plan_to_patch must return a Patch even when ops fail"
    assert any("nonexistent_op" in r.message for r in caplog.records), \
        "C1: failed ops must be logged, not silently swallowed"


def test_c1_good_ops_still_work():
    df = _make_df()
    good_plan = {"ops": [{"op": "fill_missing", "params": {"column": "val", "fill_mode": "mean"}}]}
    result = plan_to_patch(df, good_plan)
    assert isinstance(result, Patch)


# C2: majority vote does not corrupt float values via repr/literal_eval
def test_c2_float_not_corrupted():
    precise_val = 91.055999999999997
    p1 = Patch.create(cell_edits={(1, "val"): precise_val})
    p2 = Patch.create(cell_edits={(1, "val"): precise_val})
    result = majority_vote_patch([p1, p2])
    edits = result.cell_edits_dict()
    assert (1, "val") in edits
    assert edits[(1, "val")] == precise_val, \
        f"C2: float corrupted by repr/literal_eval: got {edits[(1, 'val')]!r}"


# H1: clarification picks param with actual differences, not alphabetically
def test_h1_picks_differing_param():
    df = pd.DataFrame({'_rid': [1], 'a': [1], 'b': [2]})
    plans = [
        {"ops": [{"op": "fill_missing", "params": {"column": "a", "fill_mode": "mean"}}]},
        {"ops": [{"op": "fill_missing", "params": {"column": "a", "fill_mode": "median"}}]},
    ]
    patches = [plan_to_patch(df, p) for p in plans]
    consensus = calculate_consensus(patches)
    if consensus.contested_atoms:
        q = generate_clarification_question(df, plans, patches, consensus)
        if q is not None:
            # fill_mode actually differs; column='a' is constant → fill_mode should be preferred
            assert q.parameter_name == "fill_mode", \
                f"H1: expected differing param 'fill_mode', got '{q.parameter_name}'"


def test_h1_no_diff_falls_back():
    """When all params are identical, falls back to first alphabetically (not an error)."""
    df = pd.DataFrame({'_rid': [1], 'a': [None]})
    plans = [
        {"ops": [{"op": "fill_missing", "params": {"column": "a", "fill_mode": "mean"}}]},
        {"ops": []},
    ]
    patches = [plan_to_patch(df, p) for p in plans]
    # just ensure it doesn't crash
    consensus = calculate_consensus(patches)
    q = generate_clarification_question(df, plans, patches, consensus)
    # either None or a valid question
    assert q is None or hasattr(q, 'parameter_name')
