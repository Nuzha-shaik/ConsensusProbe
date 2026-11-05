"""MockProvider: deterministic simulated LLM that generates cleaning plans."""
from __future__ import annotations
import hashlib
import json
import random
from typing import Any


def _derive_seed(base_seed: int, k: int) -> int:
    """Derive a sub-seed from base_seed and plan index k."""
    h = hashlib.sha256(f"{base_seed}:{k}".encode()).hexdigest()
    return int(h[:8], 16)


class MockProvider:
    """Simulated LLM provider. Deterministic given (seed, k)."""

    def __init__(self, gold_plan: list[dict], ambiguous_params: dict | None = None,
                 p_amb: float = 0.4, eps: float = 0.05):
        """
        gold_plan: list of {op, params} dicts defining the correct operations.
        ambiguous_params: {op_index: {param_name: [alternatives]}} for ambiguous ops.
        p_amb: probability of picking a non-gold alternative for ambiguous params.
        eps: probability of deviating from gold for unambiguous ops.
        """
        self.gold_plan = gold_plan
        self.ambiguous_params = ambiguous_params or {}
        self.p_amb = p_amb
        self.eps = eps

    def generate(self, prompt: str, seed: int, k: int) -> dict:
        """Generate one cleaning plan. Returns {ops: [...], confidence: float}."""
        rng = random.Random(_derive_seed(seed, k))
        ops = []
        for i, gold_op in enumerate(self.gold_plan):
            op = {'op': gold_op['op'], 'params': dict(gold_op['params'])}
            if i in self.ambiguous_params:
                # For each ambiguous parameter, maybe pick an alternative
                for param_name, alternatives in self.ambiguous_params[i].items():
                    if rng.random() < self.p_amb:
                        op['params'][param_name] = rng.choice(alternatives)
            else:
                # Unambiguous: follow gold with prob 1-eps
                if rng.random() < self.eps:
                    # Minor deviation: skip this op
                    continue
            ops.append(op)

        # Confidence is deterministic from the seed
        confidence = rng.uniform(0.5, 0.99)

        return {'ops': ops, 'confidence': round(confidence, 3)}

    def generate_k(self, prompt: str, seed: int, k: int) -> list[dict]:
        """Generate K plans."""
        return [self.generate(prompt, seed, i) for i in range(k)]

    def token_count(self, prompt: str, output: dict) -> int:
        """Deterministic token count = whitespace-token count of prompt + output."""
        prompt_tokens = len(prompt.split())
        output_str = json.dumps(output, sort_keys=True)
        output_tokens = len(output_str.split())
        return prompt_tokens + output_tokens
