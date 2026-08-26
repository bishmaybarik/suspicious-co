"""Analyse the jurisdictional geometry of the ownership network.

Covers gateway amplification, empirical jurisdiction roles, leave-one-parent-out
robustness, conduit exposure by parent, round-trip structures and the vintage
composition of first-hop jurisdictions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")
df_edge = pd.read_parquet(derived_path / "edge.parquet")

# jurisdictions commonly used as holding or asset-isolation locations; the list
# is used only to summarise exposure, never to imply anything about conduct
centre_list = [
    "NETHERLANDS", "MAURITIUS", "SINGAPORE", "CYPRUS", "LUXEMBOURG", "JERSEY",
    "GUERNSEY", "ISLE OF MAN", "CAYMAN ISLANDS", "BRITISH VIRGIN ISLANDS",
    "BERMUDA", "BARBADOS", "PANAMA", "MARSHALL ISLAND", "IFSC GIFT CITY",
    "SWITZERLAND", "IRELAND", "HONGKONG", "UNITED ARAB EMIRATES",
]


# GOAL: MEASURE HOW MUCH DOWNSTREAM STRUCTURE EACH FIRST-HOP JURISDICTION CARRIES

df_gateway = df_entity[df_entity.level == 0]

df_amp = df_gateway.groupby("entity_country").agg(
    n_gateways=("target_id", "size"),
    n_parents=("parent", "nunique"),
    total_descendants=("n_descendants", "sum"),
    median_descendants=("n_descendants", "median"),
    max_descendants=("n_descendants", "max"),
).reset_index()

# the mean is sum over count; the median is the single-parent-robust counterpart
df_amp["descendants_per_gateway"] = (
    df_amp.total_descendants / df_amp.n_gateways
).round(2)
df_amp = df_amp[df_amp.n_gateways >= 3].sort_values(
    "descendants_per_gateway", ascending=False
)
write_table(df_amp, "gateway_amplification")


# GOAL: SHOW THAT GATEWAY AMPLIFICATION SURVIVES DROPPING ANY SINGLE PARENT

loo_row_list = []
for country in ["NETHERLANDS", "MAURITIUS", "SINGAPORE", "UNITED STATES OF AMERICA",
                "UNITED KINGDOM", "CYPRUS", "UNITED ARAB EMIRATES"]:
    df_country = df_gateway[df_gateway.entity_country == country]

    # drop each contributing parent in turn and recompute the ratio
    for parent in sorted(df_country.parent.unique()):
        df_keep = df_country[df_country.parent != parent]
        if len(df_keep) == 0:
            continue
        loo_row_list.append(
            {
                "entity_country": country,
                "parent_dropped": parent,
                "n_gateways_remaining": len(df_keep),
                "descendants_per_gateway": round(df_keep.n_descendants.sum() / len(df_keep), 2),
                "median_descendants": float(df_keep.n_descendants.median()),
            }
        )
df_loo = pd.DataFrame(loo_row_list)

# the worst case across all drops is the number a sceptical reader should use
df_loo_min = df_loo.groupby("entity_country").agg(
    full_sample_ratio=("entity_country", lambda s: float(
        df_amp.set_index("entity_country").descendants_per_gateway.get(s.iloc[0], np.nan))),
    min_ratio_after_dropping_one_parent=("descendants_per_gateway", "min"),
    min_median_after_dropping_one_parent=("median_descendants", "min"),
).reset_index()
write_table(df_loo, "gateway_amplification_leave_one_out")
write_table(df_loo_min, "gateway_amplification_loo_summary")


# GOAL: DERIVE EACH JURISDICTION'S ROLE FROM THE DATA RATHER THAN A FIXED LIST

df_role = df_entity.groupby("entity_country").agg(
    n_entities=("target_id", "size"),
    n_parents=("parent", "nunique"),
    mean_level=("level", "mean"),
    median_level=("level", "median"),
    pct_nonleaf=("is_leaf", lambda s: 100 * (1 - s.mean())),
    mean_children=("n_children", "mean"),
    descendants_per_entity=("n_descendants", "mean"),
    pct_level0=("level", lambda s: 100 * (s == 0).mean()),
).round(2).reset_index()
df_role = df_role[df_role.n_entities >= 8].sort_values("pct_nonleaf", ascending=False)
write_table(df_role, "jurisdiction_roles")


# GOAL: QUANTIFY HOW MANY ENTITIES ARE REACHED THROUGH A HOLDING JURISDICTION


def has_upstream_centre(path_countries):
    """Return True if a listed centre appears strictly above the entity itself."""

    # exclude the final element so an entity located in a centre does not count
    return len(set(path_countries.split(" > ")[:-1]) & set(centre_list)) > 0


df_entity["reached_through_centre"] = df_entity.path_countries.map(has_upstream_centre)

df_exposure = df_entity.groupby("parent").agg(
    n_entities=("target_id", "size"),
    pct_reached_through_centre=("reached_through_centre", lambda s: round(100 * s.mean(), 1)),
    mean_countries_on_path=("n_countries_on_path", "mean"),
    mean_border_crossings=("n_border_crossings", "mean"),
).round(2).sort_values("pct_reached_through_centre", ascending=False).reset_index()
write_table(df_exposure, "conduit_exposure_by_parent")

exposure_row_list = [
    {"sample": "all entities", "n": len(df_entity),
     "pct_reached_through_centre": round(100 * df_entity.reached_through_centre.mean(), 1)},
    {"sample": "excluding project/participation UINs", "n": int((df_entity.uin_type != "P").sum()),
     "pct_reached_through_centre": round(
         100 * df_entity[df_entity.uin_type != "P"].reached_through_centre.mean(), 1)},
    {"sample": "excluding stakes below 10 pct", "n": int((~df_entity.is_minority).sum()),
     "pct_reached_through_centre": round(
         100 * df_entity[~df_entity.is_minority].reached_through_centre.mean(), 1)},
    {"sample": "excluding the largest parent (Motherson)",
     "n": int((df_entity.parent != "SAMVARDHANA MOTHERSON INTERNATI").sum()),
     "pct_reached_through_centre": round(
         100 * df_entity[df_entity.parent != "SAMVARDHANA MOTHERSON INTERNATI"].reached_through_centre.mean(), 1)},
    {"sample": "one observation per parent (parent-weighted mean)", "n": df_entity.parent.nunique(),
     "pct_reached_through_centre": round(
         df_entity.groupby("parent").reached_through_centre.mean().mean() * 100, 1)},
]
write_table(pd.DataFrame(exposure_row_list), "conduit_exposure_robustness")


# GOAL: IDENTIFY OWNERSHIP CHAINS THAT RETURN TO INDIA

df_roundtrip = df_entity[
    df_entity.entity_country.isin(["INDIA", "IFSC GIFT CITY"]) & (df_entity.level >= 1)
][["parent", "entity_name", "entity_country", "level", "immediate_parent",
   "immediate_parent_country", "stake", "path_countries", "uin"]]
write_table(df_roundtrip.sort_values(["parent", "level"]), "round_trip_entities")


# GOAL: TRACK HOW FIRST-HOP JURISDICTIONS SHIFT ACROSS REGISTRATION VINTAGES

df_gateway = df_gateway.copy()
df_gateway["vintage"] = pd.cut(
    df_gateway.uin_year,
    [1988, 2004, 2010, 2015, 2020, 2026],
    labels=["<=2004", "2005-10", "2011-15", "2016-20", "2021-25"],
)

# group rarely used gateways together so the composition table stays readable
vintage_country_list = ["MAURITIUS", "SINGAPORE", "NETHERLANDS", "CYPRUS",
                        "UNITED ARAB EMIRATES", "IFSC GIFT CITY", "LUXEMBOURG",
                        "UNITED STATES OF AMERICA", "UNITED KINGDOM"]
df_gateway["gateway_group"] = np.where(
    df_gateway.entity_country.isin(vintage_country_list),
    df_gateway.entity_country,
    "other",
)

df_vintage_n = pd.crosstab(df_gateway.vintage, df_gateway.gateway_group)
df_vintage_pct = (100 * pd.crosstab(df_gateway.vintage, df_gateway.gateway_group,
                                    normalize="index")).round(1)
write_table(df_vintage_n.reset_index(), "gateway_vintage_counts")
write_table(df_vintage_pct.reset_index(), "gateway_vintage_shares")

# structure size by vintage speaks to build-out time rather than intent
df_uin_vintage = df_entity.groupby("uin").agg(
    uin_year=("uin_year", "first"),
    n_entities=("target_id", "size"),
    max_level=("level", "max"),
    n_countries=("entity_country", "nunique"),
)
df_uin_vintage["vintage"] = pd.cut(
    df_uin_vintage.uin_year, [1988, 2004, 2010, 2015, 2020, 2026],
    labels=["<=2004", "2005-10", "2011-15", "2016-20", "2021-25"],
)
df_vintage_size = df_uin_vintage.groupby("vintage", observed=True).agg(
    n_uins=("n_entities", "size"),
    mean_entities=("n_entities", "mean"),
    median_entities=("n_entities", "median"),
    mean_max_level=("max_level", "mean"),
    mean_countries=("n_countries", "mean"),
).round(2).reset_index()
write_table(df_vintage_size, "uin_vintage_structure_size")

df_entity.to_parquet(derived_path / "entity_enriched.parquet", index=False)

print("jurisdiction analysis written")
print("pct reached through a listed centre:",
      round(100 * df_entity.reached_through_centre.mean(), 1))
print("round-trip entities at level >= 1:", len(df_roundtrip))
