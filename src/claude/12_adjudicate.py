"""Final adjudication: independently re-verify contested statistics.

Rebuilds the ownership forest with one change relative to 02_build_hierarchy:
the reported `immediate_parent_country` of a named-but-unscraped intermediary
is PRESERVED instead of being replaced with "(UNOBSERVED)". Codex's review of
commit 5ab6cb5 showed this is real, supplied information; discarding it moved
Dr Reddy's conduit exposure from 90% to 7%. Everything contested between the
two branches is recomputed on both graphs so the difference is attributable.
"""

import networkx as nx
import numpy as np
import pandas as pd

from config import derived_path, load_rows, write_table

CENTRE_LIST = [
    "NETHERLANDS", "MAURITIUS", "SINGAPORE", "CYPRUS", "LUXEMBOURG", "JERSEY",
    "GUERNSEY", "ISLE OF MAN", "CAYMAN ISLANDS", "BRITISH VIRGIN ISLANDS",
    "BERMUDA", "BARBADOS", "PANAMA", "MARSHALL ISLANDS", "IFSC GIFT CITY",
    "SWITZERLAND", "IRELAND", "HONG KONG", "UNITED ARAB EMIRATES",
]

df_entity = pd.read_parquet(derived_path / "entity.parquet")
df_rows = load_rows()


# GOAL: CONFIRM CODEX'S CENTRAL DATA CORRECTION

# an orphan parent is named as immediate_parent but never scraped as an entity
observed_key_set = set(df_entity.node_id)
df_orphan_edge = df_entity[
    df_entity.imm_parent_node_id.notna()
    & ~df_entity.imm_parent_node_id.isin(observed_key_set)
].copy()

n_orphan_edge = len(df_orphan_edge)
n_with_country = int(
    df_orphan_edge.immediate_parent_country.fillna("").str.strip().ne("").sum()
)
orphan_node_list = sorted(df_orphan_edge.imm_parent_node_id.unique())

df_orphan_country = (
    df_orphan_edge.groupby(["imm_parent_node_id", "immediate_parent_country"])
    .agg(n_children=("target_id", "size"), parents=("parent", "nunique"))
    .reset_index()
    .sort_values("n_children", ascending=False)
)
df_orphan_country["intermediary"] = (
    df_orphan_country.imm_parent_node_id.str.split("||", regex=False).str[-1]
)
write_table(
    df_orphan_country[
        ["intermediary", "immediate_parent_country", "n_children", "parents"]
    ],
    "adj_unobserved_parent_countries",
)


# GOAL: REBUILD THE FOREST TWICE, DIFFERING ONLY IN ORPHAN COUNTRY

def build_graph():
    """Return the ownership forest exactly as 02_build_hierarchy builds it."""

    g_own = nx.DiGraph()
    root_node = "ROOT"
    g_own.add_node(root_node)

    for parent_key in df_entity.parent_key.unique():
        g_own.add_edge(root_node, "PARENT::" + parent_key)

    for row in df_entity.itertuples():
        child = row.node_id
        if pd.isna(row.imm_parent_node_id) or row.level == 0:
            g_own.add_edge("PARENT::" + row.parent_key, child)
        else:
            g_own.add_edge(row.imm_parent_node_id, child)
    return g_own, root_node


g_own, root_node = build_graph()

# orphan nodes have no incoming edge of their own; attach them to their bucket
bucket_dict = dict(zip(df_entity.node_id, df_entity.parent_key))
for node in orphan_node_list:
    if g_own.in_degree(node) == 0:
        child_list = list(g_own.successors(node))
        bucket = bucket_dict.get(child_list[0], None)
        if bucket is not None:
            g_own.add_edge("PARENT::" + bucket, node)

# the two country maps: (A) discards the reported country, (B) preserves it
country_base = dict(zip(df_entity.node_id, df_entity.entity_country))
for parent_key in df_entity.parent_key.unique():
    country_base["PARENT::" + parent_key] = "INDIA"

country_a = dict(country_base)
country_b = dict(country_base)
orphan_country_dict = dict(
    zip(df_orphan_country.imm_parent_node_id, df_orphan_country.immediate_parent_country)
)
for node in orphan_node_list:
    country_a[node] = "(UNOBSERVED)"
    country_b[node] = orphan_country_dict.get(node, "(UNOBSERVED)")

path_dict = nx.single_source_shortest_path(g_own, root_node)


def upstream_countries(node_id, country_map):
    """Return the jurisdictions strictly above an entity on its ownership path."""

    node_list = path_dict[node_id][1:-1]
    return [country_map.get(n, "(UNOBSERVED)") for n in node_list]


df_entity["upstream_a"] = [upstream_countries(n, country_a) for n in df_entity.node_id]
df_entity["upstream_b"] = [upstream_countries(n, country_b) for n in df_entity.node_id]
df_entity["centre_a"] = [
    int(any(c in CENTRE_LIST for c in u)) for u in df_entity.upstream_a
]
df_entity["centre_b"] = [
    int(any(c in CENTRE_LIST for c in u)) for u in df_entity.upstream_b
]


# GOAL: C-F003 CONDUIT EXPOSURE UNDER BOTH GRAPHS AND FOUR ESTIMANDS

def parent_share(col):
    """Return the equal-parent mean of a binary column across the 28 buckets."""

    return df_entity.groupby("parent")[col].mean().mean() * 100


