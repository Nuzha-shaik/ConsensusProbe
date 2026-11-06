"""Data cleaning operations: pure, copy-on-write, return (new_df, Patch)."""
from __future__ import annotations
import json
from typing import Any, Callable
import pandas as pd
from .patch import Patch


class OperationError(Exception):
    """Raised for unknown ops or bad params."""
    pass


def _inject_rid(df: pd.DataFrame) -> pd.DataFrame:
    """Add _rid column if not present."""
    if '_rid' not in df.columns:
        result = df.copy()
        result.insert(0, '_rid', range(len(result)))
        return result
    return df


def _drop_rid(df: pd.DataFrame) -> pd.DataFrame:
    """Remove _rid column for export."""
    if '_rid' in df.columns:
        return df.drop(columns=['_rid'])
    return df


def deduplicate(df: pd.DataFrame, by: list[str], keep: str = 'first') -> tuple[pd.DataFrame, Patch]:
    """Remove duplicate rows. Returns (new_df, patch)."""
    if keep not in ('first', 'last', False):
        raise OperationError(f"deduplicate: invalid keep={keep}")
    for col in by:
        if col not in df.columns:
            raise OperationError(f"deduplicate: column '{col}' not found")

    mask = df.duplicated(subset=by, keep=keep)
    deleted_rids = tuple(sorted(df.loc[mask, '_rid'].tolist()))
    result = df[~mask].copy()
    patch = Patch.create(deleted_rids=deleted_rids)
    return result, patch


def normalize_category(df: pd.DataFrame, col: str, mapping: dict[str, str]) -> tuple[pd.DataFrame, Patch]:
    """Normalize category values via mapping. Unmapped values stay."""
    if col not in df.columns:
        raise OperationError(f"normalize_category: column '{col}' not found")

    result = df.copy()
    if col in result.columns:
        result[col] = result[col].astype(object)
    cell_edits = {}
    for idx, row in result.iterrows():
        old_val = row[col]
        if isinstance(old_val, str) and old_val in mapping:
            new_val = mapping[old_val]
            if old_val != new_val:
                cell_edits[(row['_rid'], col)] = new_val
                result.at[idx, col] = new_val
    patch = Patch.create(cell_edits=cell_edits)
    return result, patch


def recalculate(df: pd.DataFrame, target: str, formula: str, source_cols: list[str]) -> tuple[pd.DataFrame, Patch]:
    """Recalculate a column. formula is a Python expression using col names as variables."""
    for c in source_cols:
        if c not in df.columns:
            raise OperationError(f"recalculate: source column '{c}' not found")

    result = df.copy()
    if target in result.columns:
        result[target] = result[target].astype(object)
    cell_edits = {}
    for idx, row in result.iterrows():
        local_vars = {c: row[c] for c in source_cols}
        try:
            # Safe eval: only allow arithmetic on known columns
            new_val = _safe_eval(formula, local_vars)
        except Exception as e:
            raise OperationError(f"recalculate: formula error at rid {row['_rid']}: {e}")
        old_val = row.get(target)
        if target not in result.columns or old_val != new_val:
            cell_edits[(row['_rid'], target)] = new_val
            result.at[idx, target] = new_val
    patch = Patch.create(cell_edits=cell_edits)
    return result, patch


def _safe_eval(formula: str, variables: dict) -> Any:
    """Evaluate arithmetic formula with AST evaluation without using eval()."""
    import ast
    import operator

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, str, bool)):
                return node.value
            raise OperationError(f"Unsupported constant type: {type(node.value)}")
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            raise OperationError(f"Disallowed or unknown variable in formula: {node.id}")
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in operators:
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                return operators[op_type](left, right)
            raise OperationError(f"Unsupported binary operator: {op_type}")
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in operators:
                operand = _eval_node(node.operand)
                return operators[op_type](operand)
            raise OperationError(f"Unsupported unary operator: {op_type}")
        raise OperationError(f"Unsupported expression element: {type(node).__name__}")

    try:
        tree = ast.parse(formula, mode='eval')
        return _eval_node(tree)
    except Exception as e:
        if isinstance(e, OperationError):
            raise
        raise OperationError(f"Failed to evaluate formula '{formula}': {e}")


