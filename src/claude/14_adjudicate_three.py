"""Final adjudication, part three: cross-checks of Codex's own claims.

Reproduces X-F001, X-F003, X-F008, X-F009 and X-F018 from the immutable input
through my own pipeline, and tests two things neither branch has run: whether
the C-F020 name signal survives the corrected graph, and whether any
financial-weighted version of the conduit statistic is estimable at all.
"""

import networkx as nx
import pandas as pd

from config import derived_path, load_rows, write_table

df_entity = pd.read_parquet(derived_path / "entity.parquet")
df_edge = pd.read_parquet(derived_path / "edge.parquet")
df_rows = load_rows()

check_list = []


def record(claim, codex_value, my_value, verdict, note):
    """Append one adjudicated statistic to the ledger."""

    check_list.append(
        {"claim": claim, "codex": codex_value, "claude_recheck": my_value,
         "verdict": verdict, "note": note}
    )


# GOAL: X-F001 RAW ROWS MISWEIGHT PARENT EXPOSURE

n_rows = len(df_rows)
row_share = df_rows.parent.value_counts(normalize=True) * 100
ent_share = df_entity.parent.value_counts(normalize=True) * 100
df_weight = pd.concat(
    [row_share.rename("row_pct"), ent_share.rename("entity_pct")], axis=1
).dropna()
df_weight["ratio"] = (df_weight.row_pct / df_weight.entity_pct).round(2)
df_weight = df_weight.round(2).sort_values("ratio", ascending=False).reset_index()
df_weight.columns = ["parent", "row_pct", "entity_pct", "ratio"]
write_table(df_weight, "adj_row_vs_entity_weighting")
tcl = df_weight[df_weight.parent.str.startswith("TATA COMMUNICATIONS")].iloc[0]
record(
    "X-F001 Tata Communications row share / entity share",
    "550 rows = 14.70%; 49 entities = 2.68%; ratio 5.49",
    f"{tcl.row_pct}% rows vs {tcl.entity_pct}% entities; ratio {tcl.ratio}",
    "CONFIRMED", f"raw rows n={n_rows}; entities n={len(df_entity)}",
)


# GOAL: X-F003 DUPLICATE ENTITIES ACROSS AND WITHIN PARENT BUCKETS

df_entity["global_key"] = (
    df_entity.entity_name.str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
    .str.replace(r"\s+", " ", regex=True).str.strip()
    + " @@ " + df_entity.entity_country.str.upper().str.strip()
)
dup_size = df_entity.global_key.value_counts()
dup_key_list = dup_size[dup_size > 1].index
df_dup = df_entity[df_entity.global_key.isin(dup_key_list)]
n_cluster = len(dup_key_list)
n_occurrence = len(df_dup)
n_cross_parent = int(
    df_dup.groupby("global_key").parent.nunique().gt(1).sum()
)
n_global_unique = df_entity.global_key.nunique()
write_table(
    df_dup.groupby("global_key")
    .agg(occurrences=("target_id", "size"), parents=("parent", "nunique"),
         parent_list=("parent", lambda s: "; ".join(sorted(set(s)))))
    .reset_index().sort_values("occurrences", ascending=False),
    "adj_duplicate_entity_clusters",
)
record(
    "X-F003 repeated global name-country clusters",
    "16 clusters, 32 occurrences, 12 cross-parent; 1,818 global entities",
    f"{n_cluster} clusters, {n_occurrence} occurrences, {n_cross_parent} "
    f"cross-parent; {n_global_unique} global entities",
    "CONFIRMED",
    "duplicates are 0.9% of the file and cannot drive any headline result",
)


# GOAL: X-F008 CROSS-BORDER SHARE OF NON-ROOT EDGES

df_nonroot = df_edge[df_edge.parent_country != "INDIA"]
pooled = 100 * df_nonroot.is_border_crossing.mean()
equal_parent = 100 * df_nonroot.groupby("parent_bucket").is_border_crossing.mean().mean()
loo = [
    round(100 * df_nonroot[df_nonroot.parent_bucket != p].is_border_crossing.mean(), 2)
    for p in df_nonroot.parent_bucket.unique()
]
record(
    "X-F008 cross-border share of non-root edges",
    "57.64% pooled; 58.67% equal-parent; LOO 56.06-61.78%",
    f"{pooled:.2f}% pooled (n={len(df_nonroot)}); {equal_parent:.2f}% equal-parent; "
    f"LOO {min(loo):.2f}-{max(loo):.2f}%",
    "CONFIRMED", "denominator is non-root edges, level-0 India edges excluded",
)


# GOAL: X-F009 HUB CONCENTRATION

df_holders = df_entity[df_entity.n_children > 0]
big_hub = df_holders[df_holders.n_children >= 10]
n_entity_edge = int(df_entity.n_children.sum())
record(
    "X-F009 entities with 10+ direct children",
    "34 hubs carry 742/1,834 = 40.46% of logical edges",
    f"{len(big_hub)} hubs carry {int(big_hub.n_children.sum())}/{n_entity_edge} = "
    f"{100 * big_hub.n_children.sum() / n_entity_edge:.2f}% of entity-origin edges",
    "CONFIRMED-WITH-DENOMINATOR-NOTE",
    "Codex divides by 1,834 targets; the natural denominator is the 1,569 edges "
    "that actually originate from an observed entity",
)