row_list = [
    {
        "estimand": "entity-weighted, orphan country discarded (increment 1)",
        "value_pct": df_entity.centre_a.mean() * 100,
        "n": len(df_entity),
    },
    {
        "estimand": "entity-weighted, orphan country preserved (corrected)",
        "value_pct": df_entity.centre_b.mean() * 100,
        "n": len(df_entity),
    },
    {
        "estimand": "equal-parent, orphan country discarded",
        "value_pct": parent_share("centre_a"),
        "n": df_entity.parent.nunique(),
    },
    {
        "estimand": "equal-parent, orphan country preserved",
        "value_pct": parent_share("centre_b"),
        "n": df_entity.parent.nunique(),
    },
    {
        "estimand": "level 1+ only, orphan country preserved",
        "value_pct": df_entity.loc[df_entity.level >= 1, "centre_b"].mean() * 100,
        "n": int((df_entity.level >= 1).sum()),
    },
    {
        "estimand": "level 2+ only, orphan country preserved",
        "value_pct": df_entity.loc[df_entity.level >= 2, "centre_b"].mean() * 100,
        "n": int((df_entity.level >= 2).sum()),
    },
]

# node-weighted: count each observed intermediary once, not once per descendant
internal_node_set = {
    n for n in g_own.nodes
    if n != root_node and not n.startswith("PARENT::") and g_own.out_degree(n) > 0
}
n_internal = len(internal_node_set)
n_internal_centre = sum(
    1 for n in internal_node_set if country_b.get(n, "") in CENTRE_LIST
)
row_list.append(
    {
        "estimand": "node-weighted: internal nodes located in a centre",
        "value_pct": 100 * n_internal_centre / n_internal,
        "n": n_internal,
    }
)

df_conduit = pd.DataFrame(row_list)
df_conduit["value_pct"] = df_conduit.value_pct.round(2)
write_table(df_conduit, "adj_conduit_exposure_estimands")

# leave-one-parent-out on the corrected graph
loo_list = []
for parent in sorted(df_entity.parent.unique()):
    df_keep = df_entity[df_entity.parent != parent]
    loo_list.append({"dropped": parent, "pct": round(df_keep.centre_b.mean() * 100, 2)})
df_loo = pd.DataFrame(loo_list).sort_values("pct")
write_table(df_loo, "adj_conduit_exposure_loo")

# the parent-level table, which is where the correction actually bites
df_parent_conduit = (
    df_entity.groupby("parent")
    .agg(
        n_entities=("target_id", "size"),
        pct_discarded=("centre_a", lambda s: round(s.mean() * 100, 1)),
        pct_preserved=("centre_b", lambda s: round(s.mean() * 100, 1)),
    )
    .reset_index()
)
df_parent_conduit["change_pp"] = (
    df_parent_conduit.pct_preserved - df_parent_conduit.pct_discarded
).round(1)
write_table(
    df_parent_conduit.sort_values("change_pp", ascending=False),
    "adj_conduit_exposure_by_parent_corrected",
)


# GOAL: C-F019 JURISDICTION CRITICALITY, CORRECTED AND GREEDY-COVERED

df_entity["upstream_set_b"] = [
    {c for c in u if c not in ("INDIA",)} for u in df_entity.upstream_b
]
country_pool = sorted({c for s in df_entity.upstream_set_b for c in s})

crit_list = []
for country in country_pool:
    mask = df_entity.upstream_set_b.apply(lambda s, c=country: c in s)
    n_below = int(mask.sum())
    if n_below < 10:
        continue
    n_resident = int((df_entity.entity_country == country).sum())
    equal_parent = df_entity.assign(hit=mask.astype(int)).groupby("parent").hit.mean()
    loo = [
        round(
            df_entity.loc[df_entity.parent != p, "upstream_set_b"]
            .apply(lambda s, c=country: c in s).mean() * 100,
            1,
        )
        for p in df_entity.parent.unique()
    ]
    crit_list.append(
        {
            "jurisdiction": country,
            "entities_below": n_below,
            "pct_of_1834": round(100 * n_below / len(df_entity), 1),
            "resident_entities": n_resident,
            "leverage_per_resident": round(n_below / n_resident, 1) if n_resident else np.nan,
            "n_parents_affected": int((equal_parent > 0).sum()),
            "equal_parent_pct": round(equal_parent.mean() * 100, 1),
            "loo_min_pct": min(loo),
            "loo_max_pct": max(loo),
        }
    )
df_crit = pd.DataFrame(crit_list).sort_values("entities_below", ascending=False)
write_table(df_crit, "adj_jurisdiction_criticality_corrected")

# greedy cover on the corrected graph
remaining = df_entity.upstream_set_b.tolist()
covered = np.zeros(len(remaining), dtype=bool)
cover_list = []
for step in range(1, 8):
    best, best_gain = None, -1
    for country in country_pool:
        gain = sum(
            1 for i, s in enumerate(remaining) if not covered[i] and country in s
        )
        if gain > best_gain:
            best, best_gain = country, gain
    if best_gain <= 0:
        break
    for i, s in enumerate(remaining):
        if best in s:
            covered[i] = True
    cover_list.append(
        {
            "step": step,
            "jurisdiction": best,
            "newly_detached": best_gain,
            "cumulative_pct": round(100 * covered.sum() / len(remaining), 1),
        }
    )
    country_pool = [c for c in country_pool if c != best]
write_table(pd.DataFrame(cover_list), "adj_greedy_cover_corrected")
