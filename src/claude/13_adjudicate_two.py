"""Final adjudication, part two: chokepoints, coverage, roots and gateways.

Recomputes the four remaining contested quantities. The chokepoint measure
(C-F018) is rebuilt with named-but-unscraped intermediaries treated as real
nodes, which is the same correction applied in 12_adjudicate.py. The coverage
depth gradient (C-F014) is re-estimated as a parent fixed-effect regression
rather than as a demeaned cell mean, which is the estimator Codex's review of
commit 5ab6cb5 argued for.
"""

import networkx as nx
import numpy as np
import pandas as pd

from config import derived_path, write_table

df_entity = pd.read_parquet(derived_path / "entity.parquet")
observed_key_set = set(df_entity.node_id)


# GOAL: REBUILD THE FOREST WITH UNSCRAPED INTERMEDIARIES AS REAL NODES

g_own = nx.DiGraph()
g_own.add_node("ROOT")
for parent_key in df_entity.parent_key.unique():
    g_own.add_edge("ROOT", "PARENT::" + parent_key)
for row in df_entity.itertuples():
    if pd.isna(row.imm_parent_node_id) or row.level == 0:
        g_own.add_edge("PARENT::" + row.parent_key, row.node_id)
    else:
        g_own.add_edge(row.imm_parent_node_id, row.node_id)

bucket_dict = dict(zip(df_entity.node_id, df_entity.parent_key))
orphan_set = {
    n for n in g_own.nodes
    if n not in observed_key_set and n != "ROOT" and not n.startswith("PARENT::")
}
for node in orphan_set:
    if g_own.in_degree(node) == 0:
        bucket = bucket_dict.get(list(g_own.successors(node))[0])
        g_own.add_edge("PARENT::" + bucket, node)

# only unscraped intermediaries below level 0 are structural holes; the ones
# whose reported country is INDIA are the listed parent itself, not a conduit
orphan_country = dict(
    df_entity[df_entity.imm_parent_node_id.isin(orphan_set)]
    .groupby("imm_parent_node_id").immediate_parent_country.first()
)
df_holes = (
    pd.Series(orphan_country).rename("country").reset_index()
    .rename(columns={"index": "node_id"})
)
df_holes["n_direct_children"] = df_holes.node_id.map(lambda n: g_own.out_degree(n))
df_holes["n_descendants"] = df_holes.node_id.map(lambda n: len(nx.descendants(g_own, n)))
df_holes["name"] = df_holes.node_id.str.split("||", regex=False).str[-1]
df_holes["is_foreign_hole"] = (df_holes.country != "INDIA").astype(int)
write_table(
    df_holes[df_holes.is_foreign_hole == 1]
    [["name", "country", "n_direct_children", "n_descendants"]]
    .sort_values("n_descendants", ascending=False),
    "adj_unobserved_foreign_intermediaries",
)
print("unscraped intermediary nodes:", len(orphan_set))
print("of which reported country is not India:", int(df_holes.is_foreign_hole.sum()))
print("edges into a non-India unscraped parent:", int(
    df_entity.imm_parent_node_id.isin(
        set(df_holes.loc[df_holes.is_foreign_hole == 1, "node_id"])
    ).sum()
))


# GOAL: C-F018 CHOKEPOINTS, WITH AND WITHOUT THE UNSCRAPED NODES

def chokepoint_table(include_holes):
    """Return the largest-subtree share for every parent bucket."""

    row_list = []
    for parent, df_grp in df_entity.groupby("parent"):
        parent_key = df_grp.parent_key.iloc[0]
        member_set = set(df_grp.node_id)
        n_ent = len(df_grp)
        if n_ent < 15:
            continue
        cand_list = list(member_set)
        if include_holes:
            cand_list += [
                n for n in orphan_set
                if bucket_dict.get(next(iter(g_own.successors(n))), None) == parent_key
            ]
        best_node, best_n = None, 0
        for node in cand_list:
            n_below = len(nx.descendants(g_own, node) & member_set)
            if n_below > best_n:
                best_node, best_n = node, n_below
        row_list.append(
            {
                "parent": parent,
                "n_entities": n_ent,
                "chokepoint": best_node.split("||")[-1] if best_node else "",
                "pct_below_one_node": round(100 * best_n / (n_ent - 1), 1),
            }
        )
    return pd.DataFrame(row_list)


df_choke_a = chokepoint_table(False).rename(
    columns={"pct_below_one_node": "pct_observed_only", "chokepoint": "node_observed"}
)
df_choke_b = chokepoint_table(True).rename(
    columns={"pct_below_one_node": "pct_with_holes", "chokepoint": "node_with_holes"}
)
df_choke = df_choke_a.merge(
    df_choke_b[["parent", "node_with_holes", "pct_with_holes"]], on="parent"
)
df_choke["change_pp"] = (df_choke.pct_with_holes - df_choke.pct_observed_only).round(1)
df_choke = df_choke.sort_values("pct_with_holes", ascending=False)
write_table(df_choke, "adj_chokepoint_corrected")
print("\nchokepoint median, observed only :", df_choke.pct_observed_only.median())
print("chokepoint median, holes included:", df_choke.pct_with_holes.median())
print("groups above 60% (holes included):", int((df_choke.pct_with_holes > 60).sum()),
      "of", len(df_choke))

