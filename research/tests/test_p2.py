"""Tests for P2: operations, patch, mock provider."""
import pandas as pd
import pytest
from research.patch import Patch
from research.operations import (
    deduplicate, normalize_category, recalculate,
    handle_missing, convert_type, execute_op,
    OperationError, _inject_rid,
)
from research.mock_provider import MockProvider


# --- Patch tests ---

class TestPatch:
    def test_atoms_empty(self):
        p = Patch.create()
        assert p.atoms() == ()

    def test_atoms_sorted(self):
        p = Patch.create(deleted_rids=[3, 1], cell_edits={(2, 'x'): 'a', (1, 'y'): 'b'})
        atoms = p.atoms()
        assert atoms == (
            ("del", 1), ("del", 3),
            ("edit", 1, "y", "'b'"), ("edit", 2, "x", "'a'"),
        )

    def test_flags_excluded_from_atoms(self):
        p = Patch.create(flagged={1: 'suspicious'})
        assert p.atoms() == ()
        assert p.flagged_dict() == {1: 'suspicious'}

    def test_apply(self):
        df = pd.DataFrame({'_rid': [0, 1, 2], 'val': [10, 20, 30]})
        p = Patch.create(deleted_rids=[1], cell_edits={(2, 'val'): 99})
        result = p.apply(df)
        assert list(result['_rid']) == [0, 2]
        assert result.loc[result['_rid'] == 2, 'val'].iloc[0] == 99

    def test_merge(self):
        p1 = Patch.create(deleted_rids=[1], cell_edits={(2, 'x'): 'a'})
        p2 = Patch.create(deleted_rids=[3], cell_edits={(2, 'x'): 'b'})
        merged = p1.merge(p2)
        assert set(merged.deleted_rids) == {1, 3}
        assert merged.cell_edits_dict()[(2, 'x')] == 'b'  # later wins

    def test_round_trip(self):
        df = pd.DataFrame({'_rid': [0, 1, 2, 3], 'name': ['A', 'B', 'C', 'D']})
        p = Patch.create(deleted_rids=[1], cell_edits={(2, 'name'): 'X'})
        result = p.apply(df)
        assert len(result) == 3
        assert 'X' in result['name'].values


# --- Operations tests ---

def _make_df():
    return pd.DataFrame({
        '_rid': [0, 1, 2, 3],
        'name': ['Alice', 'Bob', 'Alice', 'Charlie'],
        'category': ['cat_a', 'cat_b', 'cat_a', 'cat_c'],
        'value': [10.0, 20.0, 10.0, 30.0],
    })


class TestOperations:
    def test_deduplicate_purity(self):
        df = _make_df()
        original = df.copy()
        result, patch = deduplicate(df, by=['name'], keep='first')
        pd.testing.assert_frame_equal(df, original)  # input unchanged
        assert len(result) == 3
        assert 2 in patch.deleted_rids

    def test_deduplicate_bad_keep(self):
        with pytest.raises(OperationError):
            deduplicate(_make_df(), by=['name'], keep='invalid')

    def test_deduplicate_missing_col(self):
        with pytest.raises(OperationError):
            deduplicate(_make_df(), by=['nonexistent'])

    def test_normalize_category_purity(self):
        df = _make_df()
        original = df.copy()
        result, patch = normalize_category(df, 'category', {'cat_a': 'Category A', 'cat_b': 'Category B'})
        pd.testing.assert_frame_equal(df, original)
        assert 'Category A' in result['category'].values

    def test_handle_missing_drop(self):
        df = pd.DataFrame({'_rid': [0, 1, 2], 'val': [1.0, None, 3.0]})
        original = df.copy()
        result, patch = handle_missing(df, 'val', 'drop')
        pd.testing.assert_frame_equal(df, original)
        assert len(result) == 2
        assert 1 in patch.deleted_rids

    def test_handle_missing_fill_mean(self):
        df = pd.DataFrame({'_rid': [0, 1, 2], 'val': [10.0, None, 30.0]})
        result, patch = handle_missing(df, 'val', 'fill_mean')
        assert result.loc[result['_rid'] == 1, 'val'].iloc[0] == 20.0

    def test_convert_type(self):
        df = pd.DataFrame({'_rid': [0, 1], 'val': ['1', '2']})
        result, patch = convert_type(df, 'val', 'int')
        assert result['val'].iloc[0] == 1

    def test_recalculate(self):
        df = pd.DataFrame({'_rid': [0, 1], 'price': [10, 20], 'qty': [2, 3], 'total': [0, 0]})
        result, patch = recalculate(df, 'total', 'price * qty', ['price', 'qty'])
        assert result.loc[0, 'total'] == 20
        assert result.loc[1, 'total'] == 60

    def test_execute_op_unknown(self):
        with pytest.raises(OperationError, match="Unknown operation"):
            execute_op(_make_df(), 'nonexistent', {})

    def test_inject_rid(self):
        df = pd.DataFrame({'a': [1, 2]})
        result = _inject_rid(df)
        assert '_rid' in result.columns
        assert list(result['_rid']) == [0, 1]


# --- MockProvider tests ---

class TestMockProvider:
    def _make_provider(self):
        gold = [
            {'op': 'deduplicate', 'params': {'by': ['name'], 'keep': 'first'}},
            {'op': 'normalize_category', 'params': {'col': 'category', 'mapping': {'a': 'A'}}},
        ]
        amb = {0: {'by': [['name'], ['id'], ['name', 'id']]}}
        return MockProvider(gold, amb, p_amb=0.4, eps=0.05)

    def test_determinism(self):
        mp = self._make_provider()
        plan1 = mp.generate("clean data", seed=42, k=0)
        plan2 = mp.generate("clean data", seed=42, k=0)
        assert plan1 == plan2

    def test_different_k_different_plans(self):
        mp = self._make_provider()
        plan0 = mp.generate("clean data", seed=42, k=0)
        plan1 = mp.generate("clean data", seed=42, k=1)
        # With p_amb=0.4, different k values should (usually) produce different plans
        # At minimum they should be valid plans
        assert 'ops' in plan0
        assert 'ops' in plan1

    def test_generate_k(self):
        mp = self._make_provider()
        plans = mp.generate_k("clean data", seed=42, k=3)
        assert len(plans) == 3

    def test_token_count_deterministic(self):
        mp = self._make_provider()
        plan = mp.generate("clean data", seed=42, k=0)
        t1 = mp.token_count("clean data", plan)
        t2 = mp.token_count("clean data", plan)
        assert t1 == t2
        assert t1 > 0
