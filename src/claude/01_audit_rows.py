"""Audit the raw row-level panel before any analysis.

Establishes the true unit of observation, documents identifier cardinality,
missingness, duplicate patterns and quality flags, and writes audit tables to
outputs/claude/tables/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import load_rows, write_table

# load the raw subsidiary-financial-statement rows exactly as delivered
df_row = load_rows()

# blank strings are the Stata representation of missing text, so treat them as such
str_col_list = [c for c in df_row.columns if df_row[c].dtype == object]
df_row[str_col_list] = df_row[str_col_list].replace(r"^\s*$", np.nan, regex=True)


# GOAL: DOCUMENT CARDINALITY AND MISSINGNESS FOR EVERY VARIABLE

# build one audit row per variable with type, uniqueness and missingness
df_varaudit = pd.DataFrame(
    {
        "variable": df_row.columns,
        "dtype": [str(df_row[c].dtype) for c in df_row.columns],
        "n_unique": [df_row[c].nunique(dropna=True) for c in df_row.columns],
        "n_missing": [int(df_row[c].isna().sum()) for c in df_row.columns],
    }
)

# express missingness as a share so variables of different types are comparable
df_varaudit["pct_missing"] = (100 * df_varaudit.n_missing / len(df_row)).round(1)

# record an example non-missing value to make the audit table readable
df_varaudit["example"] = [
    str(df_row[c].dropna().iloc[0])[:60] if df_row[c].notna().any() else ""
    for c in df_row.columns
]

write_table(df_varaudit, "audit_variables")


# GOAL: ESTABLISH THE UNIT OF OBSERVATION

# count how many rows share each candidate key to find the true identifier
key_list = [
    ["target_id"],
    ["target_id", "fiscal_year"],
    ["parent", "entity_name"],
    ["uin", "entity_name"],
    ["entity_name"],
]
audit_key_list = []
for key in key_list:
    s_size = df_row.groupby(key, dropna=False).size()
    audit_key_list.append(
        {
            "key": " x ".join(key),
            "n_groups": len(s_size),
            "max_rows_per_group": int(s_size.max()),
            "pct_groups_unique": round(100 * (s_size == 1).mean(), 1),
        }
    )
write_table(pd.DataFrame(audit_key_list), "audit_keys")


# GOAL: CONFIRM THAT STRUCTURAL VARIABLES ARE CONSTANT WITHIN A TARGET

# any variation within target_id would break the entity-level collapse
struct_col_list = [
    "parent", "level", "entity_name", "entity_country", "immediate_parent",
    "immediate_parent_country", "stake", "sector_code", "sector_label", "uin",
    "shared_uin", "n_top30_claimants", "attribution_rule",
]
df_struct = pd.DataFrame(
    {
        "variable": struct_col_list,
        "n_targets_with_variation": [
            int((df_row.groupby("target_id")[c].nunique(dropna=False) > 1).sum())
            for c in struct_col_list
        ],
    }
)
write_table(df_struct, "audit_structural_invariance")


# GOAL: SUMMARISE SOURCE QUALITY AND VALIDATION FLAGS

# cross the quality tier against the valuation-readiness flag
df_tier = pd.crosstab(df_row.data_quality_tier, df_row.ready_for_valuation)
df_tier.columns = [f"ready_for_valuation_{c}" for c in df_tier.columns]
write_table(df_tier.reset_index(), "audit_quality_tier")

# split the semicolon-separated review reasons into one flag per reason
s_reason = df_row.review_reason.fillna("none").str.split(";").explode().str.strip()
df_reason = s_reason.value_counts().rename_axis("review_reason").reset_index(name="n_rows")
df_reason["pct_rows"] = (100 * df_reason.n_rows / len(df_row)).round(1)
write_table(df_reason, "audit_review_reasons")


# GOAL: DOCUMENT THE CURRENCY AND UNITS PROBLEM FOR FINANCIAL VARIABLES

# financial magnitudes are only comparable within a currency, so cross the two
df_cur = pd.crosstab(
    df_row.currency.fillna("(missing)"), df_row.units.fillna("(missing)")
)
write_table(df_cur.reset_index(), "audit_currency_units")

# report coverage of every financial variable on the preferred-row subsample
fin_col_list = [
    "total_assets", "total_liabilities", "equity", "share_capital",
    "reserves_surplus", "turnover", "profit_before_tax", "provision_tax",
    "profit_after_tax", "cash_flow_operating", "cash_flow_investing",
    "cash_flow_financing", "cash_end", "dividends_paid", "interest_paid",
    "issue_share_capital", "proceeds_borrowings", "repayment_borrowings",
    "shareholding_percent",
]
df_pref = df_row[df_row.preferred_for_target_year == 1]
df_fincov = pd.DataFrame(
    {
        "variable": fin_col_list,
        "pct_nonmissing_all_rows": (100 * df_row[fin_col_list].notna().mean()).round(1),
        "pct_nonmissing_preferred": (100 * df_pref[fin_col_list].notna().mean()).round(1),
    }
).reset_index(drop=True)
write_table(df_fincov, "audit_financial_coverage")

print("wrote row-level audit tables")
print("rows:", len(df_row), " unique target_id:", df_row.target_id.nunique())
print("unique uin:", df_row.uin.nunique(), " unique parent:", df_row.parent.nunique())