def handle_missing(df: pd.DataFrame, col: str, strategy: str) -> tuple[pd.DataFrame, Patch]:
    """Handle missing values. strategy: drop, fill_mean, fill_median, fill_mode, fill:<value>."""
    if col not in df.columns:
        raise OperationError(f"handle_missing: column '{col}' not found")

    result = df.copy()
    null_mask = result[col].isna()

    if strategy == 'drop':
        deleted_rids = tuple(sorted(result.loc[null_mask, '_rid'].tolist()))
        result = result[~null_mask].copy()
        return result, Patch.create(deleted_rids=deleted_rids)

    if strategy == 'fill_mean':
        fill_val = result[col].mean()
        if pd.isna(fill_val):
            raise OperationError(f"handle_missing: column '{col}' is empty; fill_mean yields NaN")
    elif strategy == 'fill_median':
        fill_val = result[col].median()
        if pd.isna(fill_val):
            raise OperationError(f"handle_missing: column '{col}' is empty; fill_median yields NaN")
    elif strategy == 'fill_mode':
        mode = result[col].mode()
        if len(mode) == 0:
            raise OperationError(f"handle_missing: column '{col}' is empty; fill_mode yields no value")
        fill_val = mode.iloc[0]
    elif strategy.startswith('fill:'):
        fill_val = strategy[5:]
    else:
        raise OperationError(f"handle_missing: unknown strategy '{strategy}'")

    cell_edits = {}
    for idx in result.index[null_mask]:
        rid = result.at[idx, '_rid']
        cell_edits[(rid, col)] = fill_val
    result[col] = result[col].fillna(fill_val)
    return result, Patch.create(cell_edits=cell_edits)


def convert_type(df: pd.DataFrame, col: str, dtype: str) -> tuple[pd.DataFrame, Patch]:
    """Convert column type. dtype: int, float, str."""
    if col not in df.columns:
        raise OperationError(f"convert_type: column '{col}' not found")

    type_map = {'int': int, 'float': float, 'str': str}
    if dtype not in type_map:
        raise OperationError(f"convert_type: unknown dtype '{dtype}'")

    result = df.copy()
    if col in result.columns:
        result[col] = result[col].astype(object)
    cell_edits = {}
    for idx, row in result.iterrows():
        old_val = row[col]
        try:
            new_val = type_map[dtype](old_val) if pd.notna(old_val) else old_val
        except (ValueError, TypeError):
            new_val = old_val  # can't convert, leave as-is
        # M4: compare actual values, not repr strings (numpy int repr can differ from int repr)
        if type(old_val) is not type(new_val) or old_val != new_val:
            cell_edits[(row['_rid'], col)] = new_val
            result.at[idx, col] = new_val
    return result, Patch.create(cell_edits=cell_edits)


# Operation registry
OPERATIONS: dict[str, dict] = {
    'deduplicate': {
        'fn': deduplicate,
        'params_schema': {
            'by': {'type': 'array', 'items': {'type': 'string'}},
            'keep': {'type': 'string', 'enum': ['first', 'last', False], 'default': 'first'},
        },
    },
    'normalize_category': {
        'fn': normalize_category,
        'params_schema': {
            'col': {'type': 'string'},
            'mapping': {'type': 'object'},
        },
    },
    'recalculate': {
        'fn': recalculate,
        'params_schema': {
            'target': {'type': 'string'},
            'formula': {'type': 'string'},
            'source_cols': {'type': 'array', 'items': {'type': 'string'}},
        },
    },
    'handle_missing': {
        'fn': handle_missing,
        'params_schema': {
            'col': {'type': 'string'},
            'strategy': {'type': 'string'},
        },
    },
    'convert_type': {
        'fn': convert_type,
        'params_schema': {
            'col': {'type': 'string'},
            'dtype': {'type': 'string', 'enum': ['int', 'float', 'str']},
        },
    },
}


def execute_op(df: pd.DataFrame, op_name: str, params: dict) -> tuple[pd.DataFrame, Patch]:
    """Execute a named operation. Raises OperationError on unknown op or bad params."""
    if op_name not in OPERATIONS:
        raise OperationError(f"Unknown operation: {op_name}")
    fn = OPERATIONS[op_name]['fn']
    return fn(df, **params)
