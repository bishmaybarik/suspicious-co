"""Independently reproduce the strongest findings on Codex's branch.

Every statistic here is recomputed from the immutable input using Claude's own
entity, edge and path tables. Nothing is copied from Codex's code or outputs;
only the numeric claims in research/codex/FINDINGS.md are used as targets.
Reviewed commit: bb67b9331f54eb7b9bfe9070c962f5664337c777.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, load_rows, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")
df_edge = pd.read_parquet(derived_path / "edge.parquet")
df_row = load_rows()

# blanks are missing text in the Stata export
str_col_list = [c for c in df_row.columns if df_row[c].dtype == object]
df_row[str_col_list] = df_row[str_col_list].replace(r"^\s*$", np.nan, regex=True)

check_row_list = []


def record(finding, claim, codex_value, claude_value, note=""):
    """Append one reproduction attempt to the review ledger."""

    check_row_list.append(
        {
            "finding": finding,
            "claim": claim,
            "codex_value": codex_value,
            "claude_value": claude_value,
            "note": note,
        }
    )


# GOAL: X-F001 - RAW ROWS MISWEIGHT PARENTS RELATIVE TO ENTITIES

s_row_share = 100 * df_row.parent.value_counts() / len(df_row)
s_ent_share = 100 * df_entity.parent.value_counts() / len(df_entity)

for parent_name in ["TATA COMMUNICATIONS LIMITED", "SAMVARDHANA MOTHERSON INTERNATI"]:
    record(
        "X-F001",
        f"{parent_name}: raw-row share vs entity share",
        "14.70% vs 2.68% (TataComm); 8.87% vs 16.89% (Motherson)",
        f"{s_row_share[parent_name]:.2f}% vs {s_ent_share[parent_name]:.2f}%",
        f"raw rows = {int(df_row.parent.value_counts()[parent_name])}",
    )

# the ratio of the two shares is the misweighting factor Codex reports
df_weight = pd.DataFrame({"raw_row_share": s_row_share, "entity_share": s_ent_share})
df_weight["ratio"] = (df_weight.raw_row_share / df_weight.entity_share).round(2)
df_weight["n_rows"] = df_row.parent.value_counts()
df_weight["n_entities"] = df_entity.parent.value_counts()
write_table(df_weight.sort_values("ratio", ascending=False).reset_index(names="parent"),
            "review_xf001_row_vs_entity_weighting")

record("X-F001", "top four parents' share of entities", "46.50%",
       f"{100 * s_ent_share.nlargest(4).sum() / 100:.2f}%".replace("0.", "")
       if False else f"{s_ent_share.nlargest(4).sum():.2f}%")


# GOAL: X-F006 - DEEP HIERARCHY AND DEEP MANUFACTURING ARE PARENT-DRIVEN

df_deep = df_entity[df_entity.level >= 5]
record("X-F006", "targets at reported level 5+", "342",
       f"{len(df_deep)}")
record("X-F006", "Motherson share of level-5+ targets", "211/342 = 61.70%",
       f"{int((df_deep.parent == 'SAMVARDHANA MOTHERSON INTERNATI').sum())}/{len(df_deep)} = "
       f"{100 * (df_deep.parent == 'SAMVARDHANA MOTHERSON INTERNATI').mean():.2f}%")
record("X-F006", "top-three parents' share of level-5+", "312/342 = 91.23%",
       f"{int(df_deep.parent.value_counts().nlargest(3).sum())}/{len(df_deep)} = "
       f"{100 * df_deep.parent.value_counts().nlargest(3).sum() / len(df_deep):.2f}%")

pooled_deep = 100 * (df_entity.level >= 5).mean()
equal_deep = 100 * df_entity.groupby("parent").apply(
    lambda d: (d.level >= 5).mean(), include_groups=False).mean()
record("X-F006", "pooled vs equal-parent level-5+ share", "18.65% vs 7.34%",
       f"{pooled_deep:.2f}% vs {equal_deep:.2f}%")

# leave-one-parent-out on the pooled deep share
loo_deep_list = []
for parent_name in sorted(df_entity.parent.unique()):
    df_keep = df_entity[df_entity.parent != parent_name]
    loo_deep_list.append({"parent_dropped": parent_name,
                          "pooled_deep_share": round(100 * (df_keep.level >= 5).mean(), 2)})
df_loo_deep = pd.DataFrame(loo_deep_list)
record("X-F006", "leave-one-parent-out range for level-5+ share", "8.59% to 20.88%",
       f"{df_loo_deep.pooled_deep_share.min():.2f}% to {df_loo_deep.pooled_deep_share.max():.2f}%")
write_table(df_loo_deep.sort_values("pooled_deep_share"), "review_xf006_deep_leave_one_out")

df_mfg = df_entity[df_entity.sector_label == "Manufacturing (General)"]
record("X-F006", "manufacturing entities at level 5+", "242/508 = 47.64%",
       f"{int((df_mfg.level >= 5).sum())}/{len(df_mfg)} = {100 * (df_mfg.level >= 5).mean():.2f}%")
df_mfg_deep = df_mfg[df_mfg.level >= 5]
record("X-F006", "Motherson + Hindalco share of deep manufacturing", "240/242 = 99.17%",
       f"{int(df_mfg_deep.parent.isin(['SAMVARDHANA MOTHERSON INTERNATI', 'HINDALCO INDUSTRIES LIMITED']).sum())}"
       f"/{len(df_mfg_deep)}")
df_mfg_nomo = df_mfg[df_mfg.parent != "SAMVARDHANA MOTHERSON INTERNATI"]
record("X-F006", "manufacturing deep share dropping Motherson", "56/264 = 21.21%",
       f"{int((df_mfg_nomo.level >= 5).sum())}/{len(df_mfg_nomo)} = "
       f"{100 * (df_mfg_nomo.level >= 5).mean():.2f}%")


# GOAL: X-F007 - NETHERLANDS AND MAURITIUS AS PATH INTERMEDIARIES

# ancestry share counts a jurisdiction once for every path node it occupies,
# so a branching intermediary is counted once per descendant path
node_row_list = []
for row in df_entity.itertuples():
    for country in row.path_countries.split(" > "):
        node_row_list.append({"target_id": row.target_id, "parent": row.parent,
                              "node_country": country})
df_node = pd.DataFrame(node_row_list)

# Codex excludes the Indian root from "observed entity appearances"
df_node_foreign = df_node[~df_node.node_country.isin(["INDIA", "(UNOBSERVED)"])]

for country in ["NETHERLANDS", "MAURITIUS"]:
    ent_share = 100 * (df_entity.entity_country == country).mean()
    anc_share = 100 * (df_node_foreign.node_country == country).mean()
    record("X-F007", f"{country}: entity share vs path-appearance share",
           "6.01% vs 19.69% (NL); 3.11% vs 8.11% (MU)",
           f"{ent_share:.2f}% vs {anc_share:.2f}%",
           "path-appearance share uses Claude's complete paths, root excluded")

    # equal-parent weighting gives every group one vote
    ent_eq = 100 * df_entity.groupby("parent").apply(
        lambda d: (d.entity_country == country).mean(), include_groups=False).mean()
    anc_eq = 100 * df_node_foreign.groupby("parent").apply(
        lambda d: (d.node_country == country).mean(), include_groups=False).mean()
    record("X-F007", f"{country}: equal-parent entity vs appearance share",
           "7.97% vs 14.61% (NL); 3.65% vs 8.26% (MU)",
           f"{ent_eq:.2f}% vs {anc_eq:.2f}%")

# non-root children generated by nodes located in each jurisdiction
df_nonroot = df_edge[df_edge.parent_depth >= 0]
for country in ["NETHERLANDS", "MAURITIUS"]:
    df_from = df_nonroot[df_nonroot.parent_country == country]
    record("X-F007", f"{country}: children of nodes in this jurisdiction",
           "299 children, 75.59% cross-border (NL); 191, 85.34% (MU)",
           f"{len(df_from)} children, {100 * df_from.is_border_crossing.mean():.2f}% cross-border",
           f"{df_from.child_country.nunique()} destination jurisdictions, "
           f"{df_from.parent_bucket.nunique()} parent groups; "
           f"largest group supplies {100 * df_from.parent_bucket.value_counts().iloc[0] / len(df_from):.2f}%")

# the mechanical alternative: count each intermediary node once, not per path
df_unique_int = df_entity[df_entity.n_children > 0]
for country in ["NETHERLANDS", "MAURITIUS"]:
    record("X-F007", f"{country}: share of UNIQUE intermediary nodes",
           "not reported by Codex",
           f"{100 * (df_unique_int.entity_country == country).mean():.2f}% of {len(df_unique_int)}",
           "unique-node counting removes the per-descendant repetition")


# GOAL: X-F008 - MOST NON-ROOT EDGES CROSS JURISDICTIONS

# Codex's denominator is the 1,650 non-root target occurrences, i.e. every
# entity at level >= 1 paired with its recorded immediate parent
df_cross = df_entity[df_entity.level >= 1].copy()
df_cross["is_cross"] = (
    df_cross.entity_country != df_cross.immediate_parent_country
).astype(int)
record("X-F008", "non-root edges crossing jurisdictions", "951/1650 = 57.64%",
       f"{int(df_cross.is_cross.sum())}/{len(df_cross)} = {100 * df_cross.is_cross.mean():.2f}%",
       "uses the recorded immediate_parent_country, not the reconstructed graph")
record("X-F008", "equal-parent mean cross-border rate", "58.67%",
       f"{100 * df_cross.groupby('parent').is_cross.mean().mean():.2f}%")

loo_cross_list = []
for parent_name in sorted(df_cross.parent.unique()):
    df_keep = df_cross[df_cross.parent != parent_name]
    loo_cross_list.append({"parent_dropped": parent_name,
                           "cross_border_rate": round(100 * df_keep.is_cross.mean(), 2)})
df_loo_cross = pd.DataFrame(loo_cross_list)
record("X-F008", "leave-one-parent-out range", "56.06% to 61.78%",
       f"{df_loo_cross.cross_border_rate.min():.2f}% to {df_loo_cross.cross_border_rate.max():.2f}%")
write_table(df_loo_cross.sort_values("cross_border_rate"), "review_xf008_cross_border_leave_one_out")


# GOAL: X-F010 - ZERO MAPPING STAKES ARE NOT LITERAL ZERO OWNERSHIP

record("X-F010", "level-0 targets with missing stake", "184/184",
       f"{int(df_entity[df_entity.level == 0].stake.isna().sum())}/"
       f"{int((df_entity.level == 0).sum())}")
df_nonroot_ent = df_entity[df_entity.level >= 1]
record("X-F010", "non-root targets with stake exactly zero", "406/1650 = 24.61%",
       f"{int((df_nonroot_ent.stake == 0).sum())}/{len(df_nonroot_ent)} = "
       f"{100 * (df_nonroot_ent.stake == 0).mean():.2f}%")

# the decisive check: rows carrying both the mapping stake and an AOC-1 share
df_both = df_row[
    (df_row.preferred_for_target_year == 1)
    & df_row.stake.notna()
    & df_row.shareholding_percent.notna()
].copy()
record("X-F010", "preferred rows with both stake and AOC shareholding", "45",
       f"{len(df_both)}")
df_contra = df_both[(df_both.stake == 0) & (df_both.shareholding_percent > 0)]
record("X-F010", "rows with stake zero but positive AOC shareholding", "7",
       f"{len(df_contra)}",
       "AOC values: " + ", ".join(f"{v:.2f}" for v in sorted(df_contra.shareholding_percent)))
record("X-F010", "rows where the two measures differ by over 1pp", "8",
       f"{int((df_both.stake - df_both.shareholding_percent).abs().gt(1).sum())}")
write_table(
    df_both[["parent", "entity_name", "level", "stake", "shareholding_percent",
             "aoc_company_name", "fiscal_year"]].sort_values(["stake", "shareholding_percent"]),
    "review_xf010_stake_vs_aoc",
)


# GOAL: X-F012 - READY ROWS STILL NEED SIGN, UNIT AND P&L GATES

df_ready = df_row[df_row.ready_for_valuation == 1]
record("X-F012", "ready preferred target-year rows", "560", f"{len(df_ready)}")

# basic plausibility: assets strictly positive and liabilities non-negative
s_basic = (df_ready.total_assets > 0) & (df_ready.total_liabilities >= 0)
record("X-F012", "ready rows failing the basic sign gate", "39/560 = 6.96%",
       f"{int((~s_basic).sum())}/{len(df_ready)} = {100 * (~s_basic).mean():.2f}%")
record("X-F012", "ready rows with negative total_assets", "3",
       f"{int((df_ready.total_assets < 0).sum())}")
record("X-F012", "ready rows with negative total_liabilities", "38",
       f"{int((df_ready.total_liabilities < 0).sum())}")
record("X-F012", "ready rows with a testable and valid P&L identity", "105/560 = 18.75%",
       f"{int((df_ready.pl_identity_ok == 1).sum())}/{len(df_ready)} = "
       f"{100 * (df_ready.pl_identity_ok == 1).mean():.2f}%")
record("X-F012", "ready rows with blank units", "516/560 = 92.14%",
       f"{int(df_ready.units.isna().sum())}/{len(df_ready)} = "
       f"{100 * df_ready.units.isna().mean():.2f}%")

df_basic = df_ready[s_basic]
record("X-F012", "negative equity within the basic-plausible sample", "127/521 = 24.38%",
       f"{int((df_basic.equity < 0).sum())}/{len(df_basic)} = "
       f"{100 * (df_basic.equity < 0).mean():.2f}%")
record("X-F012", "equal-parent negative-equity rate", "18.98%",
       f"{100 * df_basic.groupby('parent').apply(lambda d: (d.equity < 0).mean(), include_groups=False).mean():.2f}%")

df_pl = df_ready[df_ready.pl_identity_ok == 1]
record("X-F012", "loss-making rows in the P&L-valid sample", "36/105 = 34.29%",
       f"{int((df_pl.profit_after_tax < 0).sum())}/{len(df_pl)} = "
       f"{100 * (df_pl.profit_after_tax < 0).mean():.2f}%")


# GOAL: X-F017 - REPEATED PARSED BALANCE-SHEET SIGNATURES

df_parsed = df_row[
    (df_row.preferred_for_target_year == 1)
    & df_row.total_assets.notna()
    & df_row.total_liabilities.notna()
    & df_row.equity.notna()
].copy()
record("X-F017", "preferred rows with all three core balance variables", "863",
       f"{len(df_parsed)}")

sig_col_list = ["fiscal_year", "currency", "units", "total_assets",
                "total_liabilities", "equity"]
s_sig = df_parsed.groupby(sig_col_list, dropna=False).size()
s_dup = s_sig[s_sig > 1]
record("X-F017", "repeated balance-sheet signatures", "51 signatures, 104 rows",
       f"{len(s_dup)} signatures, {int(s_dup.sum())} rows "
       f"({100 * s_dup.sum() / len(df_parsed):.2f}%)")

# whether a repeat spans parents decides between alias and extraction reuse
df_parsed["sig_key"] = df_parsed[sig_col_list].astype(str).agg("|".join, axis=1)
df_dupsig = df_parsed[df_parsed.sig_key.isin(
    df_parsed.sig_key.value_counts()[lambda s: s > 1].index)]
df_sig_detail = df_dupsig.groupby("sig_key").agg(
    n_rows=("target_id", "size"),
    n_parents=("parent", "nunique"),
    n_entities=("entity_name", "nunique"),
    n_source_urls=("source_url", "nunique"),
    equity=("equity", "first"),
    total_assets=("total_assets", "first"),
    currency=("currency", "first"),
).reset_index(drop=True)
record("X-F017", "repeated signatures spanning more than one parent",
       "not reported by Codex",
       f"{int((df_sig_detail.n_parents > 1).sum())} of {len(df_sig_detail)}")
record("X-F017", "repeated signatures where equity and assets are both zero",
       "not reported by Codex",
       f"{int(((df_sig_detail.equity == 0) & (df_sig_detail.total_assets == 0)).sum())}")
write_table(df_sig_detail.sort_values("n_rows", ascending=False),
            "review_xf017_duplicate_signatures")


# GOAL: X-F014 - US CONCENTRATION UNDER ALTERNATIVE DENOMINATORS

record("X-F014", "US share of entities", "363/1830 = 19.84%",
       f"{int((df_entity.entity_country == 'UNITED STATES OF AMERICA').sum())}/{len(df_entity)} = "
       f"{100 * (df_entity.entity_country == 'UNITED STATES OF AMERICA').mean():.2f}%")
record("X-F014", "US raw-row share", "17.00%",
       f"{100 * (df_row.entity_country == 'UNITED STATES OF AMERICA').mean():.2f}%")
record("X-F014", "US equal-parent entity share", "16.02%",
       f"{100 * df_entity.groupby('parent').apply(lambda d: (d.entity_country == 'UNITED STATES OF AMERICA').mean(), include_groups=False).mean():.2f}%")

df_l1 = df_entity[df_entity.level == 1]
df_l1_us = df_l1[df_l1.entity_country == "UNITED STATES OF AMERICA"]
record("X-F014", "US share of level-1 entities", "188/779 = 24.13%",
       f"{len(df_l1_us)}/{len(df_l1)} = {100 * len(df_l1_us) / len(df_l1):.2f}%")
record("X-F014", "Reliance share of US level-1 entities", "52.66%",
       f"{100 * (df_l1_us.parent == 'RELIANCE INDUSTRIES LTD').mean():.2f}%")

df_leaf_us = df_entity[
    (df_entity.is_leaf == 1) & (df_entity.path_collapsed == "INDIA > UNITED STATES OF AMERICA")
]
record("X-F014", "leaf paths of the form India -> US -> US", "158 paths, Reliance 61.39%",
       f"{len(df_leaf_us)} leaf paths, Reliance {100 * (df_leaf_us.parent == 'RELIANCE INDUSTRIES LTD').mean():.2f}%",
       "collapsed path, so India > US covers any number of US hops")

write_table(pd.DataFrame(check_row_list), "review_codex_reproduction_ledger")

print(pd.DataFrame(check_row_list).to_string(index=False))
