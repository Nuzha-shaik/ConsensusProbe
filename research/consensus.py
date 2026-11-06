"""Consensus engine: disagreement calculation, contested atoms, and asking decisions."""
from __future__ import annotations
from dataclasses import dataclass
import itertools
from typing import Any
import pandas as pd
from .patch import Patch
from .operations import execute_op

@dataclass(frozen=True)
class ConsensusResult:
    score: float
    contested_atoms: tuple
    common_atoms: tuple
    has_destructive_or_transformative: bool

    def should_ask(self, tau_d: float) -> bool:
        """Ask iff score > tau_d AND contested atoms contain a destructive or transformative atom."""
        return (self.score > tau_d) and self.has_destructive_or_transformative

def plan_to_patch(df: pd.DataFrame, plan: dict) -> Patch:
    """Execute a plan's operations sequentially on df and accumulate Patch."""
    curr_df = df.copy()
    accum_patch = Patch.create()
    failures = []
    for op_entry in plan.get("ops", []):
        op_name = op_entry["op"]
        params = op_entry.get("params", {})
        try:
            curr_df, p = execute_op(curr_df, op_name, params)
            accum_patch = accum_patch.merge(p)
        except Exception as exc:
            failures.append((op_name, params, exc))
    if failures:
        import logging
        for op_name, params, exc in failures:
            logging.warning("plan_to_patch: op %r params %r failed: %r", op_name, params, exc)
    return accum_patch

def pairwise_disagreement(atoms1: tuple | set, atoms2: tuple | set) -> float:
    """d(i,j) = 1 - |E_i ∩ E_j| / |E_i ∪ E_j|, with d = 0 when both sets are empty."""
    s1 = set(atoms1)
    s2 = set(atoms2)
    if not s1 and not s2:
        return 0.0
    union = s1 | s2
    inter = s1 & s2
    return 1.0 - (len(inter) / len(union))

def calculate_consensus(patches: list[Patch]) -> ConsensusResult:
    """Calculate mean pairwise disagreement, contested atoms, and asking criteria."""
    if not patches:
        return ConsensusResult(score=0.0, contested_atoms=(), common_atoms=(), has_destructive_or_transformative=False)

    k = len(patches)
    atom_sets = [set(p.atoms()) for p in patches]

    if k == 1:
        atoms = tuple(sorted(atom_sets[0]))
        return ConsensusResult(score=0.0, contested_atoms=(), common_atoms=atoms, has_destructive_or_transformative=False)

    # Pairwise disagreement
    pairs = list(itertools.combinations(range(k), 2))
    d_vals = [pairwise_disagreement(atom_sets[i], atom_sets[j]) for i, j in pairs]
    mean_d = sum(d_vals) / len(d_vals) if d_vals else 0.0

    all_union = set().union(*atom_sets)
    all_inter = set(atom_sets[0]).intersection(*atom_sets[1:])
    contested = all_union - all_inter

    # Destructive or transformative: any deletion or any edit
    has_destructive_or_transformative = any(
        atom[0] in ("del", "edit") for atom in contested
    )

    return ConsensusResult(
        score=round(mean_d, 6),
        contested_atoms=tuple(sorted(contested)),
        common_atoms=tuple(sorted(all_inter)),
        has_destructive_or_transformative=has_destructive_or_transformative,
    )

@dataclass
class QuestionOption:
    option_id: int
    description: str
    affected_rows_count: int
    example_rids: list[int]
    patch: Patch

@dataclass
class ClarificationQuestion:
    question_text: str
    parameter_name: str
    options: list[QuestionOption]

