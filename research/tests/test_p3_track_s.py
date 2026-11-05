"""Tests for Track S dataset generator."""
import pytest
from research.track_s import (
    generate_track_s_task,
    generate_dev_dataset,
    AMBIGUITY_TYPES,
)

def test_seed_enforcement():
    # DEV refuses >= 5000
    with pytest.raises(ValueError, match="DEV mode refuses TEST seed"):
        generate_track_s_task(5000, mode="DEV")

    # TEST refuses < 5000
    with pytest.raises(ValueError, match="TEST mode refuses DEV seed"):
        generate_track_s_task(1000, mode="TEST")

def test_ambiguity_taxonomy_at_least_five():
    assert len(AMBIGUITY_TYPES) >= 5

def test_dev_dataset_generation():
    dev_tasks = generate_dev_dataset(start_seed=1000, n=20)
    assert len(dev_tasks) == 20

    # Check determinism: re-generating task 1000 produces identical DF and gold
    t0 = generate_track_s_task(1000, mode="DEV")
    t0_repeat = generate_track_s_task(1000, mode="DEV")
    assert t0.gold == t0_repeat.gold
    assert t0.df.equals(t0_repeat.df)

    # Check required gold fields
    for t in dev_tasks:
        assert "required_edits" in t.gold
        assert "forbidden_edits" in t.gold
        assert "ambiguous" in t.gold
        assert "ambiguity_type" in t.gold
        assert isinstance(t.gold["ambiguous"], bool)
        assert "_rid" in t.df.columns

    ambiguous_count = sum(1 for t in dev_tasks if t.gold["ambiguous"])
    # 20 tasks, roughly balanced 50%
    assert 5 <= ambiguous_count <= 15

def test_mock_provider_from_task():
    task = generate_track_s_task(1001, mode="DEV")
    provider = task.get_provider(p_amb=0.4, eps=0.05)
    plans = provider.generate_k(task.prompt, seed=task.seed, k=3)
    assert len(plans) == 3
    for plan in plans:
        assert "ops" in plan
        assert "confidence" in plan
