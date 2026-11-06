"""Regression tests for audit batch B3: H3, M4, L1, L2."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
import pytest
from research.operations import (
    handle_missing, deduplicate, convert_type, OperationError, OPERATIONS
)


def _df_with_rid(data):
    df = pd.DataFrame(data)
    df.insert(0, '_rid', range(len(df)))
    return df


# H3: fill_mean/fill_median on empty column raises OperationError
def test_h3_fill_mean_empty_raises():
    df = _df_with_rid({'val': [None, None]})
    df['val'] = df['val'].astype(float)
    with pytest.raises(OperationError, match="empty"):
        handle_missing(df, 'val', 'fill_mean')


def test_h3_fill_median_empty_raises():
    df = _df_with_rid({'val': [None, None]})
    df['val'] = df['val'].astype(float)
    with pytest.raises(OperationError, match="empty"):
        handle_missing(df, 'val', 'fill_median')


# L1: fill_mode on empty column raises OperationError
def test_l1_fill_mode_empty_raises():
    df = _df_with_rid({'val': pd.Series([], dtype=float)})
    with pytest.raises(OperationError, match="empty"):
        handle_missing(df, 'val', 'fill_mode')


# M4: repr-based change detection wrong for numpy int
def test_m4_numpy_int_detected():
    df = _df_with_rid({'val': [np.int64(3)]})
    result_df, patch = convert_type(df, 'val', 'str')
    edits = patch.cell_edits_dict()
    # np.int64(3) -> str('3'): repr differs, change must be recorded
    assert (0, 'val') in edits, "M4: convert_type must record numpy int → str change"
    assert edits[(0, 'val')] == '3'


def test_m4_no_false_change():
    """Already a str shouldn't create an edit."""
    df = _df_with_rid({'val': ['hello']})
    result_df, patch = convert_type(df, 'val', 'str')
    # str('hello') == 'hello': no spurious edit
    edits = patch.cell_edits_dict()
    assert (0, 'val') not in edits, "M4: no spurious edit when value already correct type"


# L2: deduplicate schema includes keep=False
def test_l2_schema_has_keep_false():
    schema = OPERATIONS['deduplicate']['params_schema']
    keep_enum = schema['keep']['enum']
    assert False in keep_enum, "L2: deduplicate schema must include keep=False"


def test_l2_deduplicate_keep_false_works():
    df = _df_with_rid({'a': [1, 1, 2], 'b': ['x', 'x', 'y']})
    result, patch = deduplicate(df, by=['a', 'b'], keep=False)
    # keep=False removes ALL duplicates
    assert len(result) == 1  # only (2, 'y') survives
    assert result.iloc[0]['a'] == 2
