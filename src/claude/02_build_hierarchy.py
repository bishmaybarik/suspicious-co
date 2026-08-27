"""Build the analytical representation of the corporate hierarchy.

Collapses the row panel to unique scraped entities, reconstructs the
parent-child forest from immediate_parent, re-anchors subtrees whose
intermediary was never scraped, and writes entity, edge, path,
parent-jurisdiction and parent-level analytical tables.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import networkx as nx
import numpy as np
import pandas as pd

from config import derived_path, load_rows, write_table

# name of the synthetic global root that ties all Indian parent buckets together
root_node = "::INDIA_ROOT::"


def normalise_name(s_name):
    """Return an uppercase alphanumeric-only key for matching company names."""

    # strip punctuation and collapse whitespace so "B.V." and "BV" agree
    return (
        s_name.astype(str)
        .str.upper()
        .str.replace(r"[^A-Z0-9]", " ", regex=True)
        .str.split()
        .str.join(" ")
    )


# GOAL: COLLAPSE THE ROW PANEL TO ONE ROW PER SCRAPED ENTITY TARGET

df_row = load_rows()

# blanks are missing text in the Stata export
str_col_list = [c for c in df_row.columns if df_row[c].dtype == object]
df_row[str_col_list] = df_row[str_col_list].replace(r"^\s*$", np.nan, regex=True)

# structural variables are constant within target_id (verified in 01_audit_rows)
struct_col_list = [
    "target_id", "parent", "level", "entity_name", "entity_country",
    "immediate_parent", "immediate_parent_country", "stake", "sector_code",
    "sector_label", "uin", "shared_uin", "attribution_rule",
]
df_entity = df_row.drop_duplicates("target_id")[struct_col_list].copy()

# normalised keys drive all name matching between children and their parents
df_entity["entity_key"] = normalise_name(df_entity.entity_name)
df_entity["imm_parent_key"] = normalise_name(df_entity.immediate_parent)
df_entity["parent_key"] = normalise_name(df_entity.parent)

# a node is unique within a parent bucket, so namespace the key by parent
df_entity["node_id"] = df_entity.parent_key + "||" + df_entity.entity_key
df_entity["imm_parent_node_id"] = np.where(
    df_entity.level == 0,
    "PARENT::" + df_entity.parent_key,
    df_entity.parent_key + "||" + df_entity.imm_parent_key,
)


# GOAL: ATTACH THE BEST AVAILABLE FINANCIAL AND COVERAGE INFORMATION PER ENTITY

# keep the preferred row per target-year, then the most recent such year
df_pref = df_row[df_row.preferred_for_target_year == 1].copy()

# fiscal_year is a string label like "2023-24"; its first four digits sort correctly
df_pref["fiscal_year_start"] = pd.to_numeric(
    df_pref.fiscal_year.str.slice(0, 4), errors="coerce"
)

# count how many distinct fiscal years were recovered for each entity
s_nyears = df_pref.dropna(subset=["fiscal_year_start"]).groupby("target_id").fiscal_year.nunique()

# take the latest year with a parsed balance sheet where one exists
df_fin = df_pref[df_pref.equity.notna()].sort_values(["target_id", "fiscal_year_start"])
df_fin = df_fin.drop_duplicates("target_id", keep="last")

fin_col_list = [
    "fiscal_year", "fiscal_year_start", "currency", "units", "total_assets",
    "total_liabilities", "equity", "turnover", "profit_after_tax",
    "profit_before_tax", "cash_end", "dividends_paid", "source_type",
    "data_quality_tier", "ready_for_valuation",
]
df_entity = df_entity.merge(
    df_fin.set_index("target_id")[fin_col_list], left_on="target_id", right_index=True, how="left"
)

# entity-level coverage flags summarise whether any source was ever found
df_cov = df_row.groupby("target_id").agg(
    any_source_found=("source_found", "max"),
    any_pdf_downloaded=("pdf_downloaded", "max"),
    any_variables_parsed=("variables_parsed", "max"),
    any_ready_for_valuation=("ready_for_valuation", "max"),
    n_source_rows=("target_id", "size"),
)
df_entity = df_entity.merge(df_cov, left_on="target_id", right_index=True, how="left")
df_entity["n_fiscal_years"] = df_entity.target_id.map(s_nyears).fillna(0).astype(int)


# GOAL: RECONSTRUCT THE OWNERSHIP FOREST FROM IMMEDIATE-PARENT LINKS

# every entity contributes one directed edge from its immediate parent to itself
g_own = nx.DiGraph()
g_own.add_edges_from(zip(df_entity.imm_parent_node_id, df_entity.node_id))

# connect each Indian parent bucket to the synthetic global root
for parent_key in df_entity.parent_key.unique():
    g_own.add_edge(root_node, "PARENT::" + parent_key)

# the forest must be acyclic and single-parent for path logic to be well defined
assert nx.is_directed_acyclic_graph(g_own), "ownership graph contains a cycle"
assert max(dict(g_own.in_degree()).values()) == 1, "a node has multiple immediate parents"

# orphan roots are named intermediaries that were never scraped as an entity
orphan_list = [
    n for n in g_own.nodes
    if g_own.in_degree(n) == 0 and n != root_node
]

# infer each orphan's own level from the minimum reported level of its children
s_child_level = df_entity.groupby("imm_parent_node_id")["level"].min()
df_orphan = pd.DataFrame({"node_id": orphan_list})
df_orphan["implied_level"] = df_orphan.node_id.map(s_child_level) - 1

# recover the Indian parent bucket of each node from the entity table, not by
# string-splitting the key, because "||" would be read as a regex alternation
bucket_dict = dict(zip(df_entity.node_id, df_entity.parent_key))
bucket_dict.update(dict(zip(df_entity.imm_parent_node_id, df_entity.parent_key)))
df_orphan["parent_key"] = df_orphan.node_id.map(bucket_dict)

# re-anchor each orphan subtree under its Indian parent so paths stay connected
for row in df_orphan.itertuples():
    g_own.add_edge("PARENT::" + row.parent_key, row.node_id)


# GOAL: COMPUTE DEPTH, BRANCHING AND SUBTREE SIZE FOR EVERY NODE

# distance from the global root; the Indian parent sits at distance 1
depth_dict = nx.single_source_shortest_path_length(g_own, root_node)

# offset so that a directly held foreign entity has graph depth 0, matching level
s_depth = pd.Series(depth_dict, name="depth_graph") - 2

# an orphan carries an implied level, so its subtree needs that offset added back
offset_dict = {}
for row in df_orphan.itertuples():
    # the gap between the orphan's implied level and its reconstructed depth
    gap = row.implied_level - (depth_dict[row.node_id] - 2)
    for node in [row.node_id] + list(nx.descendants(g_own, row.node_id)):
        offset_dict[node] = gap
s_depth = s_depth.add(pd.Series(offset_dict), fill_value=0).astype(int)

# out-degree is the number of directly held children recorded in the data
s_nchild = pd.Series(dict(g_own.out_degree()), name="n_children")

# subtree size counts every entity sitting anywhere below a node
s_ndesc = pd.Series(
    {n: len(nx.descendants(g_own, n)) for n in g_own.nodes}, name="n_descendants"
)

df_entity["depth_graph"] = df_entity.node_id.map(s_depth)
df_entity["n_children"] = df_entity.node_id.map(s_nchild)
df_entity["n_descendants"] = df_entity.node_id.map(s_ndesc)
df_entity["is_leaf"] = (df_entity.n_children == 0).astype(int)
df_entity["is_orphan_bridged"] = df_entity.node_id.isin(offset_dict).astype(int)

# a positive gap means the reported level is deeper than the reconstructed chain,
# which happens when the immediate-parent link crosses UIN chains and skips steps
df_entity["level_gap"] = df_entity.level - df_entity.depth_graph


# GOAL: BUILD COMPLETE ROOT-TO-ENTITY OWNERSHIP PATHS

# map each node to its country so paths can be expressed in jurisdictions
country_dict = dict(zip(df_entity.node_id, df_entity.entity_country))

# Indian parent buckets and unscraped intermediaries get explicit labels
for parent_key in df_entity.parent_key.unique():
    country_dict["PARENT::" + parent_key] = "INDIA"
for node in orphan_list:
    country_dict.setdefault(node, "(UNOBSERVED)")

# walk each path once from the root; networkx returns the full node sequence
path_dict = nx.single_source_shortest_path(g_own, root_node)

path_row_list = []
for row in df_entity.itertuples():
    # drop the synthetic global root, keeping Indian parent through the entity
    node_list = path_dict[row.node_id][1:]
    country_list = [country_dict.get(n, "(UNOBSERVED)") for n in node_list]

    # collapse consecutive repeats to count genuine jurisdiction changes
    hop_list = [
        (a, b) for a, b in zip(country_list[:-1], country_list[1:]) if a != b
    ]
    path_row_list.append(
        {
            "target_id": row.target_id,
            "node_id": row.node_id,
            "path_nodes": " > ".join(n.split("||")[-1].replace("PARENT::", "") for n in node_list),
            "path_countries": " > ".join(country_list),
            "path_length": len(node_list),
            "n_countries_on_path": len(set(country_list)),
            "n_border_crossings": len(hop_list),
            "path_has_unobserved": int("(UNOBSERVED)" in country_list),
        }
    )
df_path = pd.DataFrame(path_row_list)
df_entity = df_entity.merge(df_path.drop(columns=["node_id"]), on="target_id", how="left")


# GOAL: BUILD THE EDGE TABLE WITH BOTH ENDPOINT ATTRIBUTES

df_edge = pd.DataFrame(
    [{"parent_node_id": u, "child_node_id": v} for u, v in g_own.edges if u != root_node]
)
df_edge["parent_country"] = df_edge.parent_node_id.map(country_dict)
df_edge["child_country"] = df_edge.child_node_id.map(country_dict)
df_edge["parent_depth"] = df_edge.parent_node_id.map(s_depth)
df_edge["child_depth"] = df_edge.child_node_id.map(s_depth)
df_edge["parent_bucket"] = df_edge.child_node_id.map(bucket_dict)
df_edge["is_border_crossing"] = (df_edge.parent_country != df_edge.child_country).astype(int)

# carry the child's ownership stake onto the edge it describes
df_edge = df_edge.merge(
    df_entity.set_index("node_id")[["stake", "sector_label"]],
    left_on="child_node_id", right_index=True, how="left",
)


# GOAL: BUILD PARENT-LEVEL AND PARENT-JURISDICTION AGGREGATES

df_parent = df_entity.groupby("parent").agg(
    n_entities=("target_id", "size"),
    n_uins=("uin", "nunique"),
    n_countries=("entity_country", "nunique"),
    n_sectors=("sector_label", "nunique"),
    max_depth=("depth_graph", "max"),
    mean_depth=("depth_graph", "mean"),
    n_level0=("level", lambda s: int((s == 0).sum())),
    n_leaves=("is_leaf", "sum"),
    mean_children=("n_children", "mean"),
    max_children=("n_children", "max"),
    mean_border_crossings=("n_border_crossings", "mean"),
    max_countries_on_path=("n_countries_on_path", "max"),
    pct_source_found=("any_source_found", lambda s: round(100 * s.mean(), 1)),
    pct_ready=("any_ready_for_valuation", lambda s: round(100 * s.mean(), 1)),
).round(2).reset_index()

# entities per registered outward investment measures downstream expansion
df_parent["entities_per_uin"] = (df_parent.n_entities / df_parent.n_uins).round(2)

df_parent_country = (
    df_entity.groupby(["parent", "entity_country"])
    .agg(n_entities=("target_id", "size"), mean_depth=("depth_graph", "mean"))
    .round(2)
    .reset_index()
    .sort_values(["parent", "n_entities"], ascending=[True, False])
)

# a Herfindahl over jurisdictions summarises how concentrated each group is
df_parent_country["share"] = df_parent_country.n_entities / df_parent_country.groupby(
    "parent"
).n_entities.transform("sum")
s_hhi = df_parent_country.assign(sq=lambda d: d.share ** 2).groupby("parent").sq.sum()
df_parent["country_hhi"] = df_parent.parent.map(s_hhi).round(3)


# GOAL: PERSIST ALL DERIVED TABLES FOR DOWNSTREAM ANALYSIS

df_entity.to_parquet(derived_path / "entity.parquet", index=False)
df_edge.to_parquet(derived_path / "edge.parquet", index=False)
df_path.to_parquet(derived_path / "path.parquet", index=False)
df_parent.to_parquet(derived_path / "parent.parquet", index=False)
df_parent_country.to_parquet(derived_path / "parent_country.parquet", index=False)

write_table(df_parent.sort_values("n_entities", ascending=False), "parent_summary")
write_table(df_orphan.sort_values("parent_key"), "unobserved_intermediaries")

print("entities:", len(df_entity), " edges:", len(df_edge), " parents:", len(df_parent))
print("unobserved intermediaries bridged:", len(df_orphan))
print("depth agreement with reported level:",
      round((df_entity.depth_graph == df_entity.level).mean(), 4))