# gateway count is the mechanical rival explanation; test it again
n_gateway = df_entity[df_entity.level == 0].groupby("parent").size()
df_choke["n_gateways"] = df_choke.parent.map(n_gateway).fillna(0)
print("corr(pct_with_holes, n_gateways) =",
      round(df_choke.pct_with_holes.corr(df_choke.n_gateways), 3))
df_wide = df_choke[df_choke.n_gateways >= 5]
print("median among groups with 5+ gateways:", df_wide.pct_with_holes.median(),
      f"(n={len(df_wide)})")


# GOAL: C-F014 COVERAGE DEPTH GRADIENT AS A PARENT FIXED-EFFECT REGRESSION

df_cov = df_entity[["parent", "level", "any_ready_for_valuation"]].copy()
df_cov["ready"] = df_cov.any_ready_for_valuation.astype(float)
df_cov["deep"] = (df_cov.level >= 3).astype(float)


def within_fe(df_in):
    """Return the parent fixed-effect coefficient of deep on ready, in pp."""

    df_w = df_in.copy()
    for col in ("ready", "deep"):
        df_w[col] = df_w[col] - df_w.groupby("parent")[col].transform("mean")
    denom = (df_w.deep ** 2).sum()
    return 100 * (df_w.deep * df_w.ready).sum() / denom if denom > 0 else np.nan


raw_gap = 100 * (
    df_cov.loc[df_cov.deep == 1, "ready"].mean()
    - df_cov.loc[df_cov.deep == 0, "ready"].mean()
)
fe_coef = within_fe(df_cov)
paired = (
    df_cov.groupby(["parent", "deep"]).ready.mean().unstack()
    .dropna().assign(diff=lambda d: 100 * (d[1.0] - d[0.0]))
)
loo_fe = {p: within_fe(df_cov[df_cov.parent != p]) for p in df_cov.parent.unique()}
df_cov_out = pd.DataFrame(
    [
        {"estimator": "raw deep-minus-shallow gap", "value_pp": round(raw_gap, 2),
         "n": len(df_cov)},
        {"estimator": "parent fixed-effect coefficient", "value_pp": round(fe_coef, 2),
         "n": len(df_cov)},
        {"estimator": "mean paired within-parent difference",
         "value_pp": round(paired["diff"].mean(), 2), "n": len(paired)},
        {"estimator": "median paired within-parent difference",
         "value_pp": round(paired["diff"].median(), 2), "n": len(paired)},
        {"estimator": "leave-one-parent-out FE minimum",
         "value_pp": round(min(loo_fe.values()), 2), "n": len(loo_fe)},
        {"estimator": "leave-one-parent-out FE maximum",
         "value_pp": round(max(loo_fe.values()), 2), "n": len(loo_fe)},
    ]
)
write_table(df_cov_out, "adj_coverage_depth_estimators")
print("\ncoverage depth gradient:\n", df_cov_out.to_string(index=False))
print("LOO min driven by dropping:", min(loo_fe, key=loo_fe.get))
print("LOO max driven by dropping:", max(loo_fe, key=loo_fe.get))


# GOAL: C-F001 DOES EVERY UIN HAVE EXACTLY ONE LEVEL-0 ENTITY?

n_uin = df_entity.uin.nunique()
uin_root = df_entity[df_entity.level == 0].groupby("uin").size()
print("\nUINs:", n_uin, "| UINs with a level-0 entity:", len(uin_root))
print("UINs with more than one level-0 entity:", int((uin_root > 1).sum()))
missing_uin = sorted(set(df_entity.uin.unique()) - set(uin_root.index))
df_missing = df_entity[df_entity.uin.isin(missing_uin)]
print("UINs with NO level-0 entity:", missing_uin,
      "| entities under them:", len(df_missing),
      "| parents:", sorted(df_missing.parent.unique()))


# GOAL: C-F002 DUTCH GATEWAY AMPLIFICATION, RECHECKED

df_root = df_entity[df_entity.level == 0].copy()
df_gate = (
    df_root.groupby("entity_country")
    .agg(gateways=("target_id", "size"), parents=("parent", "nunique"),
         mean_desc=("n_descendants", "mean"), median_desc=("n_descendants", "median"),
         total_desc=("n_descendants", "sum"))
    .query("gateways >= 3").sort_values("mean_desc", ascending=False).round(2)
    .reset_index()
)
write_table(df_gate, "adj_gateway_amplification_recheck")
print("\n", df_gate.head(8).to_string(index=False))
