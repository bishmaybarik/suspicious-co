"""Test whether corporate names predict network role, and whether layering
dilutes ownership.

Both analyses are new in increment 2. The stake work adopts the corrected
zero-stake rule established in research/reviews/X-F010.md: `stake == 0` is a
missing code, not a zero share.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import networkx as nx
import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")

# a punctuation-free uppercase name makes token matching unambiguous
s_name = (
    df_entity.entity_name.str.upper()
    .str.replace(r"[^A-Z0-9 ]", " ", regex=True)
    .str.split()
    .str.join(" ")
)


# GOAL: TEST WHETHER FUNCTION WORDS IN A NAME PREDICT HOLDING BEHAVIOUR

token_dict = {
    "holding or holdco": r"\bHOLDING\b|\bHOLDINGS\b|\bHOLDCO\b",
    "investment(s)": r"\bINVESTMENT\b|\bINVESTMENTS\b",
    "group": r"\bGROUP\b",
    "international": r"\bINTERNATIONAL\b",
    "venture(s)": r"\bVENTURE\b|\bVENTURES\b",
    "capital or finance": r"\bCAPITAL\b|\bFINANCE\b|\bFINANCIAL\b",
    "global": r"\bGLOBAL\b",
    "technolog-": r"\bTECHNOLOG",
    "manufactur-": r"\bMANUFACTUR",
    "trading or trade": r"\bTRADING\b|\bTRADE\b",
}

token_row_list = []
for label, pattern in token_dict.items():
    s_has = s_name.str.contains(pattern, regex=True)
    df_has = df_entity[s_has]
    token_row_list.append(
        {
            "name_token": label,
            "n_entities": int(s_has.sum()),
            "n_parents": int(df_has.parent.nunique()),
            "pct_holding_at_least_one": round(100 * (1 - df_has.is_leaf.mean()), 1),
            "mean_children": round(df_has.n_children.mean(), 2),
            "mean_descendants": round(df_has.n_descendants.mean(), 2),
            "mean_level": round(df_has.level.mean(), 2),
        }
    )

# the comparison group is every entity carrying none of the tokens
s_any = s_name.str.contains("|".join(token_dict.values()), regex=True)
df_none = df_entity[~s_any]
token_row_list.append(
    {
        "name_token": "(none of the above)",
        "n_entities": len(df_none),
        "n_parents": int(df_none.parent.nunique()),
        "pct_holding_at_least_one": round(100 * (1 - df_none.is_leaf.mean()), 1),
        "mean_children": round(df_none.n_children.mean(), 2),
        "mean_descendants": round(df_none.n_descendants.mean(), 2),
        "mean_level": round(df_none.level.mean(), 2),
    }
)
write_table(pd.DataFrame(token_row_list).sort_values(
    "pct_holding_at_least_one", ascending=False), "name_tokens_vs_role")


# GOAL: TEST THE SAME FOR THE LEGAL FORM SUFFIX

form_dict = {
    "B.V. (Netherlands)": r"\bB V\b|\bBV\b",
    "Pte Ltd (Singapore)": r"\bPTE\b",
    "S.A.R.L. (Lux/France)": r"\bSARL\b|\bS A R L\b",
    "GmbH (Germany)": r"\bGMBH\b",
    "Inc (United States)": r"\bINC\b",
    "Ltd or Limited": r"\bLTD\b|\bLIMITED\b",
    "S.A.": r"\bSA\b",
    "Pty (Australia/South Africa)": r"\bPTY\b",
    "LLC (United States)": r"\bLLC\b",
}
form_row_list = []
for label, pattern in form_dict.items():
    s_has = s_name.str.contains(pattern, regex=True)
    if s_has.sum() < 15:
        continue
    df_has = df_entity[s_has]
    form_row_list.append(
        {
            "legal_form": label,
            "n_entities": int(s_has.sum()),
            "pct_holding_at_least_one": round(100 * (1 - df_has.is_leaf.mean()), 1),
            "mean_level": round(df_has.level.mean(), 2),
            "mean_descendants": round(df_has.n_descendants.mean(), 2),
            "modal_country": df_has.entity_country.value_counts().index[0],
            "pct_in_modal_country": round(
                100 * df_has.entity_country.value_counts().iloc[0] / len(df_has), 1),
        }
    )
write_table(pd.DataFrame(form_row_list).sort_values(
    "pct_holding_at_least_one", ascending=False), "legal_form_vs_role")


# GOAL: TEST WHETHER THE NAME SIGNAL SURVIVES PARENT AND COUNTRY CONTROLS

df_entity["has_holding_name"] = s_name.str.contains(
    r"\bHOLDING\b|\bHOLDINGS\b|\bHOLDCO\b|\bINVESTMENT\b|\bINVESTMENTS\b", regex=True)
df_entity["is_holder"] = 1 - df_entity.is_leaf

# demeaning within parent x country removes both group style and local naming law
df_entity["cell_mean"] = df_entity.groupby(
    ["parent", "entity_country"]).is_holder.transform("mean")
df_entity["demeaned_holder"] = df_entity.is_holder - df_entity.cell_mean

s_flag = df_entity.has_holding_name
name_row_list = [
    {"statistic": "entities with a holding-type name", "value": int(s_flag.sum())},
    {"statistic": "parents represented", "value": int(df_entity[s_flag].parent.nunique())},
    {"statistic": "pct that hold at least one subsidiary (holding name)",
     "value": round(100 * df_entity[s_flag].is_holder.mean(), 1)},
    {"statistic": "pct that hold at least one subsidiary (other names)",
     "value": round(100 * df_entity[~s_flag].is_holder.mean(), 1)},
    {"statistic": "raw gap in percentage points",
     "value": round(100 * (df_entity[s_flag].is_holder.mean()
                           - df_entity[~s_flag].is_holder.mean()), 1)},
    {"statistic": "gap within parent x country cells, percentage points",
     "value": round(100 * (df_entity[s_flag].demeaned_holder.mean()
                           - df_entity[~s_flag].demeaned_holder.mean()), 1)},
    {"statistic": "precision: holders among holding-named entities",
     "value": round(100 * df_entity[s_flag].is_holder.mean(), 1)},
    {"statistic": "recall: holding-named among all holders",
     "value": round(100 * s_flag[df_entity.is_holder == 1].mean(), 1)},
]

# leave-one-parent-out on the raw gap
loo_gap_list = []
for parent_name in df_entity.parent.unique():
    df_keep = df_entity[df_entity.parent != parent_name]
    s_keep = df_keep.has_holding_name
    if s_keep.sum() == 0:
        continue
    loo_gap_list.append(100 * (df_keep[s_keep].is_holder.mean()
                               - df_keep[~s_keep].is_holder.mean()))
name_row_list.append({"statistic": "leave-one-parent-out range of the raw gap",
                      "value": f"{min(loo_gap_list):.1f} to {max(loo_gap_list):.1f}"})
write_table(pd.DataFrame(name_row_list), "name_signal_robustness")


# GOAL: MEASURE CUMULATIVE OWNERSHIP DOWN THE CHAIN BELOW THE FIRST FOREIGN HOP

# rebuild the forest so ancestors can be walked edge by edge
g_own = nx.DiGraph()
g_own.add_edges_from(zip(df_entity.imm_parent_node_id, df_entity.node_id))
stake_dict = dict(zip(df_entity.node_id, df_entity.stake))
level_dict = dict(zip(df_entity.node_id, df_entity.level))
pred_dict = {child: parent for parent, child in g_own.edges}

cum_row_list = []
for row in df_entity.itertuples():
    if row.level == 0:
        continue

    # multiply recorded stakes up to the level-0 entity; a zero or missing
    # stake breaks the chain because zero is a missing code, not a share
    node, product, is_complete = row.node_id, 1.0, True
    while node in pred_dict and level_dict.get(node, 0) > 0:
        stake_value = stake_dict.get(node)
        if stake_value is None or np.isnan(stake_value) or stake_value == 0:
            is_complete = False
            break
        product *= stake_value / 100.0
        node = pred_dict[node]
    cum_row_list.append(
        {
            "target_id": row.target_id,
            "parent": row.parent,
            "level": row.level,
            "entity_country": row.entity_country,
            "chain_complete": is_complete,
            "cumulative_ownership": 100 * product if is_complete else np.nan,
        }
    )
df_cum = pd.DataFrame(cum_row_list)

# chain completion falls with depth, so report it alongside the estimates
df_complete = df_cum.groupby("level").chain_complete.agg(
    n_entities="size", pct_complete=lambda s: round(100 * s.mean(), 1)).reset_index()
write_table(df_complete, "cumulative_ownership_completion")

df_ok = df_cum[df_cum.chain_complete]
df_by_level = df_ok.groupby("level").agg(
    n=("cumulative_ownership", "size"),
    median=("cumulative_ownership", "median"),
    mean=("cumulative_ownership", "mean"),
    pct_at_100=("cumulative_ownership", lambda s: round(100 * (s > 99.99).mean(), 1)),
    pct_below_50=("cumulative_ownership", lambda s: round(100 * (s < 50).mean(), 1)),
).round(2).reset_index()
write_table(df_by_level, "cumulative_ownership_by_level")


# GOAL: TEST WHETHER APPARENT DEPTH-CONTROL PATTERNS SURVIVE PARENT CONTROLS

df_pos = df_entity[df_entity.stake.notna() & (df_entity.stake > 0)].copy()
df_pos["is_deep"] = (df_pos.level >= 3).astype(int)
df_pos["parent_mean_stake"] = df_pos.groupby("parent").stake.transform("mean")
df_pos["demeaned_stake"] = df_pos.stake - df_pos.parent_mean_stake

df_ok = df_ok.copy()
df_ok["is_deep"] = (df_ok.level >= 3).astype(int)
df_ok["parent_mean_cum"] = df_ok.groupby("parent").cumulative_ownership.transform("mean")
df_ok["demeaned_cum"] = df_ok.cumulative_ownership - df_ok.parent_mean_cum

dilution_row_list = [
    {"measure": "single-edge stake, shallow (levels 1-2)",
     "value": round(df_pos[df_pos.is_deep == 0].stake.mean(), 1)},
    {"measure": "single-edge stake, deep (level 3+)",
     "value": round(df_pos[df_pos.is_deep == 1].stake.mean(), 1)},
    {"measure": "raw deep-minus-shallow gap, percentage points",
     "value": round(df_pos[df_pos.is_deep == 1].stake.mean()
                    - df_pos[df_pos.is_deep == 0].stake.mean(), 1)},
    {"measure": "within-parent deep-minus-shallow gap, percentage points",
     "value": round(df_pos[df_pos.is_deep == 1].demeaned_stake.mean()
                    - df_pos[df_pos.is_deep == 0].demeaned_stake.mean(), 1)},
    {"measure": "cumulative ownership, shallow (levels 1-2)",
     "value": round(df_ok[df_ok.is_deep == 0].cumulative_ownership.mean(), 1)},
    {"measure": "cumulative ownership, deep (level 3+)",
     "value": round(df_ok[df_ok.is_deep == 1].cumulative_ownership.mean(), 1)},
    {"measure": "within-parent cumulative gap, percentage points",
     "value": round(df_ok[df_ok.is_deep == 1].demeaned_cum.mean()
                    - df_ok[df_ok.is_deep == 0].demeaned_cum.mean(), 1)},
]

# Reliance's minority venture holdings sit almost entirely at level 1
df_nor = df_ok[df_ok.parent != "RELIANCE INDUSTRIES LTD"]
dilution_row_list.append(
    {"measure": "cumulative ownership excluding Reliance, shallow",
     "value": round(df_nor[df_nor.is_deep == 0].cumulative_ownership.mean(), 1)})
dilution_row_list.append(
    {"measure": "cumulative ownership excluding Reliance, deep",
     "value": round(df_nor[df_nor.is_deep == 1].cumulative_ownership.mean(), 1)})
write_table(pd.DataFrame(dilution_row_list), "ownership_dilution_by_depth")


# GOAL: RECORD THE CORRECTED MINORITY FILTER FROM THE X-F010 REVIEW

filter_row_list = [
    {"filter": "stake < 10 including the zero code (increment 1 rule)",
     "n_entities_removed": int(((df_entity.stake.notna()) & (df_entity.stake < 10)).sum())},
    {"filter": "stake strictly positive and below 10 (corrected rule)",
     "n_entities_removed": int(((df_entity.stake.notna()) & (df_entity.stake > 0)
                                & (df_entity.stake < 10)).sum())},
    {"filter": "children of the two venture-fund vehicles",
     "n_entities_removed": int(df_entity.immediate_parent.str.contains(
         "BREAKTHROUGH", case=False, na=False).sum())},
]
write_table(pd.DataFrame(filter_row_list), "corrected_minority_filter")

print("name and stake analysis written")
print(pd.DataFrame(name_row_list).to_string(index=False))
print()
print(pd.DataFrame(dilution_row_list).to_string(index=False))
