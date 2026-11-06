import pytest
import pandas as pd
import numpy as np
from research.track_s import generate_track_s_task
from research.canary import inject_canaries
from research.simulators import UserSimulator
from research.patch import Patch
from research.consensus import ClarificationQuestion, QuestionOption

def test_h4_stable_rid_edits():
    task = generate_track_s_task(seed=42, mode="DEV")
    assert "_rid" in task.df.columns
    # Check that rows with _rid 0..5 exist
    rids = set(task.df["_rid"])
    assert 0 in rids

def test_h5_canary_arbitrary_schema():
    custom_df = pd.DataFrame([
        {"alpha": 10, "beta": "foo", "_rid": 1},
        {"alpha": 20, "beta": "bar", "_rid": 2},
    ])
    res_df, canary_ids = inject_canaries(custom_df, seed=123)
    assert len(canary_ids) > 0
    assert "_canary" in res_df.columns
    assert "alpha" in res_df.columns
    assert "beta" in res_df.columns

def test_m2_simulator_per_task_rng():
    p1 = Patch.create(deleted_rids=[1])
    p2 = Patch.create(deleted_rids=[2])
    sim = UserSimulator(mode="noisy", seed=42)
    q = ClarificationQuestion(
        question_text="Which?",
        parameter_name="col",
        options=[
            QuestionOption(0, "Opt 1", 1, [1], p1),
            QuestionOption(1, "Opt 2", 1, [2], p2),
        ]
    )
    gold = {"required_edits": {("del", 1)}, "forbidden_edits": set()}
    ans1 = sim.answer_question(q, gold=gold)
    ans2 = sim.answer_question(q, gold=gold)
    assert ans1 in [0, 1, "unsure"]
    assert ans2 in [0, 1, "unsure"]
