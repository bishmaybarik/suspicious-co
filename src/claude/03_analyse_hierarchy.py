"""Analyse the shape of the reconstructed ownership hierarchy.

Produces depth, branching, motif and parent-heterogeneity tables together with
the denominator checks that each headline number needs.
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity.parquet")
df_edge = pd.read_parquet(derived_path / "edge.parquet")

# the UIN string encodes the RBI regional office, an investment-type character
# and the registration year; 06_audit_uin_structure.py validates this reading
df_entity["uin_office"] = df_entity.uin.str.slice(0, 2)
df_entity["uin_type"] = df_entity.uin.str.slice(2, 3)
df_entity["uin_year"] = pd.to_numeric(df_entity.uin.str.slice(5, 9), errors="coerce")


# GOAL: DESCRIBE THE DEPTH DISTRIBUTION AND THE ODI-TO-ENTITY MULTIPLIER

# one row per reported level with entity counts and cumulative shares
df_depth = df_entity.level.value_counts().sort_index().rename("n_entities").to_frame()
df_depth["pct"] = (100 * df_depth.n_entities / len(df_entity)).round(1)
df_depth["cum_pct"] = df_depth.pct.cumsum().round(1)

# the reconstructed graph depth is the robustness counterpart of reported level
df_depth["n_entities_graph_depth"] = (
    df_entity.depth_graph.value_counts().sort_index()
)
df_depth.index.name = "level"
write_table(df_depth.reset_index(), "depth_distribution")

# each UIN is one registered outward investment; entities per UIN measures how
# far the actual structure runs beyond the registered first foreign entity
df_uin = df_entity.groupby(["parent", "uin"]).agg(
    n_entities=("target_id", "size"),
    max_level=("level", "max"),
    n_countries=("entity_country", "nunique"),
    uin_type=("uin_type", "first"),
    uin_year=("uin_year", "first"),
).reset_index()
write_table(df_uin.sort_values("n_entities", ascending=False), "uin_summary")


# GOAL: DESCRIBE BRANCHING AND THE CONCENTRATION OF OWNERSHIP EDGES

df_branch = (
    df_entity.n_children.value_counts().sort_index().rename("n_nodes").to_frame()
)
df_branch["pct_of_entities"] = (100 * df_branch.n_nodes / len(df_entity)).round(2)
df_branch.index.name = "n_children"
write_table(df_branch.reset_index(), "branching_distribution")

# the largest holding nodes and the share of all edges they account for
df_hub = df_entity.nlargest(25, "n_children")[
    ["parent", "entity_name", "entity_country", "level", "n_children",
     "n_descendants", "sector_label", "stake"]
]
write_table(df_hub, "top_holding_nodes")


# GOAL: MEASURE HOW MUCH OF THE STRUCTURE IS LAYERING RATHER THAN BRANCHING

df_nonleaf = df_entity[df_entity.n_children > 0]
layer_row_list = [
    {"statistic": "entities", "value": len(df_entity)},
    {"statistic": "leaf entities", "value": int(df_entity.is_leaf.sum())},
    {"statistic": "pct leaf", "value": round(100 * df_entity.is_leaf.mean(), 1)},
    {"statistic": "non-leaf entities", "value": len(df_nonleaf)},
    {"statistic": "non-leaf with exactly one child", "value": int((df_nonleaf.n_children == 1).sum())},
    {"statistic": "pct of non-leaf with one child", "value": round(100 * (df_nonleaf.n_children == 1).mean(), 1)},
    {"statistic": "pct of edges from top-20 nodes",
     "value": round(100 * df_entity.nlargest(20, "n_children").n_children.sum() / df_entity.n_children.sum(), 1)},
    {"statistic": "entities per registered UIN", "value": round(len(df_entity) / df_entity.uin.nunique(), 2)},
    {"statistic": "median entities per UIN", "value": float(df_uin.n_entities.median())},
    {"statistic": "pct of entities in top-10 UINs",
     "value": round(100 * df_uin.nlargest(10, "n_entities").n_entities.sum() / len(df_entity), 1)},
    {"statistic": "descendants per level-0 gateway",
     "value": round(df_entity[df_entity.level == 0].n_descendants.sum() / (df_entity.level == 0).sum(), 2)},
]
write_table(pd.DataFrame(layer_row_list), "hierarchy_shape_summary")


# GOAL: EXTRACT RECURRING JURISDICTION MOTIFS FROM COMPLETE OWNERSHIP PATHS


def collapse_repeats(path_countries):
    """Return the jurisdiction sequence with consecutive repeats removed."""

    # consecutive same-country hops are domestic layering, not a new jurisdiction
    country_list = path_countries.split(" > ")
    out_list = [country_list[0]]
    for country in country_list[1:]:
        if country != out_list[-1]:
            out_list.append(country)
    return " > ".join(out_list)


df_entity["path_collapsed"] = df_entity.path_countries.map(collapse_repeats)

df_motif = (
    df_entity.path_collapsed.value_counts().rename("n_entities").reset_index()
)
df_motif.columns = ["jurisdiction_sequence", "n_entities"]
df_motif["n_parents"] = df_motif.jurisdiction_sequence.map(
    df_entity.groupby("path_collapsed").parent.nunique()
)
write_table(df_motif.head(40), "jurisdiction_path_motifs")

# three-jurisdiction sub-sequences isolate the intermediary sandwich itself
trigram_count = Counter()
trigram_parent_dict = {}
for path_collapsed, parent in zip(df_entity.path_collapsed, df_entity.parent):
    country_list = path_collapsed.split(" > ")
    for i in range(len(country_list) - 2):
        key = tuple(country_list[i:i + 3])
        trigram_count[key] += 1
        trigram_parent_dict.setdefault(key, set()).add(parent)

df_trigram = pd.DataFrame(
    [
        {"j1": a, "j2": b, "j3": c, "n_paths": n, "n_parents": len(trigram_parent_dict[(a, b, c)])}
        for (a, b, c), n in trigram_count.items()
    ]
).sort_values("n_paths", ascending=False)
write_table(df_trigram.head(30), "jurisdiction_trigrams")


# GOAL: RANK PARENT GROUPS ON BREADTH VERSUS DEPTH VERSUS SPREAD

df_parent = pd.read_parquet(derived_path / "parent.parquet")

# correlations show whether complexity dimensions move together across groups
corr_row_list = [
    {"pair": "log(n_entities) vs max_depth",
     "corr": round(np.corrcoef(np.log(df_parent.n_entities), df_parent.max_depth)[0, 1], 3)},
    {"pair": "log(n_entities) vs mean_depth",
     "corr": round(np.corrcoef(np.log(df_parent.n_entities), df_parent.mean_depth)[0, 1], 3)},
    {"pair": "log(n_entities) vs log(n_countries)",
     "corr": round(np.corrcoef(np.log(df_parent.n_entities), np.log(df_parent.n_countries))[0, 1], 3)},
    {"pair": "max_depth vs country_hhi",
     "corr": round(np.corrcoef(df_parent.max_depth, df_parent.country_hhi)[0, 1], 3)},
    {"pair": "max_depth vs pct_source_found",
     "corr": round(np.corrcoef(df_parent.max_depth, df_parent.pct_source_found)[0, 1], 3)},
]
write_table(pd.DataFrame(corr_row_list), "parent_complexity_correlations")


# GOAL: CHECK WHETHER BREADTH IS INFLATED BY NON-CONTROLLING HOLDINGS

# very small stakes are fund or project participations rather than subsidiaries
df_entity["is_minority"] = (df_entity.stake.notna()) & (df_entity.stake < 10)
df_control = df_entity[~df_entity.is_minority]

df_denom = pd.DataFrame(
    {
        "parent": df_parent.parent,
        "n_entities_all": df_parent.n_entities.values,
    }
)
df_denom["n_entities_stake_ge_10"] = df_denom.parent.map(df_control.groupby("parent").size()).fillna(0).astype(int)
df_denom["n_entities_excl_project_uin"] = df_denom.parent.map(
    df_entity[df_entity.uin_type != "P"].groupby("parent").size()
).fillna(0).astype(int)
df_denom["pct_dropped_by_stake_filter"] = (
    100 * (1 - df_denom.n_entities_stake_ge_10 / df_denom.n_entities_all)
).round(1)
write_table(df_denom.sort_values("n_entities_all", ascending=False), "parent_denominator_check")

df_entity.to_parquet(derived_path / "entity_enriched.parquet", index=False)

print("hierarchy analysis written")
print("pct leaf:", round(100 * df_entity.is_leaf.mean(), 1))
print("non-leaf with one child:", round(100 * (df_nonleaf.n_children == 1).mean(), 1), "%")
print("entities per UIN:", round(len(df_entity) / df_entity.uin.nunique(), 2))
