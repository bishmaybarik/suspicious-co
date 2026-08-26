"""Analyse extraction coverage and the thin financial layer of the panel.

Coverage is treated as a first-class result because it determines which
entities any later OFBV valuation can actually see. Financial results are
reported as tentative because of currency mixing and small samples.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")


# GOAL: DOCUMENT HOW COVERAGE VARIES WITH DEPTH AND JURISDICTION

df_cov_depth = df_entity.groupby("level").agg(
    n_entities=("target_id", "size"),
    pct_any_source_found=("any_source_found", lambda s: round(100 * s.mean(), 1)),
    pct_variables_parsed=("any_variables_parsed", lambda s: round(100 * s.mean(), 1)),
    pct_ready_for_valuation=("any_ready_for_valuation", lambda s: round(100 * s.mean(), 1)),
).reset_index()
write_table(df_cov_depth, "coverage_by_level")

df_cov_country = df_entity.groupby("entity_country").agg(
    n_entities=("target_id", "size"),
    mean_level=("level", "mean"),
    pct_any_source_found=("any_source_found", lambda s: round(100 * s.mean(), 1)),
    pct_ready_for_valuation=("any_ready_for_valuation", lambda s: round(100 * s.mean(), 1)),
).round(2).reset_index()
df_cov_country = df_cov_country[df_cov_country.n_entities >= 15].sort_values(
    "pct_ready_for_valuation", ascending=False
)
write_table(df_cov_country, "coverage_by_country")

df_cov_parent = df_entity.groupby("parent").agg(
    n_entities=("target_id", "size"),
    pct_any_source_found=("any_source_found", lambda s: round(100 * s.mean(), 1)),
    pct_ready_for_valuation=("any_ready_for_valuation", lambda s: round(100 * s.mean(), 1)),
).sort_values("pct_ready_for_valuation", ascending=False).reset_index()
write_table(df_cov_parent, "coverage_by_parent")

cov_row_list = [
    {"statistic": "entities", "value": len(df_entity)},
    {"statistic": "entities with any source found",
     "value": int(df_entity.any_source_found.sum())},
    {"statistic": "pct with any source found",
     "value": round(100 * df_entity.any_source_found.mean(), 1)},
    {"statistic": "entities with a parsed balance sheet",
     "value": int(df_entity.equity.notna().sum())},
    {"statistic": "pct with a parsed balance sheet",
     "value": round(100 * df_entity.equity.notna().mean(), 1)},
    {"statistic": "entities valuation-ready in at least one year",
     "value": int(df_entity.any_ready_for_valuation.sum())},
    {"statistic": "pct valuation-ready",
     "value": round(100 * df_entity.any_ready_for_valuation.mean(), 1)},
]
write_table(pd.DataFrame(cov_row_list), "coverage_summary")


# GOAL: TEST WHETHER COVERAGE IS RANDOM WITH RESPECT TO STRUCTURE

# a simple linear probability model keeps the comparison transparent
df_lpm = df_entity[["any_ready_for_valuation", "level", "n_children", "parent"]].copy()
df_lpm["deep"] = (df_lpm.level >= 3).astype(int)
df_lpm["has_children"] = (df_lpm.n_children > 0).astype(int)

# within-parent differences remove any parent-level disclosure effect
df_lpm["parent_mean"] = df_lpm.groupby("parent").any_ready_for_valuation.transform("mean")
df_lpm["demeaned"] = df_lpm.any_ready_for_valuation - df_lpm.parent_mean

lpm_row_list = []
for group_col in ["deep", "has_children"]:
    for value in [0, 1]:
        df_cell = df_lpm[df_lpm[group_col] == value]
        lpm_row_list.append(
            {
                "split": group_col,
                "value": value,
                "n": len(df_cell),
                "raw_pct_ready": round(100 * df_cell.any_ready_for_valuation.mean(), 1),
                "within_parent_gap_pp": round(100 * df_cell.demeaned.mean(), 1),
            }
        )
write_table(pd.DataFrame(lpm_row_list), "coverage_selection_check")


# GOAL: COMPARE THE FINANCIAL SIGNATURE OF INTERMEDIARIES AND OPERATING ENTITIES

df_fin = df_entity[df_entity.equity.notna()].copy()

# turnover relative to assets separates operating businesses from holding shells
df_ratio = df_fin[
    df_fin.turnover.notna() & df_fin.total_assets.notna() & (df_fin.total_assets > 0)
].copy()
df_ratio["turnover_to_assets"] = df_ratio.turnover / df_ratio.total_assets
df_ratio["has_children"] = df_ratio.n_children > 0

df_sig = df_ratio.groupby("has_children").agg(
    n=("turnover_to_assets", "size"),
    median_turnover_to_assets=("turnover_to_assets", "median"),
    mean_turnover_to_assets=("turnover_to_assets", "mean"),
    pct_zero_turnover=("turnover", lambda s: round(100 * (s == 0).mean(), 1)),
).round(3).reset_index()
write_table(df_sig, "holding_vs_operating_financial_signature")

# the same comparison inside a single currency guards against unit mixing
df_sig_usd = df_ratio[df_ratio.currency == "USD"].groupby("has_children").agg(
    n=("turnover_to_assets", "size"),
    median_turnover_to_assets=("turnover_to_assets", "median"),
).round(3).reset_index()
write_table(df_sig_usd, "holding_vs_operating_signature_usd")

# negative equity is reported descriptively only; samples are small by country
df_neg = df_fin.groupby("entity_country").agg(
    n=("equity", "size"),
    pct_negative_equity=("equity", lambda s: round(100 * (s < 0).mean(), 1)),
).reset_index()
df_neg = df_neg[df_neg.n >= 10].sort_values("pct_negative_equity", ascending=False)
write_table(df_neg, "negative_equity_by_country")

print("coverage and financial analysis written")
print("pct valuation-ready:", round(100 * df_entity.any_ready_for_valuation.mean(), 1))
print("entities with parsed equity:", int(df_entity.equity.notna().sum()))
