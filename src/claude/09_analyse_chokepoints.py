"""Analyse structural chokepoints, jurisdictional criticality and routing.

New in increment 2. Because the reconstructed ownership graph is a forest,
every ancestor of an entity is a dominator of it: removing any node on the
path detaches everything below it. That makes single-node and single-
jurisdiction dependence directly measurable without any network heuristics.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")

# the jurisdictions strictly above an entity are exactly its chokepoints
df_entity["upstream_set"] = df_entity.path_countries.map(
    lambda s: set(s.split(" > ")[:-1])
)

# the first foreign jurisdiction on the path is the entity's gateway
df_entity["gateway_country"] = df_entity.path_countries.map(
    lambda s: s.split(" > ")[1]
)


# GOAL: MEASURE HOW MUCH OF EACH GROUP HANGS BELOW A SINGLE FOREIGN ENTITY

df_choke = df_entity.groupby("parent").agg(
    n_entities=("target_id", "size"),
    n_gateways=("level", lambda s: int((s == 0).sum())),
    max_descendants=("n_descendants", "max"),
).reset_index()

# the denominator excludes the chokepoint node itself
df_choke["pct_below_one_node"] = (
    100 * df_choke.max_descendants / (df_choke.n_entities - 1)
).round(1)

# name the chokepoint and its jurisdiction so the result is inspectable
s_top = df_entity.loc[df_entity.groupby("parent").n_descendants.idxmax()].set_index("parent")
df_choke["chokepoint_entity"] = df_choke.parent.map(s_top.entity_name)
df_choke["chokepoint_country"] = df_choke.parent.map(s_top.entity_country)
df_choke["chokepoint_level"] = df_choke.parent.map(s_top.level)

# a group with one registered investment is concentrated by construction, so
# the gateway Herfindahl separates mechanical from chosen concentration
df_gateway = df_entity[df_entity.level == 0].assign(
    subtree_size=lambda d: d.n_descendants + 1
)
s_share = df_gateway.subtree_size / df_gateway.groupby("parent").subtree_size.transform("sum")
df_choke["gateway_hhi"] = df_choke.parent.map(
    df_gateway.assign(sq=s_share ** 2).groupby("parent").sq.sum()
).round(3)

df_choke = df_choke[df_choke.n_entities >= 15].sort_values(
    "pct_below_one_node", ascending=False
)
write_table(df_choke, "chokepoint_single_node")

# the mechanical worry is that few gateways force concentration; test it
df_big = df_choke.copy()
choke_row_list = [
    {"statistic": "groups with at least 15 entities", "value": len(df_big)},
    {"statistic": "median pct of network below one entity",
     "value": float(df_big.pct_below_one_node.median())},
    {"statistic": "groups with over 60 pct below one entity",
     "value": int((df_big.pct_below_one_node > 60).sum())},
    {"statistic": "groups with over 90 pct below one entity",
     "value": int((df_big.pct_below_one_node > 90).sum())},
    {"statistic": "correlation of n_gateways with pct_below_one_node",
     "value": round(np.corrcoef(df_big.n_gateways, df_big.pct_below_one_node)[0, 1], 3)},
    {"statistic": "median pct below one entity, groups with 5+ gateways",
     "value": float(df_big[df_big.n_gateways >= 5].pct_below_one_node.median())},
    {"statistic": "chokepoints located in a financial-centre jurisdiction",
     "value": int(df_big.chokepoint_country.isin(
         ["MAURITIUS", "NETHERLANDS", "SINGAPORE", "SWITZERLAND", "CYPRUS",
          "CHANNEL ISLAND", "JERSEY", "LUXEMBOURG"]).sum())},
]
write_table(pd.DataFrame(choke_row_list), "chokepoint_summary")


# GOAL: MEASURE HOW MANY ENTITIES EACH JURISDICTION SITS ABOVE

country_list = sorted(
    {c for s in df_entity.upstream_set for c in s if c not in ("INDIA", "(UNOBSERVED)")}
)

crit_row_list = []
for country in country_list:
    s_above = df_entity.upstream_set.map(lambda s: country in s)
    if s_above.sum() < 5:
        continue

    # leave-one-parent-out bounds the influence of any single group
    loo_list = [
        100 * df_entity[df_entity.parent != p].upstream_set.map(
            lambda s: country in s).mean()
        for p in df_entity.parent.unique()
    ]
    crit_row_list.append(
        {
            "jurisdiction": country,
            "n_entities_below": int(s_above.sum()),
            "pct_of_all_entities": round(100 * s_above.mean(), 2),
            "equal_parent_pct": round(
                100 * df_entity.assign(a=s_above).groupby("parent").a.mean().mean(), 2),
            "loo_min_pct": round(min(loo_list), 2),
            "loo_max_pct": round(max(loo_list), 2),
            "n_parents_affected": int(df_entity[s_above].parent.nunique()),
            "n_resident_entities": int((df_entity.entity_country == country).sum()),
        }
    )
df_crit = pd.DataFrame(crit_row_list)

# entities held below per entity resident there is the leverage of a location
df_crit["below_per_resident"] = (
    df_crit.n_entities_below / df_crit.n_resident_entities.replace(0, np.nan)
).round(2)
df_crit = df_crit.sort_values("n_entities_below", ascending=False)
write_table(df_crit, "jurisdiction_criticality")


# GOAL: FIND THE SMALLEST SET OF JURISDICTIONS SITTING ABOVE MOST ENTITIES


def greedy_cover(df_sample, max_steps=8):
    """Return the greedy sequence of jurisdictions covering the most entities."""

    # at each step take the jurisdiction above the most still-uncovered entities
    remaining_set = set(df_sample.index)
    step_list = []
    for _ in range(max_steps):
        best_country, best_n = None, 0
        for country in country_list:
            n_cover = sum(1 for i in remaining_set if country in df_sample.upstream_set[i])
            if n_cover > best_n:
                best_country, best_n = country, n_cover
        if best_n == 0:
            break
        remaining_set = {
            i for i in remaining_set if best_country not in df_sample.upstream_set[i]
        }
        step_list.append(
            {
                "step": len(step_list) + 1,
                "jurisdiction": best_country,
                "newly_covered": best_n,
                "cumulative_pct": round(
                    100 * (len(df_sample) - len(remaining_set)) / len(df_sample), 1),
            }
        )
    return pd.DataFrame(step_list)


df_cover = greedy_cover(df_entity)
df_cover["sample"] = "all entities"

# the control-weighted sample removes the two venture-fund portfolios
df_control = df_entity[
    ~df_entity.immediate_parent.str.contains("BREAKTHROUGH", case=False, na=False)
]
df_cover_ctrl = greedy_cover(df_control)
df_cover_ctrl["sample"] = "excluding venture-fund portfolios"

write_table(pd.concat([df_cover, df_cover_ctrl], ignore_index=True),
            "jurisdiction_greedy_cover")


# GOAL: MEASURE WHICH GATEWAY EACH DESTINATION IS REACHED THROUGH

route_row_list = []
for country, df_dest in df_entity[df_entity.level >= 1].groupby("entity_country"):
    if len(df_dest) < 12:
        continue
    s_gw = df_dest.gateway_country.value_counts()
    route_row_list.append(
        {
            "destination": country,
            "n_entities": len(df_dest),
            "n_distinct_gateways": len(s_gw),
            "top_gateway": s_gw.index[0],
            "top_gateway_pct": round(100 * s_gw.iloc[0] / len(df_dest), 1),
            "n_parents": int(df_dest.parent.nunique()),
            "top_gateway_n_parents": int(
                df_dest[df_dest.gateway_country == s_gw.index[0]].parent.nunique()),
        }
    )
df_route = pd.DataFrame(route_row_list).sort_values("top_gateway_pct", ascending=False)
write_table(df_route, "destination_routing_concentration")

print("chokepoint analysis written")
print("median pct of a group's network below one entity:",
      df_big.pct_below_one_node.median())
print(df_cover.to_string(index=False))
