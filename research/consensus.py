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
    for op_entry in plan.get("ops", []):
        op_name = op_entry["op"]
        params = op_entry.get("params", {})
        try:
            curr_df, p = execute_op(curr_df, op_name, params)
            accum_patch = accum_patch.merge(p)
        except Exception:
            # If an op fails to apply, continue or record as-is
            continue
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
