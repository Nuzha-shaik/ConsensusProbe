"""Tests for P4: Consensus engine, question generator, simulators, and policies."""
import pandas as pd
import pytest
from research.patch import Patch
from research.consensus import (
    calculate_consensus,
    pairwise_disagreement,
    majority_vote_patch,
    generate_clarification_question,
)
from research.simulators import UserSimulator, evaluate_option_quality
from research.track_s import generate_track_s_task
from research.policies import (
    run_system_a,
    run_system_a2,
    run_system_b,
    run_system_c,
    run_system_d,
    run_system_e,
    run_system_r,
)

def test_pairwise_disagreement():
    e1 = {("del", 1), ("del", 2)}
    e2 = {("del", 1), ("del", 3)}
    # Union=3, Inter=1 -> d = 1 - 1/3 = 2/3
    assert abs(pairwise_disagreement(e1, e2) - (2.0 / 3.0)) < 1e-6
    # Empty sets -> d = 0
    assert pairwise_disagreement(set(), set()) == 0.0

def test_consensus_calculation():
    p1 = Patch.create(deleted_rids=[1, 2])
    p2 = Patch.create(deleted_rids=[1, 3])
    p3 = Patch.create(deleted_rids=[1, 2])
    res = calculate_consensus([p1, p2, p3])
    assert res.score > 0
    assert res.has_destructive_or_transformative is True
    assert (("del", 2) in res.contested_atoms) or (("del", 3) in res.contested_atoms)

def test_majority_vote_patch():
    p1 = Patch.create(deleted_rids=[1, 2], cell_edits={(3, "val"): 100})
    p2 = Patch.create(deleted_rids=[1, 4], cell_edits={(3, "val"): 100})
    p3 = Patch.create(deleted_rids=[1, 2], cell_edits={(3, "val"): 200})
    maj = majority_vote_patch([p1, p2, p3])
    # rid 1 in all 3 -> kept
    assert 1 in maj.deleted_rids
    # rid 2 in 2/3 -> kept
    assert 2 in maj.deleted_rids
    # rid 4 in 1/3 -> not kept
    assert 4 not in maj.deleted_rids
    # (3, "val"): 100 in 2/3 -> kept
    assert maj.cell_edits_dict().get((3, "val")) == 100

def test_user_simulator_modes():
    gold = {"required_edits": (("del", 1),), "forbidden_edits": (("del", 2),)}
    p_good = Patch.create(deleted_rids=[1])
    p_bad = Patch.create(deleted_rids=[2])

    from research.consensus import ClarificationQuestion, QuestionOption
    q = ClarificationQuestion(
        question_text="Pick strategy",
        parameter_name="test",
        options=[
            QuestionOption(0, "Good", 1, [1], p_good),
            QuestionOption(1, "Bad", 1, [2], p_bad),
        ],
    )

    # Oracle always chooses good (idx 0)
    oracle = UserSimulator(mode="oracle", seed=42)
    assert oracle.answer_question(q, gold) == 0

    # Noisy chooses good most of the time
    noisy = UserSimulator(mode="noisy", seed=42)
    answers = [noisy.answer_question(q, gold) for _ in range(20)]
    assert 0 in answers

    # Unsure returns unsure some of the time
    unsure = UserSimulator(mode="unsure", seed=42)
    answers = [unsure.answer_question(q, gold) for _ in range(50)]
    assert "unsure" in answers

def test_policy_systems_on_mini_tasks():
    # Ambiguous task
    task = generate_track_s_task(1000, mode="DEV")
    sim = UserSimulator(mode="oracle", seed=42)

    # System A
    res_a = run_system_a(task, sim, trial=0)
    assert res_a.system == "A"
    assert res_a.questions_asked == 0

    # System A2
    res_a2 = run_system_a2(task, sim, trial=0)
    assert res_a2.system == "A2"
    assert res_a2.questions_asked == 0

    # System C (always ask)
    res_c = run_system_c(task, sim, trial=0)
    assert res_c.system == "C"
    assert res_c.questions_asked == 1

    # System D (confidence check)
    res_d = run_system_d(task, sim, trial=0, confidence_threshold=1.0)
    assert res_d.system == "D"
    assert res_d.questions_asked == 1

    # System E (ConsensusGate)
    res_e = run_system_e(task, sim, trial=0, tau_d=0.0)
    assert res_e.system == "E"
    assert isinstance(res_e.task_success, bool)
