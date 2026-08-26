"""Shared paths and loaders for Claude's blind-discovery analysis.

Every script in src/claude/ imports paths and the canonical row-level panel
from here so that file locations are defined in exactly one place.
"""

from pathlib import Path

import pandas as pd

# immutable read-only research inputs supplied by the controller
input_path = Path.home() / ".agent-inputs" / "suspicious-co"
dta_path = input_path / "subsidiary_financial_variables_refined.dta"
dict_path = input_path / "subsidiary_financial_variables_refined_data_dictionary.txt"

# worktree root inferred from this file's location, never from the cwd
root_path = Path(__file__).resolve().parents[2]

# output locations for tables, figures and derived analytical datasets
out_path = root_path / "outputs" / "claude"
tab_path = out_path / "tables"
fig_path = out_path / "figures"
derived_path = out_path / "derived"
research_path = root_path / "research" / "claude"

# create output directories on import so scripts never fail on a fresh clone
for _dir_path in (tab_path, fig_path, derived_path, research_path):
    _dir_path.mkdir(parents=True, exist_ok=True)


def load_rows():
    """Return the raw subsidiary-financial-statement row panel, unmodified."""

    # read without categorical conversion so string labels stay as text
    return pd.read_stata(dta_path, convert_categoricals=False)


def write_table(df_table, name, index=False):
    """Write a table to outputs/claude/tables as both markdown and csv."""

    # markdown is committed; csv is gitignored but useful for local reuse
    (tab_path / f"{name}.md").write_text(df_table.to_markdown(index=index))
    df_table.to_csv(tab_path / f"{name}.csv", index=index)