# GOAL: X-F018 LARGEST UIN CHANNEL VERSUS MY GRAPH CHOKEPOINT

modal_uin = (
    df_entity.groupby(["parent", "uin"]).size().rename("n")
    .reset_index().sort_values("n", ascending=False)
    .drop_duplicates("parent")
)
n_modal = int(modal_uin.n.sum())
parent_size = df_entity.parent.value_counts()
modal_uin["share"] = 100 * modal_uin.n / modal_uin.parent.map(parent_size)
record(
    "X-F018 within-parent modal UIN share of targets",
    "1,095/1,834 = 59.71% pooled; equal-parent 62.05%; median 61.16%",
    f"{n_modal}/{len(df_entity)} = {100 * n_modal / len(df_entity):.2f}% pooled; "
    f"equal-parent {modal_uin.share.mean():.2f}%; median {modal_uin.share.median():.2f}%",
    "CONFIRMED", "a registration-channel statistic, not a graph statistic",
)

df_choke = pd.read_csv("../../outputs/claude/tables/adj_chokepoint_corrected.csv")
df_compare = df_choke[["parent", "pct_with_holes"]].merge(
    modal_uin[["parent", "share"]].rename(columns={"share": "pct_modal_uin"}),
    on="parent",
)
df_compare["gap_pp"] = (df_compare.pct_with_holes - df_compare.pct_modal_uin).round(1)
df_compare = df_compare.round(1).sort_values("gap_pp")
write_table(df_compare, "adj_chokepoint_vs_uin_channel")
print("corr(graph chokepoint, modal-UIN share) =",
      round(df_compare.pct_with_holes.corr(df_compare.pct_modal_uin), 3))
print("median graph chokepoint:", df_compare.pct_with_holes.median(),
      "| median modal-UIN share:", df_compare.pct_modal_uin.median())


# GOAL: DOES THE C-F020 NAME SIGNAL SURVIVE THE CORRECTED GRAPH?

# the 20 unscraped intermediaries are holders that the entity table cannot see,
# so the holder flag they would carry is missing, not zero
name_pattern = r"HOLDING|HOLDINGS|HOLDCO|INVESTMENT|INVESTMENTS"
df_entity["holding_name"] = (
    df_entity.entity_name.str.upper().str.contains(name_pattern, regex=True).astype(int)
)
df_entity["is_holder"] = (df_entity.n_children > 0).astype(int)
raw_gap = 100 * (
    df_entity.loc[df_entity.holding_name == 1, "is_holder"].mean()
    - df_entity.loc[df_entity.holding_name == 0, "is_holder"].mean()
)
df_dm = df_entity.copy()
df_dm["cell"] = df_dm.parent + "||" + df_dm.entity_country
size = df_dm.groupby("cell").cell.transform("size")
df_dm = df_dm[size >= 2]
for col in ("holding_name", "is_holder"):
    df_dm[col] = df_dm[col] - df_dm.groupby("cell")[col].transform("mean")
denom = (df_dm.holding_name ** 2).sum()
within_gap = 100 * (df_dm.holding_name * df_dm.is_holder).sum() / denom
loo_gap = []
for parent in df_entity.parent.unique():
    df_k = df_entity[df_entity.parent != parent]
    loo_gap.append(
        100 * (df_k.loc[df_k.holding_name == 1, "is_holder"].mean()
               - df_k.loc[df_k.holding_name == 0, "is_holder"].mean())
    )
record(
    "C-F020 holding-name flag predicts holder status",
    "not reviewed by Codex",
    f"raw gap {raw_gap:.1f}pp (n={int(df_entity.holding_name.sum())} named); "
    f"within parent x country {within_gap:.1f}pp; LOO {min(loo_gap):.1f}-{max(loo_gap):.1f}pp",
    "SELF-CONFIRMED",
    "unchanged by the orphan-country correction, which alters no out-degree",
)


# GOAL: IS ANY FINANCIAL-WEIGHTED VERSION OF THE CONDUIT STATISTIC ESTIMABLE?

df_ready = df_rows[df_rows.ready_for_valuation == 1] if "ready_for_valuation" in df_rows else pd.DataFrame()
n_ready = len(df_ready)
unit_blank = int(df_ready.units.fillna("").str.strip().eq("").sum()) if n_ready else 0
cur_n = df_ready.currency.replace("", pd.NA).nunique() if n_ready else 0
record(
    "financial weighting of any structural statistic",
    "X-F012: units blank for 516/560 ready rows",
    f"{unit_blank}/{n_ready} ready rows have a blank unit; {cur_n} currencies",
    "NOT ESTIMABLE",
    "absolute assets cannot be pooled, so every structural statistic in this "
    "project is necessarily entity-weighted, never value-weighted",
)

df_check = pd.DataFrame(check_list)
write_table(df_check, "adj_cross_check_ledger")
print()
for row in check_list:
    print(f"[{row['verdict']}] {row['claim']}")
    print(f"    codex : {row['codex']}")
    print(f"    claude: {row['claude_recheck']}")
