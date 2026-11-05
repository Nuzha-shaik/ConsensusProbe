"""Patch: immutable record of edits to a DataFrame."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Patch:
    """Describes edits: deleted row IDs, cell edits, flagged rows."""
    deleted_rids: tuple[int, ...] = ()
    cell_edits: tuple[tuple[tuple[int, str], Any], ...] = ()  # sorted ((rid, col), value)
    flagged: tuple[tuple[int, str], ...] = ()  # sorted (rid, reason)

    @staticmethod
    def create(deleted_rids=None, cell_edits=None, flagged=None) -> Patch:
        d = tuple(sorted(deleted_rids or []))
        c = tuple(sorted(((k, v) for k, v in (cell_edits or {}).items()), key=lambda x: x[0]))
        f = tuple(sorted((flagged or {}).items()))
        return Patch(deleted_rids=d, cell_edits=c, flagged=f)

    def atoms(self) -> tuple:
        """Edit set E as sorted hashable atoms. Flags excluded."""
        atoms = []
        for rid in self.deleted_rids:
            atoms.append(("del", rid))
        for (rid, col), value in self.cell_edits:
            atoms.append(("edit", rid, col, repr(value)))
        return tuple(sorted(atoms))

    def cell_edits_dict(self) -> dict:
        return dict(self.cell_edits)

    def flagged_dict(self) -> dict:
        return dict(self.flagged)

    def apply(self, df):
        """Apply patch to DataFrame (must have _rid column). Returns new DataFrame."""
        import pandas as pd
        result = df.copy()
        if self.deleted_rids:
            result = result[~result['_rid'].isin(self.deleted_rids)].copy()
        edits = self.cell_edits_dict()
        for (rid, col), value in edits.items():
            mask = result['_rid'] == rid
            if mask.any():
                result.loc[mask, col] = value
        return result

    def merge(self, other: Patch) -> Patch:
        """Merge two patches. Later (other) wins on conflicts."""
        deleted = set(self.deleted_rids) | set(other.deleted_rids)
        edits = dict(self.cell_edits)
        edits.update(dict(other.cell_edits))
        flags = dict(self.flagged)
        flags.update(dict(other.flagged))
        return Patch.create(deleted_rids=deleted, cell_edits=edits, flagged=flags)
