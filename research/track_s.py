"""Track S generator: retail/inventory tasks with gold labels and controlled ambiguity."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
import random
from typing import Literal
import pandas as pd
from .patch import Patch
from .operations import _inject_rid
from .mock_provider import MockProvider

AMBIGUITY_TYPES = [
    "duplicate_id_vs_name",
    "category_granularity",
    "missing_strategy",
    "recalculate_basis",
    "type_coercion",
]

@dataclass
class TrackSTask:
    task_id: str
    seed: int
    mode: Literal["DEV", "TEST"]
    df: pd.DataFrame
    gold: dict
    ambiguous_params: dict
    prompt: str

    def get_provider(self, p_amb: float = 0.4, eps: float = 0.05) -> MockProvider:
        return MockProvider(
            gold_plan=self.gold["gold_plan"],
            ambiguous_params=self.ambiguous_params,
            p_amb=p_amb,
            eps=eps,
        )

def _seed_rng(seed: int) -> random.Random:
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return random.Random(int(h[:8], 16))

def generate_track_s_task(seed: int, mode: Literal["DEV", "TEST"] = "DEV") -> TrackSTask:
    """Generate a single synthetic retail/inventory cleaning task."""
    if mode == "DEV" and seed >= 5000:
        raise ValueError(f"DEV mode refuses TEST seed {seed} (must be < 5000)")
    if mode == "TEST" and seed < 5000:
        raise ValueError(f"TEST mode refuses DEV seed {seed} (must be >= 5000)")

    rng = _seed_rng(seed)

    # 50% ambiguous tasks
    is_ambiguous = (rng.random() < 0.5)
    ambiguity_type = rng.choice(AMBIGUITY_TYPES) if is_ambiguous else "none"

    rows = []
    num_rows = rng.randint(25, 40)
    products = ["Laptop Pro", "Desk Chair", "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard"]
    cats_broad = {"Laptop Pro": "Electronics", "Desk Chair": "Furniture", "Wireless Mouse": "Electronics", "USB-C Hub": "Electronics", "Mechanical Keyboard": "Electronics"}
    cats_fine = {"Laptop Pro": "Computers", "Desk Chair": "Office", "Wireless Mouse": "Accessories", "USB-C Hub": "Accessories", "Mechanical Keyboard": "Accessories"}

    for i in range(num_rows):
        prod = rng.choice(products)
        sku = f"SKU-{1000 + (i % 12)}"
        price = round(rng.uniform(15.0, 500.0), 2)
        qty = rng.randint(1, 10)
        total = round(price * qty, 2)
        cat = cats_broad[prod] if rng.random() < 0.7 else cats_fine[prod]
        rows.append({
            "sku": sku,
            "product_name": prod,
            "category": cat,
            "price": price,
            "quantity": qty,
            "total": total,
            "tax_rate": 0.10,
        })

    df = pd.DataFrame(rows)
    df = _inject_rid(df)

    # Inject dirty data according to ambiguity_type
    required_edits = []
    forbidden_edits = []
    gold_plan = []
    ambiguous_params = {}

    if is_ambiguous and ambiguity_type == "duplicate_id_vs_name":
        # Two rows have identical product_name but different SKU, or identical SKU but different product_name
        df.at[0, "product_name"] = "Laptop Pro"
        df.at[0, "sku"] = "SKU-9999"
        df.at[1, "product_name"] = "Laptop Pro"
        df.at[1, "sku"] = "SKU-8888"
        # Gold: deduplicate by product_name
        gold_plan.append({"op": "deduplicate", "params": {"by": ["product_name"], "keep": "first"}})
        ambiguous_params[0] = {"by": [["sku"], ["product_name", "sku"]]}
        # Required: rid 1 deleted
        required_edits.append(("del", 1))
        # Forbidden: deleting rid 0 or deleting unrelated rows
        forbidden_edits.append(("del", 0))

    elif is_ambiguous and ambiguity_type == "category_granularity":
        # Broad vs fine categorization
        df.at[2, "category"] = "elec"
        mapping_broad = {"elec": "Electronics"}
        mapping_fine = {"elec": "Accessories"}
        gold_plan.append({"op": "normalize_category", "params": {"col": "category", "mapping": mapping_broad}})
        ambiguous_params[0] = {"mapping": [mapping_fine, {"elec": "Office"}]}
        required_edits.append(("edit", 2, "category", repr("Electronics")))
        forbidden_edits.append(("edit", 2, "category", repr("Accessories")))

    elif is_ambiguous and ambiguity_type == "missing_strategy":
        # Missing values in price
        df.at[3, "price"] = None
        gold_plan.append({"op": "handle_missing", "params": {"col": "price", "strategy": "fill_median"}})
        ambiguous_params[0] = {"strategy": ["drop", "fill_mean", "fill:0.0"]}
        # Median fill
        med = float(df["price"].dropna().median())
        required_edits.append(("edit", 3, "price", repr(med)))
        forbidden_edits.append(("del", 3))  # Dropping rid 3 is a destructive silent error if unjustified

    elif is_ambiguous and ambiguity_type == "recalculate_basis":
        # Total recalculation: pre-tax (price * qty) vs post-tax (price * qty * (1 + tax_rate))
        df.at[4, "total"] = 0.0
        gold_plan.append({
            "op": "recalculate",
            "params": {"target": "total", "formula": "price * quantity", "source_cols": ["price", "quantity"]}
        })
        ambiguous_params[0] = {
            "formula": ["price * quantity * (1 + tax_rate)", "price * quantity * 0.9"]
        }
        val = round(df.at[4, "price"] * df.at[4, "quantity"], 2)
        required_edits.append(("edit", 4, "total", repr(val)))
        val_tax = round(val * 1.10, 2)
        forbidden_edits.append(("edit", 4, "total", repr(val_tax)))

    elif is_ambiguous and ambiguity_type == "type_coercion":
        # Quantity stored as float or string
        df.at[5, "quantity"] = 5.0
        gold_plan.append({"op": "convert_type", "params": {"col": "quantity", "dtype": "int"}})
        ambiguous_params[0] = {"dtype": ["str", "float"]}
        required_edits.append(("edit", 5, "quantity", repr(5)))
        forbidden_edits.append(("edit", 5, "quantity", repr("5")))

    else:
        # Unambiguous task
        ambiguity_type = "unambiguous"
        df.at[0, "category"] = "elec"
        gold_plan.append({"op": "normalize_category", "params": {"col": "category", "mapping": {"elec": "Electronics"}}})
        required_edits.append(("edit", 0, "category", repr("Electronics")))
        forbidden_edits.append(("del", 0))

    gold = {
        "required_edits": tuple(sorted(required_edits)),
        "forbidden_edits": tuple(sorted(forbidden_edits)),
        "ambiguous": is_ambiguous,
        "ambiguity_type": ambiguity_type,
        "gold_plan": gold_plan,
    }

    prompt = f"Clean the inventory dataset for task {seed}. Address missing values, duplicates, and category standards."

    return TrackSTask(
        task_id=f"track_s_{mode.lower()}_{seed}",
        seed=seed,
        mode=mode,
        df=df,
        gold=gold,
        ambiguous_params=ambiguous_params,
        prompt=prompt,
    )

def generate_dev_dataset(start_seed: int = 1000, n: int = 20) -> list[TrackSTask]:
    """Generate 20 DEV tasks with seeds 1000-1019."""
    return [generate_track_s_task(seed, mode="DEV") for seed in range(start_seed, start_seed + n)]

def generate_test_dataset(start_seed: int = 5000, n: int = 100) -> list[TrackSTask]:
    """Generate 100 TEST tasks with seeds 5000-5099."""
    return [generate_track_s_task(seed, mode="TEST") for seed in range(start_seed, start_seed + n)]
