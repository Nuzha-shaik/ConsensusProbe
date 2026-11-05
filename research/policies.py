"""Policy implementations for automated data cleaning with interactive consensus."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import random
from typing import Literal
import pandas as pd

from .patch import Patch
from .consensus import (
    plan_to_patch,
    calculate_consensus,
    generate_clarification_question,
    majority_vote_patch,
    ClarificationQuestion,
    QuestionOption,
)
from .simulators import UserSimulator, UserMode
from .track_s import TrackSTask

@dataclass
class PolicyResult:
    system: str
    task_id: str
    mode: str
    trial: int
    task_success: bool
    silent_error: bool
    questions_asked: int
    question_precision: float
    tokens: int
    simulated_latency: float
    final_patch: Patch

def evaluate_metrics(
    final_patch: Patch,
    gold: dict,
    questions_asked: int,
    is_ambiguous: bool,
) -> tuple[bool, bool, float]:
    """Calculate task_success, silent_error, and question_precision."""
    applied_atoms = set(final_patch.atoms())
    req_atoms = set(gold.get("required_edits", ()))
    forb_atoms = set(gold.get("forbidden_edits", ()))
    flagged_rids = set(final_patch.flagged_dict().keys())

    # task_success: all gold required edits applied AND zero forbidden edits
    req_satisfied = req_atoms.issubset(applied_atoms)
    forb_violated = len(applied_atoms & forb_atoms) > 0
    task_success = req_satisfied and not forb_violated

    # silent_error: a forbidden destructive edit applied without a question or flag
    # If a forbidden edit was applied, but the user was asked or the rid was flagged, it is not silent.
    # If forbidden edit applied AND questions_asked == 0 AND none of the forbidden rids are flagged:
    forbidden_rids = {atom[1] for atom in (applied_atoms & forb_atoms)}
    unflagged_forbidden = forbidden_rids - flagged_rids
    silent_error = (len(unflagged_forbidden) > 0) and (questions_asked == 0)

    # question_precision: asked-on-ambiguous / asked
    if questions_asked > 0:
        question_precision = 1.0 if is_ambiguous else 0.0
    else:
        question_precision = 1.0  # vacuously valid or 0.0, standard 1.0 when not asked

    return task_success, silent_error, question_precision

def run_system_a(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, **kwargs) -> PolicyResult:
    """System A: Single plan, never asks."""
    provider = provider or task.get_provider()
    plan = provider.generate(task.prompt, seed=task.seed, k=0)
    patch = plan_to_patch(task.df, plan)
    tokens = provider.token_count(task.prompt, plan)
    latency = 1.0

    task_success, silent_error, q_prec = evaluate_metrics(patch, task.gold, 0, task.gold["ambiguous"])

    return PolicyResult(
        system="A",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=0,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=patch,
    )

def run_system_a2(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, k: int = 3, **kwargs) -> PolicyResult:
    """System A2: Majority-vote of K=3 plans, never asks (token-matched control)."""
    provider = provider or task.get_provider()
    plans = provider.generate_k(task.prompt, seed=task.seed, k=k)
    patches = [plan_to_patch(task.df, p) for p in plans]
    maj_patch = majority_vote_patch(patches)

    tokens = sum(provider.token_count(task.prompt, p) for p in plans)
    latency = 1.0  # parallel generation

    task_success, silent_error, q_prec = evaluate_metrics(maj_patch, task.gold, 0, task.gold["ambiguous"])

    return PolicyResult(
        system="A2",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=0,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=maj_patch,
    )

def run_system_b(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, **kwargs) -> PolicyResult:
    """System B: Single plan + heuristic validators (row drop > 20%, null rate > 30%)."""
    provider = provider or task.get_provider()
    plan = provider.generate(task.prompt, seed=task.seed, k=0)
    patch = plan_to_patch(task.df, plan)
    tokens = provider.token_count(task.prompt, plan)
    latency = 1.0

    # Validators
    triggered = False
    orig_rows = len(task.df)
    deleted_rows = len(patch.deleted_rids)
    if orig_rows > 0 and (deleted_rows / orig_rows) > 0.20:
        triggered = True

    # High null rate or key violation check
    applied_df = patch.apply(task.df)
    for col in applied_df.columns:
        if col != "_rid" and applied_df[col].isna().mean() > 0.30:
            triggered = True

    questions_asked = 0
    final_patch = patch
    if triggered:
        questions_asked = 1
        latency += 0.5
        # Provide fallback question: approve or revert
        empty_patch = Patch.create()
        q = ClarificationQuestion(
            question_text="Data validation rule triggered. Proceed with changes?",
            parameter_name="validation_alert",
            options=[
                QuestionOption(0, "Apply planned changes", len(patch.deleted_rids), list(patch.deleted_rids)[:3], patch),
                QuestionOption(1, "Discard changes", 0, [], empty_patch),
            ],
        )
        ans = simulator.answer_question(q, task.gold)
        if ans == 1:
            final_patch = empty_patch
        elif ans == "unsure":
            final_patch = Patch.create(
                deleted_rids=patch.deleted_rids,
                cell_edits=patch.cell_edits_dict(),
                flagged={r: "validator_uncertain" for r in patch.deleted_rids},
            )

    task_success, silent_error, q_prec = evaluate_metrics(final_patch, task.gold, questions_asked, task.gold["ambiguous"])

    return PolicyResult(
        system="B",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=questions_asked,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=final_patch,
    )

def run_system_c(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, **kwargs) -> PolicyResult:
    """System C: Always ask."""
    provider = provider or task.get_provider()
    plans = provider.generate_k(task.prompt, seed=task.seed, k=3)
    patches = [plan_to_patch(task.df, p) for p in plans]
    consensus = calculate_consensus(patches)
    tokens = sum(provider.token_count(task.prompt, p) for p in plans)
    latency = 1.5

    questions_asked = 1
    question = generate_clarification_question(task.df, plans, patches, consensus)
    if question and question.options:
        ans = simulator.answer_question(question, task.gold)
        if ans == "unsure":
            maj = majority_vote_patch(patches)
            final_patch = Patch.create(
                deleted_rids=maj.deleted_rids,
                cell_edits=maj.cell_edits_dict(),
                flagged={r: "unsure_fallback" for r in consensus.contested_atoms if isinstance(r, tuple)},
            )
        else:
            final_patch = question.options[ans].patch
    else:
        final_patch = patches[0]

    task_success, silent_error, q_prec = evaluate_metrics(final_patch, task.gold, questions_asked, task.gold["ambiguous"])

    return PolicyResult(
        system="C",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=questions_asked,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=final_patch,
    )

def run_system_d(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, confidence_threshold: float = 0.75, **kwargs) -> PolicyResult:
    """System D: Ask when self-reported confidence < threshold."""
    provider = provider or task.get_provider()
    plan = provider.generate(task.prompt, seed=task.seed, k=0)
    patch = plan_to_patch(task.df, plan)
    tokens = provider.token_count(task.prompt, plan)
    latency = 1.0

    questions_asked = 0
    final_patch = patch
    if plan.get("confidence", 1.0) < confidence_threshold:
        questions_asked = 1
        latency += 0.5
        empty_patch = Patch.create()
        q = ClarificationQuestion(
            question_text="Model confidence below threshold. Proceed?",
            parameter_name="confidence_check",
            options=[
                QuestionOption(0, "Apply plan", len(patch.deleted_rids), list(patch.deleted_rids)[:3], patch),
                QuestionOption(1, "Discard plan", 0, [], empty_patch),
            ],
        )
        ans = simulator.answer_question(q, task.gold)
        if ans == 1:
            final_patch = empty_patch
        elif ans == "unsure":
            final_patch = Patch.create(
                deleted_rids=patch.deleted_rids,
                cell_edits=patch.cell_edits_dict(),
                flagged={r: "low_conf_flag" for r in patch.deleted_rids},
            )

    task_success, silent_error, q_prec = evaluate_metrics(final_patch, task.gold, questions_asked, task.gold["ambiguous"])

    return PolicyResult(
        system="D",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=questions_asked,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=final_patch,
    )

def run_system_e(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, tau_d: float = 0.0, k: int = 3, **kwargs) -> PolicyResult:
    """System E: ConsensusGate."""
    provider = provider or task.get_provider()
    plans = provider.generate_k(task.prompt, seed=task.seed, k=k)
    patches = [plan_to_patch(task.df, p) for p in plans]
    consensus = calculate_consensus(patches)
    tokens = sum(provider.token_count(task.prompt, p) for p in plans)
    latency = 1.0

    questions_asked = 0
    if consensus.should_ask(tau_d):
        question = generate_clarification_question(task.df, plans, patches, consensus)
        if question and question.options:
            questions_asked = 1
            latency += 0.5
            ans = simulator.answer_question(question, task.gold)
            if ans == "unsure":
                # Fall back to majority plan and flag contested rids
                maj = majority_vote_patch(patches)
                contested_rids = {atom[1] for atom in consensus.contested_atoms}
                final_patch = Patch.create(
                    deleted_rids=maj.deleted_rids,
                    cell_edits=maj.cell_edits_dict(),
                    flagged={r: "consensus_unsure" for r in contested_rids},
                )
            else:
                final_patch = question.options[ans].patch
        else:
            final_patch = majority_vote_patch(patches)
    else:
        final_patch = majority_vote_patch(patches)

    task_success, silent_error, q_prec = evaluate_metrics(final_patch, task.gold, questions_asked, task.gold["ambiguous"])

    return PolicyResult(
        system="E",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=questions_asked,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=final_patch,
    )

def run_system_r(task: TrackSTask, simulator: UserSimulator, trial: int, provider=None, dev_ask_rate: float = 0.45, **kwargs) -> PolicyResult:
    """System R: Random-ask baseline that asks with probability equal to E's DEV ask rate."""
    provider = provider or task.get_provider()
    plan = provider.generate(task.prompt, seed=task.seed, k=0)
    patch = plan_to_patch(task.df, plan)
    tokens = provider.token_count(task.prompt, plan)
    latency = 1.0

    # Seeded random ask
    rng = hashlib.sha256(f"R:{task.seed}:{trial}".encode()).hexdigest()
    val = int(rng[:8], 16) / 0xFFFFFFFF
    should_ask = (val < dev_ask_rate)

    questions_asked = 0
    final_patch = patch
    if should_ask:
        questions_asked = 1
        latency += 0.5
        empty_patch = Patch.create()
        q = ClarificationQuestion(
            question_text="Random inspection point triggered. Confirm changes?",
            parameter_name="random_audit",
            options=[
                QuestionOption(0, "Apply plan", len(patch.deleted_rids), list(patch.deleted_rids)[:3], patch),
                QuestionOption(1, "Discard plan", 0, [], empty_patch),
            ],
        )
        ans = simulator.answer_question(q, task.gold)
        if ans == 1:
            final_patch = empty_patch
        elif ans == "unsure":
            final_patch = Patch.create(
                deleted_rids=patch.deleted_rids,
                cell_edits=patch.cell_edits_dict(),
                flagged={r: "random_check_unsure" for r in patch.deleted_rids},
            )

    task_success, silent_error, q_prec = evaluate_metrics(final_patch, task.gold, questions_asked, task.gold["ambiguous"])

    return PolicyResult(
        system="R",
        task_id=task.task_id,
        mode=simulator.mode,
        trial=trial,
        task_success=task_success,
        silent_error=silent_error,
        questions_asked=questions_asked,
        question_precision=q_prec,
        tokens=tokens,
        simulated_latency=latency,
        final_patch=final_patch,
    )

SYSTEM_DISPATCH = {
    "A": run_system_a,
    "A2": run_system_a2,
    "B": run_system_b,
    "C": run_system_c,
    "D": run_system_d,
    "E": run_system_e,
    "R": run_system_r,
}
