"""User simulators for interactive clarification evaluation."""
from __future__ import annotations
import hashlib
import random
from typing import Literal
from .consensus import ClarificationQuestion, QuestionOption
from .patch import Patch

UserMode = Literal["oracle", "noisy", "unsure"]

def _seed_rng(seed: int | str) -> random.Random:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return random.Random(int(h[:8], 16))

def evaluate_option_quality(option_patch: Patch, gold: dict) -> float:
    """Score how well an option's patch matches gold requirements without forbidden edits."""
    atoms = set(option_patch.atoms())
    req = set(gold.get("required_edits", ()))
    forb = set(gold.get("forbidden_edits", ()))

    score = 0.0
    # Reward applying required edits
    if req:
        score += len(atoms & req) / len(req)
    else:
        score += 1.0

    # Heavily penalize forbidden edits
    if atoms & forb:
        score -= 2.0 * len(atoms & forb)

    return score

class UserSimulator:
    def __init__(self, mode: UserMode, seed: int):
        self.mode = mode
        self.seed = seed
        self.rng = _seed_rng(seed)

    def answer_question(self, question: ClarificationQuestion, gold: dict) -> int | Literal["unsure"]:
        """Return the index of the chosen option, or 'unsure'."""
        if not question.options:
            return "unsure"

        # Find best option according to gold
        option_scores = [evaluate_option_quality(opt.patch, gold) for opt in question.options]
        best_idx = int(max(range(len(option_scores)), key=lambda i: option_scores[i]))

        if self.mode == "oracle":
            return best_idx

        elif self.mode == "noisy":
            # 80% correct, 20% random choice
            if self.rng.random() < 0.8:
                return best_idx
            else:
                other_indices = [i for i in range(len(question.options)) if i != best_idx]
                if other_indices:
                    return self.rng.choice(other_indices)
                return best_idx

        elif self.mode == "unsure":
            # 30% unsure, 70% oracle
            if self.rng.random() < 0.3:
                return "unsure"
            return best_idx

        return best_idx
