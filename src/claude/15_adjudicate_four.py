"""Final adjudication, part four: robustness of the two proposed core results.

Subjects the corrected chokepoint statistic (C-F018) and the jurisdiction
cover (C-F019) to the checks the protocol names: venture-fund exclusion,
minority-stake exclusion, and a benchmark test of whether the chokepoint's
jurisdiction is unusual relative to the group's own footprint.
"""

import networkx as nx
import pandas as pd

from config import derived_path, write_table

CENTRE_LIST = [
    "NETHERLANDS", "MAURITIUS", "SINGAPORE", "CYPRUS", "LUXEMBOURG", "JERSEY",
    "GUERNSEY", "ISLE OF MAN", "CAYMAN ISLANDS", "BRITISH VIRGIN ISLANDS",
    "BERMUDA", "BARBADOS", "PANAMA", "MARSHALL ISLANDS", "IFSC GIFT CITY",
    "SWITZERLAND", "IRELAND", "HONG KONG", "UNITED ARAB EMIRATES",
]

df_entity = pd.read_parquet(derived_path / "entity.parquet")
observed_key_set = set(df_entity.node_id)

# reported country of every named-but-unscraped intermediary, preserved
country_map = dict(zip(df_entity.node_id, df_entity.entity_country))
country_map.update(
    dict(
        df_entity[df_entity.imm_parent_node_id.notna()
                  & ~df_entity.imm_parent_node_id.isin(observed_key_set)]
        .groupby("imm_parent_node_id").immediate_parent_country.first()
    )
)


def build(df_in):
    """Return the ownership forest over a chosen subset of entities."""

    g_own = nx.DiGraph()
    g_own.add_node("ROOT")
    keep_set = set(df_in.node_id)
    bucket_dict = dict(zip(df_in.node_id, df_in.parent_key))
    for parent_key in df_in.parent_key.unique():
        g_own.add_edge("ROOT", "PARENT::" + parent_key)
    for row in df_in.itertuples():
        if pd.isna(row.imm_parent_node_id) or row.level == 0:
            g_own.add_edge("PARENT::" + row.parent_key, row.node_id)
        else:
            g_own.add_edge(row.imm_parent_node_id, row.node_id)
    for node in [
        n for n in list(g_own.nodes)
        if n not in keep_set and n != "ROOT" and not n.startswith("PARENT::")
    ]:
        if g_own.in_degree(node) == 0:
            g_own.add_edge(
                "PARENT::" + bucket_dict[next(iter(g_own.successors(node)))], node
            )
    return g_own


def group_chokepoints(df_in):
    """Yield (parent, best node, share below it) for every group of 15+ entities."""

    g_own = build(df_in)
    for parent, df_grp in df_in.groupby("parent"):
        if len(df_grp) < 15:
            continue
        member_set = set(df_grp.node_id)
        parent_key = df_grp.parent_key.iloc[0]
        cand = [
            n for n in g_own.nodes
            if n != "ROOT" and not n.startswith("PARENT::")
            and n.split("||", 1)[0] == parent_key
        ]
        best_node = max(
            cand, key=lambda n: len(nx.descendants(g_own, n) & member_set)
        )
        best_n = len(nx.descendants(g_own, best_node) & member_set)
        yield parent, best_node, 100 * best_n / (len(df_grp) - 1)


def choke_median(df_in, label):
    """Return the parent-level median largest-subtree share on a subset."""

    s_share = pd.Series([s for _, _, s in group_chokepoints(df_in)])
    return {
        "sample": label, "n_groups": len(s_share),
        "median_pct": round(s_share.median(), 1),
        "mean_pct": round(s_share.mean(), 1),
        "n_above_60": int((s_share > 60).sum()),
    }


# a fund portfolio is a stake below 10% that is strictly positive; a recorded
# zero is a missing code (see research/reviews/X-F010.md) and is not filtered
df_no_fund = df_entity[
    ~df_entity.imm_parent_node_id.fillna("").str.contains(
        "BREAKTHROUGH ENERGY VENTURES", regex=False
    )
]
df_no_minor = df_entity[~((df_entity.stake > 0) & (df_entity.stake < 10))]

df_choke_rob = pd.DataFrame(
    [
        choke_median(df_entity, "all entities, unscraped intermediaries included"),
        choke_median(df_no_fund, "excluding the two venture-fund portfolios"),
        choke_median(df_no_minor, "excluding strictly positive stakes below 10%"),
        choke_median(df_entity[df_entity.level <= 8], "excluding levels above 8"),
    ]
)
write_table(df_choke_rob, "adj_chokepoint_robustness")
print(df_choke_rob.to_string(index=False))


# GOAL: IS THE CHOKEPOINT'S JURISDICTION UNUSUAL FOR ITS OWN GROUP?

row_list = []
for parent, best_node, share in group_chokepoints(df_entity):
    df_grp = df_entity[df_entity.parent == parent]
    choke_country = country_map.get(best_node, "(UNKNOWN)")
    row_list.append(
        {
            "parent": parent,
            "chokepoint": best_node.split("||", 1)[-1],
            "chokepoint_country": choke_country,
            "pct_below": round(share, 1),
            "is_centre": int(choke_country in CENTRE_LIST),
            "group_pct_in_centres": round(
                100 * df_grp.entity_country.isin(CENTRE_LIST).mean(), 1
            ),
        }
    )
df_cc = pd.DataFrame(row_list)
write_table(
    df_cc.sort_values(["is_centre", "pct_below"], ascending=False),
    "adj_chokepoint_jurisdiction",
)
print("\nchokepoints located in a financial centre:",
      int(df_cc.is_centre.sum()), "of", len(df_cc),
      f"= {100 * df_cc.is_centre.mean():.1f}%")
print("if the chokepoint were a randomly drawn entity from its own group,")
print("  the expected centre rate would be",
      f"{df_cc.group_pct_in_centres.mean():.1f}%")