def generate_clarification_question(
    df: pd.DataFrame,
    plans: list[dict],
    patches: list[Patch],
    consensus: ConsensusResult,
) -> ClarificationQuestion | None:
    """Group contested plans/patches into 2-4 distinct options with affected row counts and example rids."""
    if not consensus.contested_atoms:
        return None

    # Group unique patches among plans
    unique_candidates: list[tuple[Patch, list[int]]] = []
    for plan_idx, p in enumerate(patches):
        matched = False
        for c_idx, (cand_patch, p_indices) in enumerate(unique_candidates):
            if set(cand_patch.atoms()) == set(p.atoms()):
                p_indices.append(plan_idx)
                matched = True
                break
        if not matched:
            unique_candidates.append((p, [plan_idx]))

    # If only 1 unique patch, no meaningful question
    if len(unique_candidates) <= 1:
        return None

    # Deterministic sorting: transformative/cleaning actions first (higher impact first), status-quo last
    unique_candidates.sort(
        key=lambda item: (
            len(item[0].deleted_rids) + len(item[0].cell_edits) > 0,
            len(item[0].deleted_rids),
            len(item[0].cell_edits),
            len(item[1]),
        ),
        reverse=True,
    )

    # Limit to 2-4 options
    options = []
    # Identify parameter difference if possible
    # Identify parameter where values actually differ across plans (H1)
    diff_params = {}
    for p in plans:
        for op in p.get("ops", []):
            for k, v in op.get("params", {}).items():
                diff_params.setdefault(k, set()).add(repr(v))
    # Prefer the first param that has >1 distinct value; fall back to first param alphabetically
    differing = [k for k, vals in sorted(diff_params.items()) if len(vals) > 1]
    param_name = differing[0] if differing else (sorted(diff_params)[0] if diff_params else "cleaning_strategy")

    for opt_id, (cand_patch, plan_indices) in enumerate(unique_candidates[:4]):
        affected_rids = sorted(list({int(r) for r in cand_patch.deleted_rids} | {int(rid) for (rid, col) in cand_patch.cell_edits_dict().keys()}))
        example_rids = [int(x) for x in affected_rids[:3]]

        desc = f"Strategy {opt_id + 1} (supported by {len(plan_indices)} plans): "
        if cand_patch.deleted_rids and cand_patch.cell_edits:
            desc += f"delete {len(cand_patch.deleted_rids)} rows; edit {len(cand_patch.cell_edits)} cells."
        elif cand_patch.deleted_rids:
            desc += f"delete {len(cand_patch.deleted_rids)} rows."
        elif cand_patch.cell_edits:
            desc += f"edit {len(cand_patch.cell_edits)} cells."
        else:
            desc += "no modifications."

        options.append(QuestionOption(
            option_id=opt_id,
            description=desc,
            affected_rows_count=len(affected_rids),
            example_rids=example_rids,
            patch=cand_patch,
        ))

    if param_name in ("by", "cleaning_strategy") or "by" in differing:
        q_text = "Multiple conflicting cleaning plans detected regarding duplicate handling and missing values. Which strategy should be applied?"
    else:
        q_text = f"Multiple conflicting cleaning plans detected regarding '{param_name}'. Which strategy should be applied?"

    return ClarificationQuestion(
        question_text=q_text,
        parameter_name=param_name,
        options=options,
    )

def majority_vote_patch(patches: list[Patch]) -> Patch:
    """Aggregate K patches by majority vote on atoms (atom in >= ceil(K/2) patches)."""
    if not patches:
        return Patch.create()
    if len(patches) == 1:
        return patches[0]

    k = len(patches)
    threshold = (k // 2) + 1

    atom_counts: dict[tuple, int] = {}
    for p in patches:
        for a in p.atoms():
            atom_counts[a] = atom_counts.get(a, 0) + 1

    majority_atoms = {a for a, count in atom_counts.items() if count >= threshold}

    del_rids = sorted([a[1] for a in majority_atoms if a[0] == "del"])
    # C2: collect actual values from patches directly, avoid repr/literal_eval float corruption
    edits: dict[tuple, Any] = {}
    for p in patches:
        for (rid, col), val in p.cell_edits_dict().items():
            atom = ("edit", rid, col, repr(val))
            if atom in majority_atoms:
                edits[(rid, col)] = val

    return Patch.create(deleted_rids=del_rids, cell_edits=edits)

