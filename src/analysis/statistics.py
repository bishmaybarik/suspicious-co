"""Final estimands, robustness checks, and publication tables."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

import networkx as nx
import numpy as np
import pandas as pd

from .config import DECLARED_CENTRES, PARENT_SHORT
from .data_model import AnalysisData


TOP_THREE_UPSTREAM = {
    "NETHERLANDS",
    "UNITED STATES OF AMERICA",
    "MAURITIUS",
}
HOLDING_NAME_PATTERN = re.compile(
    r"\b(?:HOLDING|HOLDINGS|HOLDCO|INVESTMENT|INVESTMENTS)\b"
)


@dataclass(frozen=True)
class FinalResults:
    tables: dict[str, pd.DataFrame]
    metrics: dict[str, Any]
    plot_data: dict[str, pd.DataFrame]


def percent(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else np.nan


def hhi(values: pd.Series) -> float:
    counts = values.value_counts()
    shares = counts / counts.sum()
    return float(np.square(shares).sum())


def within_coefficient(
    frame: pd.DataFrame, outcome: str, treatment: str, fixed_effect: str
) -> float:
    work = frame[[outcome, treatment, fixed_effect]].dropna().copy()
    x = work[treatment].astype(float)
    y = work[outcome].astype(float)
    xw = x - x.groupby(work[fixed_effect]).transform("mean")
    yw = y - y.groupby(work[fixed_effect]).transform("mean")
    denominator = float(np.square(xw).sum())
    return float((xw * yw).sum() / denominator) if denominator else np.nan


def leave_one_parent_out(
    frame: pd.DataFrame, estimator: Callable[[pd.DataFrame], float]
) -> list[float]:
    return [
        estimator(frame[frame["parent"].ne(parent)])
        for parent in sorted(frame["parent"].unique())
    ]


def entity_coverage(data: AnalysisData) -> pd.DataFrame:
    coverage = (
        data.raw.groupby("target_id")
        .agg(
            any_source_found=("source_found", "max"),
            # The upstream variables_parsed flag is narrower than the
            # adjudicated balance-sheet gate. A target has a parsed balance
            # sheet when equity is numeric in at least one source row.
            any_balance_parsed=("equity", lambda values: values.notna().any()),
            any_ready=("ready_for_valuation", "max"),
        )
        .reset_index()
    )
    return data.occurrences[
        ["target_id", "parent", "level", "group_entity_id"]
    ].merge(coverage, on="target_id", how="left", validate="one_to_one")


def repeated_evidence_audit(data: AnalysisData) -> tuple[pd.DataFrame, dict[str, int]]:
    preferred = data.preferred.copy()
    parsed = preferred.dropna(
        subset=["total_assets", "total_liabilities", "equity"]
    ).copy()
    signature_columns = [
        "fiscal_year",
        "currency",
        "units",
        "total_assets",
        "total_liabilities",
        "equity",
    ]
    parsed["signature_id"] = parsed.groupby(
        signature_columns, dropna=False, sort=False
    ).ngroup()
    sizes = parsed.groupby("signature_id").size()
    repeated_ids = set(sizes[sizes.gt(1)].index)
    repeated = parsed[parsed["signature_id"].isin(repeated_ids)]

    detail_rows: list[dict[str, Any]] = []
    for signature_id, group in repeated.groupby("signature_id"):
        same_url = group["source_url"].nunique(dropna=False) == 1
        different_names = group["entity_name"].nunique(dropna=False) > 1
        identical_evidence = all(
            group[column].nunique(dropna=False) == 1
            for column in [
                "total_assets_evidence",
                "total_liabilities_evidence",
                "equity_evidence",
            ]
        )
        detail_rows.append(
            {
                "signature_id": int(signature_id),
                "rows": len(group),
                "same_source_url": same_url,
                "different_entity_names": different_names,
                "same_url_different_names": same_url and different_names,
                "identical_core_evidence": identical_evidence,
                "ready_rows": int(group["ready_for_valuation"].eq(1).sum()),
            }
        )
    detail = pd.DataFrame(detail_rows)

    ready = preferred[preferred["ready_for_valuation"].eq(1)].copy()
    repeated_ready = ready.index.isin(repeated.index)
    sign_bad = ~(
        ready["total_assets"].gt(0) & ready["total_liabilities"].ge(0)
    )
    proven_ids = set(
        detail.loc[
            detail["same_url_different_names"]
            & detail["identical_core_evidence"],
            "signature_id",
        ]
    )
    proven_rows = parsed[parsed["signature_id"].isin(proven_ids)]
    proven_ready = ready.index.isin(proven_rows.index)

    metrics = {
        "parsed_rows": len(parsed),
        "repeated_signatures": len(repeated_ids),
        "repeated_rows": len(repeated),
        "proven_reuse_clusters": len(proven_ids),
        "ready_repeated_rows": int(repeated_ready.sum()),
        "sign_bad_ready_rows": int(sign_bad.sum()),
        "broad_flagged_ready_rows": int((repeated_ready | sign_bad).sum()),
        "broad_unflagged_ready_rows": int((~repeated_ready & ~sign_bad).sum()),
        "strict_flagged_ready_rows": int((proven_ready | sign_bad).sum()),
        "strict_unflagged_ready_rows": int((~proven_ready & ~sign_bad).sum()),
    }
    return detail.sort_values(["rows", "signature_id"], ascending=[False, True]), metrics


def sample_construction(
    data: AnalysisData, evidence_metrics: dict[str, int]
) -> pd.DataFrame:
    nonroot = data.edges[data.edges["reported_level"].gt(0)]
    expected = nonroot["link_status"].isin(
        ["exact_expected_level", "normalized_expected_level"]
    )
    missing = nonroot[nonroot["parent_node_type"].eq("unobserved_entity")]
    coverage = entity_coverage(data)
    ready = data.preferred[data.preferred["ready_for_valuation"].eq(1)]
    sign_plausible = ready[
        ready["total_assets"].gt(0) & ready["total_liabilities"].ge(0)
    ]
    pl_valid = sign_plausible[
        sign_plausible["pl_identity_ok"].eq(1)
        & sign_plausible["profit_after_tax"].notna()
    ]
    rows = [
        ("Raw source rows", len(data.raw), "source candidate", "No"),
        (
            "Preferred target-year rows",
            len(data.preferred),
            "target_id × fiscal_year",
            "No",
        ),
        (
            "Structural target occurrences",
            len(data.occurrences),
            "target_id",
            "Primary exposure/path unit",
        ),
        (
            "Parent-scoped normalized entity candidates",
            len(data.group_entities),
            "parent × normalized name-country",
            "Primary group-architecture unit",
        ),
        (
            "Global normalized entity candidates",
            len(data.global_entities),
            "normalized name-country",
            "Cross-parent unique-company sensitivity",
        ),
        ("UINs", data.occurrences["uin"].nunique(), "uin", "Registration/mapping unit"),
        (
            "Observed level-0 targets",
            int(data.occurrences["level"].eq(0).sum()),
            "target occurrence",
            "Observed first foreign hop",
        ),
        (
            "Ultimate-parent buckets",
            data.occurrences["parent"].nunique(),
            "source parent label",
            "Equal-parent/LOO unit",
        ),
        (
            "Nonroot edge occurrences",
            len(nonroot),
            "reported child-parent relation",
            "Level-0 edges excluded",
        ),
        (
            "Expected-prior-level observed links",
            int(expected.sum()),
            "nonroot edge",
            "Observed parent at level minus one",
        ),
        (
            "Edges to named but unscraped parents",
            len(missing),
            "nonroot edge",
            "Country retained; identity unresolved",
        ),
        (
            "Normalized missing-parent names",
            missing["parent_node_id"].nunique(),
            "unresolved node",
            "Conservative name-country key",
        ),
        (
            "Complete observed paths",
            int(data.paths["path_status"].eq("complete_to_ultimate_parent").sum()),
            "target path",
            "Reaches Indian parent through observed entities",
        ),
        (
            "Targets with any located source",
            int(coverage["any_source_found"].sum()),
            "target occurrence",
            "Financial coverage gate",
        ),
        (
            "Targets with parsed balance sheet",
            int(coverage["any_balance_parsed"].sum()),
            "target occurrence",
            "Financial coverage gate",
        ),
        (
            "Targets valuation-ready at least once",
            int(coverage["any_ready"].sum()),
            "target occurrence",
            "Selected financial subset",
        ),
        (
            "Ready target-year rows",
            len(ready),
            "preferred target-year",
            "Upstream ready flag",
        ),
        (
            "Sign-plausible ready rows",
            len(sign_plausible),
            "preferred target-year",
            "Assets > 0; liabilities ≥ 0",
        ),
        (
            "P&L-valid rows",
            len(pl_valid),
            "preferred target-year",
            "Sign-plausible and P&L identity valid",
        ),
        (
            "Ready rows unflagged by broad duplicate/sign screen",
            evidence_metrics["broad_unflagged_ready_rows"],
            "preferred target-year",
            "Not a validated final financial sample",
        ),
    ]
    return pd.DataFrame(rows, columns=["stage", "count", "unit", "use_or_caution"])


def subtree_and_parent_architecture(
    data: AnalysisData,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    occurrence = data.occurrences
    entities = data.group_entities
    logical = data.logical_edges
    target_weight = entities.set_index("group_entity_id")["target_occurrences"]
    coverage = entity_coverage(data)
    coverage_parent = coverage.groupby("parent")["any_ready"].mean()
    rows: list[dict[str, Any]] = []

    for parent, parent_entities in entities.groupby("parent", sort=True):
        parent_occ = occurrence[occurrence["parent"].eq(parent)]
        parent_edges = logical[logical["parent"].eq(parent)]
        graph = nx.DiGraph()
        graph.add_edges_from(
            parent_edges[["parent_node_id", "child_group_entity_id"]].itertuples(
                index=False, name=None
            )
        )
        if not nx.is_directed_acyclic_graph(graph):
            raise AssertionError(f"cycle in normalized graph for {parent}")
        entity_nodes = set(parent_entities["group_entity_id"])
        observed_nodes = set(
            parent_edges.loc[
                parent_edges["parent_node_type"].eq("observed_entity"),
                "parent_node_id",
            ]
        )
        missing_nodes = set(
            parent_edges.loc[
                parent_edges["parent_node_type"].eq("unobserved_entity"),
                "parent_node_id",
            ]
        )
        root_nodes = parent_edges.loc[
            parent_edges["parent_node_type"].eq("ultimate_parent"),
            "parent_node_id",
        ].unique()
        if len(root_nodes) != 1:
            raise AssertionError(f"expected one root node for {parent}")
        root = root_nodes[0]
        reachable_before = nx.descendants(graph, root) & entity_nodes

        observed_candidates: list[tuple[int, int, str]] = []
        dominator_candidates: list[tuple[int, str]] = []
        for node in observed_nodes:
            descendants = nx.descendants(graph, node) & entity_nodes
            target_descendants = int(target_weight.reindex(descendants).sum())
            observed_candidates.append((target_descendants, len(descendants), node))
            graph_without = graph.copy()
            graph_without.remove_node(node)
            reachable_after = nx.descendants(graph_without, root) & entity_nodes
            detached = (reachable_before - reachable_after) - {node}
            dominator_candidates.append((len(detached), node))

        if observed_candidates:
            observed_target, observed_entity, observed_node = max(observed_candidates)
            detached_entity, dominator_node = max(dominator_candidates)
        else:
            observed_target = observed_entity = detached_entity = 0
            observed_node = dominator_node = ""

        inclusive_candidates: list[tuple[int, str]] = []
        for node in observed_nodes | missing_nodes:
            inclusive_candidates.append(
                (len(nx.descendants(graph, node) & entity_nodes), node)
            )
        inclusive_entity, inclusive_node = max(inclusive_candidates, default=(0, ""))

        def node_label(node: str, field: str) -> str:
            if not node:
                return ""
            observed = parent_entities[parent_entities["group_entity_id"].eq(node)]
            if not observed.empty:
                return str(
                    observed.iloc[0][
                        "canonical_entity_name" if field == "name" else "entity_country"
                    ]
                )
            source = parent_edges[parent_edges["parent_node_id"].eq(node)]
            if source.empty:
                return ""
            return str(
                source.iloc[0][
                    "matched_parent_name" if field == "name" else "matched_parent_country"
                ]
            )

        country_counts = parent_entities["entity_country"].value_counts()
        top_country = str(country_counts.index[0])
        complete = data.paths[
            data.paths["parent"].eq(parent)
            & data.paths["path_status"].eq("complete_to_ultimate_parent")
        ]
        nonroot = data.edges[
            data.edges["parent"].eq(parent) & data.edges["reported_level"].gt(0)
        ]
        modal = parent_occ.groupby("uin").size().max()
        rows.append(
            {
                "parent": parent,
                "parent_short": PARENT_SHORT.get(parent, parent.title()),
                "target_occurrences": len(parent_occ),
                "normalized_entities": len(parent_entities),
                "raw_source_rows": int(data.raw["parent"].eq(parent).sum()),
                "row_share_to_entity_share_ratio": (
                    data.raw["parent"].eq(parent).mean()
                    / (len(parent_entities) / len(data.group_entities))
                ),
                "uins": parent_occ["uin"].nunique(),
                "observed_level0_targets": int(parent_occ["level"].eq(0).sum()),
                "jurisdictions": parent_entities["entity_country"].nunique(),
                "jurisdiction_hhi": hhi(parent_entities["entity_country"]),
                "top_jurisdiction": top_country,
                "top_jurisdiction_pct": percent(country_counts.iloc[0], len(parent_entities)),
                "maximum_reported_level": int(parent_occ["level"].max()),
                "maximum_reconstructed_level_complete": (
                    float(complete["reconstructed_level"].max()) if len(complete) else np.nan
                ),
                "complete_path_pct": percent(len(complete), len(parent_occ)),
                "modal_uin_target_pct": percent(modal, len(parent_occ)),
                "largest_observed_subtree_entity_pct": percent(
                    observed_entity, len(parent_entities) - 1
                ),
                "largest_observed_subtree_name": node_label(observed_node, "name"),
                "largest_observed_subtree_country": node_label(observed_node, "country"),
                "named_node_inclusive_subtree_pct": percent(
                    inclusive_entity, len(parent_entities) - 1
                ),
                "named_node_inclusive_subtree_name": node_label(inclusive_node, "name"),
                "named_node_inclusive_subtree_country": node_label(
                    inclusive_node, "country"
                ),
                "strict_dag_dominator_entity_pct": percent(
                    detached_entity, len(parent_entities) - 1
                ),
                "strict_dag_dominator_name": node_label(dominator_node, "name"),
                "root_reachable_entity_pct": percent(
                    len(reachable_before), len(parent_entities)
                ),
                "nonroot_cross_border_edge_pct": percent(
                    nonroot["cross_border_edge"].sum(), len(nonroot)
                ),
                "valuation_ready_target_pct": 100 * coverage_parent[parent],
            }
        )

    parent_table = pd.DataFrame(rows).sort_values(
        "normalized_entities", ascending=False
    )
    concentration = parent_table[parent_table["target_occurrences"].ge(15)].copy()
    concentration = concentration.sort_values(
        "largest_observed_subtree_entity_pct", ascending=False
    )
    return parent_table, concentration


def gateway_amplification(
    data: AnalysisData,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    roots = data.occurrences[data.occurrences["level"].eq(0)].drop_duplicates(
        "group_entity_id"
    )
    roots = roots[
        ["parent", "group_entity_id", "entity_country_std", "uin", "entity_name"]
    ]
    records: list[dict[str, Any]] = []
    for parent, parent_edges in data.logical_edges.groupby("parent"):
        graph = nx.DiGraph()
        graph.add_edges_from(
            parent_edges[["parent_node_id", "child_group_entity_id"]].itertuples(
                index=False, name=None
            )
        )
        entity_nodes = set(
            data.group_entities.loc[
                data.group_entities["parent"].eq(parent), "group_entity_id"
            ]
        )
        for root in roots[roots["parent"].eq(parent)].itertuples(index=False):
            descendants = nx.descendants(graph, root.group_entity_id) & entity_nodes
            branch_sizes: list[int] = []
            for child in graph.successors(root.group_entity_id):
                branch = {child} | (nx.descendants(graph, child) & entity_nodes)
                branch_sizes.append(len(branch & descendants))
            largest_branch = max(branch_sizes, default=0)
            records.append(
                {
                    "parent": parent,
                    "parent_short": PARENT_SHORT.get(parent, parent.title()),
                    "gateway_group_entity_id": root.group_entity_id,
                    "gateway_name": root.entity_name,
                    "gateway_country": root.entity_country_std,
                    "uin": root.uin,
                    "descendants": len(descendants),
                    "direct_child_branches": graph.out_degree(root.group_entity_id),
                    "largest_branch_share": (
                        largest_branch / len(descendants) if descendants else np.nan
                    ),
                }
            )
    gateway = pd.DataFrame(records)

    summary_rows: list[dict[str, Any]] = []
    for country, group in gateway.groupby("gateway_country"):
        if len(group) < 3:
            continue
        parent_means = group.groupby("parent")["descendants"].mean()
        loo = leave_one_parent_out(group, lambda frame: frame["descendants"].mean())
        balanced = group[group["largest_branch_share"].le(0.5)]
        summary_rows.append(
            {
                "gateway_country": country,
                "gateways": len(group),
                "parents": group["parent"].nunique(),
                "mean_descendants": group["descendants"].mean(),
                "median_descendants": group["descendants"].median(),
                "parent_equal_mean_descendants": parent_means.mean(),
                "loo_min_mean_descendants": min(loo),
                "loo_max_mean_descendants": max(loo),
                "gateways_without_majority_child_branch": len(balanced),
                "mean_descendants_without_majority_child_branch": balanced[
                    "descendants"
                ].mean(),
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        "mean_descendants", ascending=False
    )
    return gateway.sort_values(
        ["gateway_country", "descendants"], ascending=[True, False]
    ), summary


def upstream_frame(data: AnalysisData) -> pd.DataFrame:
    strict = data.path_steps[data.path_steps["step_from_terminal"].gt(0)]
    country_sets = strict.groupby("terminal_target_id")["country"].agg(
        lambda values: frozenset(values.dropna())
    )
    frame = data.occurrences[
        [
            "target_id",
            "parent",
            "group_entity_id",
            "immediate_parent",
            "level",
        ]
    ].copy()
    frame["upstream_countries"] = frame["target_id"].map(country_sets)
    frame["upstream_countries"] = frame["upstream_countries"].map(
        lambda value: value if isinstance(value, frozenset) else frozenset()
    )
    status = data.paths.set_index("target_id")["path_status"]
    frame["complete_path"] = frame["target_id"].map(status).eq(
        "complete_to_ultimate_parent"
    )
    return frame


def jurisdiction_roles(
    data: AnalysisData,
    upstream: pd.DataFrame,
    gateway_summary: pd.DataFrame,
) -> pd.DataFrame:
    entities = data.group_entities
    observed_parent_edges = data.logical_edges[
        data.logical_edges["parent_node_type"].eq("observed_entity")
    ]
    unique_intermediaries = observed_parent_edges.drop_duplicates("parent_node_id")
    resident = entities["entity_country"].value_counts()
    resident_parents = entities.groupby("entity_country")["parent"].nunique()
    intermediary = unique_intermediaries["matched_parent_country"].value_counts()
    outgoing = (
        observed_parent_edges.groupby("matched_parent_country")
        .agg(
            observed_entity_origin_edges=("logical_edge_id", "size"),
            cross_border_child_edges=(
                "child_country",
                lambda values: 0,
            ),
            destination_jurisdictions=("child_country", "nunique"),
            intermediary_parents=("parent", "nunique"),
        )
    )
    cross = observed_parent_edges.assign(
        cross_border=lambda frame: frame["matched_parent_country"].ne(
            frame["child_country"]
        )
    ).groupby("matched_parent_country")["cross_border"].sum()
    outgoing["cross_border_child_edges"] = cross

    countries = sorted(
        (set(entities["entity_country"].dropna()) - {"INDIA"})
        | (set().union(*upstream["upstream_countries"].tolist()) - {"INDIA"})
    )
    parents = sorted(upstream["parent"].unique())
    rows: list[dict[str, Any]] = []
    for country in countries:
        exposed = upstream["upstream_countries"].map(lambda values: country in values)
        by_parent = upstream.assign(exposed=exposed).groupby("parent")["exposed"].mean()
        loo = [
            percent(
                exposed[upstream["parent"].ne(parent)].sum(),
                upstream["parent"].ne(parent).sum(),
            )
            for parent in parents
        ]
        residents = int(resident.get(country, 0))
        below = int(exposed.sum())
        out = outgoing.loc[country] if country in outgoing.index else None
        gateway_row = gateway_summary[gateway_summary["gateway_country"].eq(country)]
        rows.append(
            {
                "jurisdiction": country,
                "resident_entities": residents,
                "resident_entity_pct": percent(residents, len(entities)),
                "resident_parent_groups": int(resident_parents.get(country, 0)),
                "unique_observed_intermediaries": int(intermediary.get(country, 0)),
                "unique_intermediary_pct": percent(
                    intermediary.get(country, 0), len(unique_intermediaries)
                ),
                "observed_entity_origin_edges": (
                    int(out["observed_entity_origin_edges"]) if out is not None else 0
                ),
                "cross_border_child_edges": (
                    int(out["cross_border_child_edges"]) if out is not None else 0
                ),
                "destination_jurisdictions": (
                    int(out["destination_jurisdictions"]) if out is not None else 0
                ),
                "target_paths_below": below,
                "pooled_target_path_pct": percent(below, len(upstream)),
                "equal_parent_target_path_pct": 100 * by_parent.mean(),
                "loo_min_target_path_pct": min(loo),
                "loo_max_target_path_pct": max(loo),
                "parents_affected": int(upstream.loc[exposed, "parent"].nunique()),
                "target_paths_below_per_resident": (
                    below / residents if residents else np.nan
                ),
                "level0_gateways": (
                    int(gateway_row.iloc[0]["gateways"]) if not gateway_row.empty else 0
                ),
                "mean_gateway_descendants": (
                    float(gateway_row.iloc[0]["mean_descendants"])
                    if not gateway_row.empty
                    else np.nan
                ),
                "median_gateway_descendants": (
                    float(gateway_row.iloc[0]["median_descendants"])
                    if not gateway_row.empty
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["target_paths_below", "resident_entities"], ascending=False
    )


def greedy_cover(upstream: pd.DataFrame, max_steps: int = 8) -> pd.DataFrame:
    countries = sorted(
        set().union(*upstream["upstream_countries"].tolist()) - {"INDIA"}
    )
    remaining = set(upstream.index)
    rows: list[dict[str, Any]] = []
    for step in range(1, max_steps + 1):
        gain, country = max(
            (
                sum(
                    country in upstream.at[index, "upstream_countries"]
                    for index in remaining
                ),
                country,
            )
            for country in countries
        )
        if gain == 0:
            break
        remaining = {
            index
            for index in remaining
            if country not in upstream.at[index, "upstream_countries"]
        }
        rows.append(
            {
                "step": step,
                "jurisdiction": country,
                "newly_covered_target_paths": gain,
                "cumulative_target_path_pct": percent(
                    len(upstream) - len(remaining), len(upstream)
                ),
            }
        )
        countries.remove(country)
    return pd.DataFrame(rows)


def depth_audit(data: AnalysisData) -> tuple[pd.DataFrame, pd.DataFrame]:
    occurrence = data.occurrences
    complete = data.paths[
        data.paths["path_status"].eq("complete_to_ultimate_parent")
    ]
    levels = range(0, int(occurrence["level"].max()) + 1)
    rows = []
    for level in levels:
        reported = int(occurrence["level"].eq(level).sum())
        reconstructed = int(complete["reconstructed_level"].eq(level).sum())
        rows.append(
            {
                "level": level,
                "reported_target_occurrences": reported,
                "reported_pct_all_targets": percent(reported, len(occurrence)),
                "reconstructed_complete_paths": reconstructed,
                "reconstructed_pct_complete_paths": percent(
                    reconstructed, len(complete)
                ),
            }
        )
    distribution = pd.DataFrame(rows)

    deep = occurrence["level"].ge(5)
    parent_rates = occurrence.assign(deep=deep).groupby("parent")["deep"].mean()
    loo = leave_one_parent_out(
        occurrence.assign(deep=deep), lambda frame: 100 * frame["deep"].mean()
    )
    mismatch = complete[complete["reported_level_matches_reconstruction"].eq(0)]
    manufacturing = occurrence[
        occurrence["sector_label"].eq("Manufacturing (General)")
    ]
    deep_manufacturing = manufacturing[manufacturing["level"].ge(5)]
    top_two_names = {"SAMVARDHANA MOTHERSON INTERNATI", "HINDALCO INDUSTRIES LIMITED"}
    summary_rows = [
        (
            "Reported level 2+",
            int(occurrence["level"].ge(2).sum()),
            len(occurrence),
            percent(occurrence["level"].ge(2).sum(), len(occurrence)),
            "target occurrences",
        ),
        (
            "Reported level 5+",
            int(deep.sum()),
            len(occurrence),
            percent(deep.sum(), len(occurrence)),
            "target occurrences",
        ),
        (
            "Reported level 5+, equal-parent",
            np.nan,
            len(parent_rates),
            100 * parent_rates.mean(),
            "parent mean",
        ),
        (
            "Reported level 5+, LOO minimum",
            np.nan,
            27,
            min(loo),
            "target occurrences after one parent omitted",
        ),
        (
            "Reported level 5+, LOO maximum",
            np.nan,
            27,
            max(loo),
            "target occurrences after one parent omitted",
        ),
        (
            "Reconstructed distance 5+",
            int(complete["reconstructed_level"].ge(5).sum()),
            len(complete),
            percent(complete["reconstructed_level"].ge(5).sum(), len(complete)),
            "complete paths",
        ),
        (
            "Reported/reconstructed mismatch",
            len(mismatch),
            len(complete),
            percent(len(mismatch), len(complete)),
            "complete paths",
        ),
        (
            "Motherson share of mismatches",
            int(mismatch["parent"].eq("SAMVARDHANA MOTHERSON INTERNATI").sum()),
            len(mismatch),
            percent(
                mismatch["parent"].eq("SAMVARDHANA MOTHERSON INTERNATI").sum(),
                len(mismatch),
            ),
            "mismatching complete paths",
        ),
        (
            "Manufacturing targets at reported level 5+",
            len(deep_manufacturing),
            len(manufacturing),
            percent(len(deep_manufacturing), len(manufacturing)),
            "manufacturing target occurrences",
        ),
        (
            "Motherson + Hindalco share of deep manufacturing",
            int(deep_manufacturing["parent"].isin(top_two_names).sum()),
            len(deep_manufacturing),
            percent(
                deep_manufacturing["parent"].isin(top_two_names).sum(),
                len(deep_manufacturing),
            ),
            "reported level-5+ manufacturing targets",
        ),
    ]
    summary = pd.DataFrame(
        summary_rows,
        columns=["statistic", "numerator", "denominator", "value_pct", "unit"],
    )
    return distribution, summary


def ownership_audit(data: AnalysisData) -> tuple[pd.DataFrame, dict[str, float]]:
    occurrence = data.occurrences
    nonroot = occurrence[occurrence["level"].gt(0)].copy()
    positive = nonroot[nonroot["stake"].gt(0)].copy()
    positive["depth_group"] = np.where(positive["level"].eq(1), "level 1", "level 2+")
    positive["fully_owned"] = positive["stake"].ge(99.5)
    rates = positive.groupby("depth_group")["fully_owned"].mean()
    parent_rates = positive.groupby(["parent", "depth_group"])["fully_owned"].mean()
    equal_rates = parent_rates.groupby("depth_group").mean()
    paired = parent_rates.unstack().dropna()
    without_reliance = positive[
        positive["parent"].ne("RELIANCE INDUSTRIES LTD")
    ]
    without_rates = without_reliance.groupby("depth_group")["fully_owned"].mean()

    comparison = data.preferred.dropna(subset=["stake", "shareholding_percent"])
    zero_comparison = comparison[comparison["stake"].eq(0)]
    metrics = {
        "level1_full_pct": 100 * rates["level 1"],
        "level2plus_full_pct": 100 * rates["level 2+"],
        "pooled_gap_pp": 100 * (rates["level 2+"] - rates["level 1"]),
        "equal_parent_gap_pp": 100
        * (equal_rates["level 2+"] - equal_rates["level 1"]),
        "paired_parent_gap_pp": 100
        * (paired["level 2+"] - paired["level 1"]).mean(),
        "paired_parent_median_gap_pp": 100
        * (paired["level 2+"] - paired["level 1"]).median(),
        "exclude_reliance_gap_pp": 100
        * (without_rates["level 2+"] - without_rates["level 1"]),
    }
    rows = [
        ("Level-0 stakes missing", int(occurrence["level"].eq(0).sum()), int(occurrence["level"].eq(0).sum()), 100.0, "level-0 targets"),
        ("Nonroot recorded zero stakes", int(nonroot["stake"].eq(0).sum()), len(nonroot), percent(nonroot["stake"].eq(0).sum(), len(nonroot)), "nonroot edges"),
        ("Positive nonroot stakes", len(positive), len(nonroot), percent(len(positive), len(nonroot)), "nonroot edges"),
        ("Rows with mapping stake and AOC share", len(comparison), len(data.preferred), percent(len(comparison), len(data.preferred)), "preferred target-years"),
        ("Zero mapping stake but positive AOC share", int(zero_comparison["shareholding_percent"].gt(0).sum()), len(zero_comparison), percent(zero_comparison["shareholding_percent"].gt(0).sum(), len(zero_comparison)), "comparable zero-stake rows"),
        ("Stake/AOC difference above 1 pp", int((comparison["stake"] - comparison["shareholding_percent"]).abs().gt(1).sum()), len(comparison), percent((comparison["stake"] - comparison["shareholding_percent"]).abs().gt(1).sum(), len(comparison)), "comparable rows"),
        ("Full ownership at level 1", int(positive[positive["depth_group"].eq("level 1")]["fully_owned"].sum()), int(positive["depth_group"].eq("level 1").sum()), metrics["level1_full_pct"], "positive-stake edges"),
        ("Full ownership at level 2+", int(positive[positive["depth_group"].eq("level 2+")]["fully_owned"].sum()), int(positive["depth_group"].eq("level 2+").sum()), metrics["level2plus_full_pct"], "positive-stake edges"),
        ("Pooled level-2+ minus level-1 gap", np.nan, len(positive), metrics["pooled_gap_pp"], "percentage points"),
        ("Equal-parent level-2+ minus level-1 gap", np.nan, len(parent_rates.index.get_level_values(0).unique()), metrics["equal_parent_gap_pp"], "percentage points"),
        ("Gap excluding Reliance", np.nan, len(without_reliance), metrics["exclude_reliance_gap_pp"], "percentage points"),
    ]
    return pd.DataFrame(rows, columns=["statistic", "numerator", "denominator", "value", "unit"]), metrics


def financial_audit(
    data: AnalysisData, evidence_metrics: dict[str, int]
) -> tuple[pd.DataFrame, dict[str, float]]:
    coverage = entity_coverage(data)
    ready = data.preferred[data.preferred["ready_for_valuation"].eq(1)].copy()
    sign_plausible = ready[
        ready["total_assets"].gt(0) & ready["total_liabilities"].ge(0)
    ]
    pl_valid = sign_plausible[
        sign_plausible["pl_identity_ok"].eq(1)
        & sign_plausible["profit_after_tax"].notna()
    ]
    coverage["ready"] = coverage["any_ready"].astype(float)
    coverage["deep"] = coverage["level"].ge(3).astype(float)
    raw_gap = 100 * (
        coverage.loc[coverage["deep"].eq(1), "ready"].mean()
        - coverage.loc[coverage["deep"].eq(0), "ready"].mean()
    )
    fe = 100 * within_coefficient(coverage, "ready", "deep", "parent")
    loo = [
        100 * within_coefficient(
            coverage[coverage["parent"].ne(parent)], "ready", "deep", "parent"
        )
        for parent in sorted(coverage["parent"].unique())
    ]
    parent_ready = coverage.groupby("parent")["ready"].mean()
    metrics = {
        "raw_depth_gap_pp": raw_gap,
        "parent_fe_depth_gap_pp": fe,
        "parent_fe_loo_min_pp": min(loo),
        "parent_fe_loo_max_pp": max(loo),
        "minimum_parent_ready_pct": 100 * parent_ready.min(),
        "maximum_parent_ready_pct": 100 * parent_ready.max(),
        "parents_with_zero_ready": int(parent_ready.eq(0).sum()),
    }
    rows = [
        ("Preferred target-year rows", len(data.preferred), len(data.preferred), 100.0, "preferred target-years"),
        ("Ready rows", len(ready), len(data.preferred), percent(len(ready), len(data.preferred)), "preferred target-years"),
        ("Sign-plausible ready rows", len(sign_plausible), len(ready), percent(len(sign_plausible), len(ready)), "ready rows"),
        ("P&L-valid rows", len(pl_valid), len(ready), percent(len(pl_valid), len(ready)), "ready rows"),
        ("Ready rows with blank units", int(ready["units"].isna().sum()), len(ready), percent(ready["units"].isna().sum(), len(ready)), "ready rows"),
        ("Targets with any source", int(coverage["any_source_found"].sum()), len(coverage), percent(coverage["any_source_found"].sum(), len(coverage)), "targets"),
        ("Targets with parsed balance sheet", int(coverage["any_balance_parsed"].sum()), len(coverage), percent(coverage["any_balance_parsed"].sum(), len(coverage)), "targets"),
        ("Targets ready at least once", int(coverage["any_ready"].sum()), len(coverage), percent(coverage["any_ready"].sum(), len(coverage)), "targets"),
        ("Repeated numeric signatures", evidence_metrics["repeated_signatures"], evidence_metrics["parsed_rows"], percent(evidence_metrics["repeated_rows"], evidence_metrics["parsed_rows"]), "signature clusters; percent is rows involved"),
        ("Demonstrated same-URL/different-name reuse clusters", evidence_metrics["proven_reuse_clusters"], evidence_metrics["repeated_signatures"], percent(evidence_metrics["proven_reuse_clusters"], evidence_metrics["repeated_signatures"]), "repeated-signature clusters"),
        ("Ready rows unflagged by broad duplicate/sign screen", evidence_metrics["broad_unflagged_ready_rows"], len(ready), percent(evidence_metrics["broad_unflagged_ready_rows"], len(ready)), "not a validated final sample"),
        ("Raw ready depth gap", np.nan, len(coverage), raw_gap, "percentage points"),
        ("Parent fixed-effect ready depth gap", np.nan, len(coverage), fe, "percentage points"),
        ("Parent-FE LOO minimum", np.nan, len(coverage), min(loo), "percentage points"),
        ("Parent-FE LOO maximum", np.nan, len(coverage), max(loo), "percentage points"),
    ]
    return pd.DataFrame(rows, columns=["statistic", "numerator", "denominator", "value", "unit"]), metrics


def name_signal(data: AnalysisData) -> dict[str, float]:
    holder_nodes = set(
        data.logical_edges.loc[
            data.logical_edges["parent_node_type"].eq("observed_entity"),
            "parent_node_id",
        ]
    )
    work = data.occurrences[
        ["parent", "entity_country_std", "entity_name", "group_entity_id"]
    ].copy()
    cleaned = work["entity_name"].astype(str).str.upper().str.replace(
        r"[^A-Z0-9 ]", " ", regex=True
    )
    work["holding_name"] = cleaned.map(
        lambda value: bool(HOLDING_NAME_PATTERN.search(value))
    )
    work["holder"] = work["group_entity_id"].isin(holder_nodes).astype(float)
    work["cell"] = work["parent"].astype(str) + "\x1f" + work[
        "entity_country_std"
    ].astype(str)
    flagged = work["holding_name"]
    raw_gap = 100 * (
        work.loc[flagged, "holder"].mean() - work.loc[~flagged, "holder"].mean()
    )
    fe = 100 * within_coefficient(work, "holder", "holding_name", "cell")
    loo = []
    for parent in sorted(work["parent"].unique()):
        kept = work[work["parent"].ne(parent)]
        loo.append(
            100 * within_coefficient(kept, "holder", "holding_name", "cell")
        )
    return {
        "holding_name_entities": int(flagged.sum()),
        "holding_name_holder_pct": 100 * work.loc[flagged, "holder"].mean(),
        "other_name_holder_pct": 100 * work.loc[~flagged, "holder"].mean(),
        "raw_gap_pp": raw_gap,
        "parent_country_fe_gap_pp": fe,
        "loo_min_pp": min(loo),
        "loo_max_pp": max(loo),
    }


def structural_robustness(
    data: AnalysisData,
    parent_table: pd.DataFrame,
    concentration: pd.DataFrame,
    gateway_summary: pd.DataFrame,
    roles: pd.DataFrame,
    upstream: pd.DataFrame,
    depth_summary: pd.DataFrame,
    ownership_metrics: dict[str, float],
    financial_metrics: dict[str, float],
    name_metrics: dict[str, float],
) -> tuple[pd.DataFrame, dict[str, float]]:
    nonroot = data.edges[data.edges["reported_level"].gt(0)]
    cross_parent = nonroot.groupby("parent")["cross_border_edge"].mean()
    cross_loo = leave_one_parent_out(
        nonroot, lambda frame: 100 * frame["cross_border_edge"].mean()
    )
    raw_nonroot = data.occurrences[data.occurrences["level"].gt(0)]
    raw_cross = raw_nonroot["entity_country"].ne(
        raw_nonroot["immediate_parent_country"]
    )

    modal = (
        data.occurrences.groupby(["parent", "uin"]).size().rename("n").reset_index()
    )
    modal = modal.sort_values("n", ascending=False).drop_duplicates("parent")
    parent_sizes = data.occurrences["parent"].value_counts()
    modal["share"] = modal["n"] / modal["parent"].map(parent_sizes)
    modal_loo = []
    for parent in sorted(data.occurrences["parent"].unique()):
        numerator = modal.loc[modal["parent"].ne(parent), "n"].sum()
        denominator = data.occurrences["parent"].ne(parent).sum()
        modal_loo.append(percent(numerator, denominator))

    netherlands = gateway_summary.set_index("gateway_country").loc["NETHERLANDS"]
    role = roles.set_index("jurisdiction")
    dutch = role.loc["NETHERLANDS"]

    top_three = upstream["upstream_countries"].map(
        lambda values: bool(values & TOP_THREE_UPSTREAM)
    )
    top_three_parent = upstream.assign(exposed=top_three).groupby("parent")[
        "exposed"
    ].mean()
    top_three_loo = leave_one_parent_out(
        upstream.assign(exposed=top_three), lambda frame: 100 * frame["exposed"].mean()
    )
    no_funds = upstream[
        ~upstream["immediate_parent"].str.contains(
            "BREAKTHROUGH", case=False, na=False
        )
    ]
    no_funds_exposure = no_funds["upstream_countries"].map(
        lambda values: bool(values & TOP_THREE_UPSTREAM)
    )

    centre = upstream["upstream_countries"].map(
        lambda values: bool(values & DECLARED_CENTRES)
    )
    centre_parent = upstream.assign(exposed=centre).groupby("parent")["exposed"].mean()
    centre_loo = leave_one_parent_out(
        upstream.assign(exposed=centre), lambda frame: 100 * frame["exposed"].mean()
    )
    observed_intermediaries = data.logical_edges[
        data.logical_edges["parent_node_type"].eq("observed_entity")
    ].drop_duplicates("parent_node_id")
    centre_nodes = observed_intermediaries["matched_parent_country"].isin(
        DECLARED_CENTRES
    )

    deep_row = depth_summary[depth_summary["statistic"].eq("Reported level 5+")].iloc[0]
    deep_equal = depth_summary[
        depth_summary["statistic"].eq("Reported level 5+, equal-parent")
    ].iloc[0]
    deep_loo_min = depth_summary[
        depth_summary["statistic"].eq("Reported level 5+, LOO minimum")
    ].iloc[0]
    deep_loo_max = depth_summary[
        depth_summary["statistic"].eq("Reported level 5+, LOO maximum")
    ].iloc[0]
    graph_deep = depth_summary[
        depth_summary["statistic"].eq("Reconstructed distance 5+")
    ].iloc[0]

    metrics = {
        "cross_border_pooled_pct": 100 * nonroot["cross_border_edge"].mean(),
        "cross_border_equal_parent_pct": 100 * cross_parent.mean(),
        "cross_border_loo_min_pct": min(cross_loo),
        "cross_border_loo_max_pct": max(cross_loo),
        "cross_border_raw_label_pct": 100 * raw_cross.mean(),
        "modal_uin_pooled_pct": percent(modal["n"].sum(), len(data.occurrences)),
        "modal_uin_equal_parent_pct": 100 * modal["share"].mean(),
        "modal_uin_median_parent_pct": 100 * modal["share"].median(),
        "modal_uin_loo_min_pct": min(modal_loo),
        "modal_uin_loo_max_pct": max(modal_loo),
        "largest_observed_subtree_median_pct": concentration[
            "largest_observed_subtree_entity_pct"
        ].median(),
        "named_node_inclusive_subtree_median_pct": concentration[
            "named_node_inclusive_subtree_pct"
        ].median(),
        "strict_dag_dominator_median_pct": concentration[
            "strict_dag_dominator_entity_pct"
        ].median(),
        "netherlands_gateway_mean": netherlands["mean_descendants"],
        "netherlands_gateway_median": netherlands["median_descendants"],
        "netherlands_gateway_equal_parent_mean": netherlands[
            "parent_equal_mean_descendants"
        ],
        "netherlands_gateway_loo_min": netherlands["loo_min_mean_descendants"],
        "netherlands_gateway_loo_max": netherlands["loo_max_mean_descendants"],
        "netherlands_gateway_robust_subset_mean": netherlands[
            "mean_descendants_without_majority_child_branch"
        ],
        "netherlands_upstream_pooled_pct": dutch["pooled_target_path_pct"],
        "netherlands_upstream_equal_parent_pct": dutch[
            "equal_parent_target_path_pct"
        ],
        "netherlands_upstream_loo_min_pct": dutch["loo_min_target_path_pct"],
        "netherlands_upstream_loo_max_pct": dutch["loo_max_target_path_pct"],
        "top_three_upstream_count": int(top_three.sum()),
        "top_three_upstream_pooled_pct": 100 * top_three.mean(),
        "top_three_upstream_equal_parent_pct": 100 * top_three_parent.mean(),
        "top_three_upstream_loo_min_pct": min(top_three_loo),
        "top_three_upstream_loo_max_pct": max(top_three_loo),
        "top_three_excluding_funds_pct": 100 * no_funds_exposure.mean(),
        "declared_centre_upstream_pooled_pct": 100 * centre.mean(),
        "declared_centre_upstream_equal_parent_pct": 100 * centre_parent.mean(),
        "declared_centre_upstream_loo_min_pct": min(centre_loo),
        "declared_centre_upstream_loo_max_pct": max(centre_loo),
        "declared_centre_unique_observed_node_pct": 100 * centre_nodes.mean(),
    }

    rows = [
        ("Cross-border nonroot edges", "%", metrics["cross_border_pooled_pct"], metrics["cross_border_equal_parent_pct"], metrics["cross_border_loo_min_pct"], metrics["cross_border_loo_max_pct"], metrics["cross_border_raw_label_pct"], "Raw-label sensitivity"),
        ("Modal UIN channel", "% of targets", metrics["modal_uin_pooled_pct"], metrics["modal_uin_equal_parent_pct"], metrics["modal_uin_loo_min_pct"], metrics["modal_uin_loo_max_pct"], metrics["modal_uin_median_parent_pct"], "Median parent"),
        ("Largest observed subtree", "median parent %", metrics["largest_observed_subtree_median_pct"], np.nan, np.nan, np.nan, metrics["strict_dag_dominator_median_pct"], "Strict DAG dominator"),
        ("Largest subtree incl. named missing nodes", "median parent %", metrics["named_node_inclusive_subtree_median_pct"], np.nan, np.nan, np.nan, metrics["largest_observed_subtree_median_pct"], "Observed-node baseline"),
        ("Dutch gateway amplification", "mean descendants", metrics["netherlands_gateway_mean"], metrics["netherlands_gateway_equal_parent_mean"], metrics["netherlands_gateway_loo_min"], metrics["netherlands_gateway_loo_max"], metrics["netherlands_gateway_robust_subset_mean"], "No majority child branch"),
        ("Netherlands strictly upstream", "% of targets", metrics["netherlands_upstream_pooled_pct"], metrics["netherlands_upstream_equal_parent_pct"], metrics["netherlands_upstream_loo_min_pct"], metrics["netherlands_upstream_loo_max_pct"], np.nan, "Descendant/path estimand"),
        ("Netherlands + US + Mauritius upstream", "% of targets", metrics["top_three_upstream_pooled_pct"], metrics["top_three_upstream_equal_parent_pct"], metrics["top_three_upstream_loo_min_pct"], metrics["top_three_upstream_loo_max_pct"], metrics["top_three_excluding_funds_pct"], "Exclude venture-fund children"),
        ("Reported depth 5+", "% of targets", deep_row["value_pct"], deep_equal["value_pct"], deep_loo_min["value_pct"], deep_loo_max["value_pct"], graph_deep["value_pct"], "Reconstructed depth 5+, complete paths"),
        ("Full-ownership depth gap", "percentage points", ownership_metrics["pooled_gap_pp"], ownership_metrics["equal_parent_gap_pp"], np.nan, np.nan, ownership_metrics["exclude_reliance_gap_pp"], "Exclude Reliance"),
        ("Financial-ready deep gap", "percentage points", financial_metrics["raw_depth_gap_pp"], financial_metrics["parent_fe_depth_gap_pp"], financial_metrics["parent_fe_loo_min_pp"], financial_metrics["parent_fe_loo_max_pp"], np.nan, "Parent FE in equal-parent column"),
        ("Holding-name role gap", "percentage points", name_metrics["raw_gap_pp"], name_metrics["parent_country_fe_gap_pp"], name_metrics["loo_min_pp"], name_metrics["loo_max_pp"], np.nan, "Parent-country FE in equal-parent column"),
        ("Declared-centre upstream exposure", "% of targets", metrics["declared_centre_upstream_pooled_pct"], metrics["declared_centre_upstream_equal_parent_pct"], metrics["declared_centre_upstream_loo_min_pct"], metrics["declared_centre_upstream_loo_max_pct"], metrics["declared_centre_unique_observed_node_pct"], "Unique-node sensitivity"),
    ]
    table = pd.DataFrame(
        rows,
        columns=[
            "estimand",
            "unit",
            "pooled_or_primary",
            "equal_parent_or_fe",
            "loo_min",
            "loo_max",
            "alternative",
            "alternative_definition",
        ],
    )
    return table, metrics


def evidence_classification() -> pd.DataFrame:
    rows = [
        ("Core", "Denominator correction", "Raw rows are source observations, not firms."),
        ("Core", "Multidimensional parent architecture", "Size, geography, depth, branching, and channels are distinct axes."),
        ("Core", "Dominant channels and large observed subtrees", "Report UIN, observed-subtree, named-node, and DAG estimands separately."),
        ("Core", "Gateway-jurisdiction topology", "Dutch and Mauritian roles survive unique-node, gateway, parent-weighted, and LOO checks."),
        ("Core", "Depth measurement and parent concentration", "Reported depth is not observed graph distance; pooled deep patterns are parent-driven."),
        ("Supporting", "Cross-border nonroot edges", "Stable under parent balance and leave-one-parent-out checks."),
        ("Supporting", "Stake-zero and ownership-composition audit", "Recorded zeros are unsafe; the pooled ownership-depth gradient is composition."),
        ("Supporting", "Financial selection and extraction audit", "Coverage and parsing quality preclude population financial conclusions."),
        ("Supporting", "Holding-type name proxy", "Large within parent-country association, pending external role validation."),
        ("Descriptive", "Three-country descendant cover", "Large path-weighted exposure but materially lower with equal-parent weighting."),
        ("Fragile", "Fixed 19-jurisdiction centre exposure", "Maintained list and descendant weighting determine the magnitude."),
        ("Fragile", "Cumulative no-dilution claim", "Positive-stake complete chains are selected and zeros are unresolved."),
        ("Unresolved", "UIN substring semantics and vintage", "Requires an authoritative RBI specification."),
        ("Rejected", "General deep-manufacturing pattern", "Two parents account for nearly all deep manufacturing targets."),
        ("Rejected", "Financial health by depth or jurisdiction", "Selection, units, duplicate extraction, and small valid samples preclude inference."),
        ("Unresolved", "Tax, legal, regulatory, or misconduct mechanism", "Topology alone does not identify purpose, legality, or causation."),
    ]
    return pd.DataFrame(rows, columns=["classification", "result", "reason"])


def build_final_results(data: AnalysisData) -> FinalResults:
    evidence_detail, evidence_metrics = repeated_evidence_audit(data)
    construction = sample_construction(data, evidence_metrics)
    parent_table, concentration = subtree_and_parent_architecture(data)
    gateways, gateway_summary = gateway_amplification(data)
    upstream = upstream_frame(data)
    roles = jurisdiction_roles(data, upstream, gateway_summary)
    cover = greedy_cover(upstream)
    depth_distribution, depth_summary = depth_audit(data)
    ownership_table, ownership_metrics = ownership_audit(data)
    financial_table, financial_metrics = financial_audit(data, evidence_metrics)
    name_metrics = name_signal(data)
    robustness, structural_metrics = structural_robustness(
        data,
        parent_table,
        concentration,
        gateway_summary,
        roles,
        upstream,
        depth_summary,
        ownership_metrics,
        financial_metrics,
        name_metrics,
    )

    missing_parents = (
        data.edges[data.edges["parent_node_type"].eq("unobserved_entity")]
        .groupby(
            ["parent_node_id", "matched_parent_name", "matched_parent_country"],
            dropna=False,
        )
        .agg(
            incident_child_edges=("child_target_id", "size"),
            parent_groups=("parent", "nunique"),
        )
        .reset_index()
        .sort_values("incident_child_edges", ascending=False)
    )

    coverage = entity_coverage(data)
    nonroot_edges = data.edges[data.edges["reported_level"].gt(0)]
    ready_rows = data.preferred[data.preferred["ready_for_valuation"].eq(1)]
    sign_plausible_rows = ready_rows[
        ready_rows["total_assets"].gt(0)
        & ready_rows["total_liabilities"].ge(0)
    ]
    pl_valid_rows = sign_plausible_rows[
        sign_plausible_rows["pl_identity_ok"].eq(1)
        & sign_plausible_rows["profit_after_tax"].notna()
    ]
    modal_uin_count = int(
        data.occurrences.groupby(["parent", "uin"]).size().groupby("parent").max().sum()
    )
    observed_intermediary_count = int(
        data.logical_edges.loc[
            data.logical_edges["parent_node_type"].eq("observed_entity"),
            "parent_node_id",
        ].nunique()
    )
    deep_audit = depth_summary.set_index("statistic")
    tata_communications = parent_table.set_index("parent_short").loc[
        "Tata Communications"
    ]
    motherson = parent_table.set_index("parent_short").loc["Motherson"]

    key_metrics: dict[str, Any] = {
        "source_rows": len(data.raw),
        "preferred_target_year_rows": len(data.preferred),
        "target_occurrences": len(data.occurrences),
        "parent_scoped_normalized_entities": len(data.group_entities),
        "global_normalized_entities": len(data.global_entities),
        "uins": data.occurrences["uin"].nunique(),
        "observed_level0_targets": int(data.occurrences["level"].eq(0).sum()),
        "ultimate_parent_buckets": data.occurrences["parent"].nunique(),
        "jurisdiction_labels": data.occurrences["entity_country_std"].nunique(),
        "nonroot_edges": int(data.edges["reported_level"].gt(0).sum()),
        "expected_prior_level_links": int(
            nonroot_edges["link_status"].isin(
                ["exact_expected_level", "normalized_expected_level"]
            ).sum()
        ),
        "observed_other_level_links": int(
            nonroot_edges["parent_node_type"].eq("observed_entity").sum()
            - nonroot_edges["link_status"].isin(
                ["exact_expected_level", "normalized_expected_level"]
            ).sum()
        ),
        "cross_border_edges": int(nonroot_edges["cross_border_edge"].sum()),
        "complete_paths": int(data.paths["path_status"].eq("complete_to_ultimate_parent").sum()),
        "complete_path_pct": percent(
            data.paths["path_status"].eq("complete_to_ultimate_parent").sum(),
            len(data.paths),
        ),
        "missing_parent_edges": int(data.edges["parent_node_type"].eq("unobserved_entity").sum()),
        "normalized_missing_parent_nodes": int(data.edges.loc[data.edges["parent_node_type"].eq("unobserved_entity"), "parent_node_id"].nunique()),
        "targets_with_source": int(coverage["any_source_found"].sum()),
        "targets_balance_parsed": int(coverage["any_balance_parsed"].sum()),
        "ready_target_year_rows": len(ready_rows),
        "sign_plausible_ready_rows": len(sign_plausible_rows),
        "pl_valid_rows": len(pl_valid_rows),
        "valuation_ready_targets": int(coverage["any_ready"].sum()),
        "missing_units_ready_rows": int(
            data.preferred.loc[
                data.preferred["ready_for_valuation"].eq(1), "units"
            ].isna().sum()
        ),
        "reported_level2plus_count": int(data.occurrences["level"].ge(2).sum()),
        "reported_level2plus_pct": percent(
            data.occurrences["level"].ge(2).sum(), len(data.occurrences)
        ),
        "reported_level5plus_count": int(data.occurrences["level"].ge(5).sum()),
        "reported_level5plus_pct": percent(
            data.occurrences["level"].ge(5).sum(), len(data.occurrences)
        ),
        "reported_level5plus_equal_parent_pct": float(
            depth_summary.loc[
                depth_summary["statistic"].eq("Reported level 5+, equal-parent"),
                "value_pct",
            ].iloc[0]
        ),
        "reconstructed_level5plus_pct": float(
            depth_summary.loc[
                depth_summary["statistic"].eq("Reconstructed distance 5+"),
                "value_pct",
            ].iloc[0]
        ),
        "depth_mismatch_count": int(
            data.paths["reported_level_matches_reconstruction"].eq(0).sum()
        ),
        "depth_mismatch_pct": percent(
            data.paths["reported_level_matches_reconstruction"].eq(0).sum(),
            data.paths["path_status"].eq("complete_to_ultimate_parent").sum(),
        ),
        "motherson_mismatch_share_pct": percent(
            data.paths[
                data.paths["reported_level_matches_reconstruction"].eq(0)
            ]["parent"].eq("SAMVARDHANA MOTHERSON INTERNATI").sum(),
            data.paths["reported_level_matches_reconstruction"].eq(0).sum(),
        ),
        "zero_nonroot_stakes": int(
            data.occurrences.loc[data.occurrences["level"].gt(0), "stake"].eq(0).sum()
        ),
        "zero_nonroot_stake_pct": percent(
            data.occurrences.loc[data.occurrences["level"].gt(0), "stake"].eq(0).sum(),
            data.occurrences["level"].gt(0).sum(),
        ),
        "modal_uin_target_count": modal_uin_count,
        "concentration_parent_count": len(concentration),
        "observed_intermediary_nodes": observed_intermediary_count,
        "deep_manufacturing_count": int(
            deep_audit.loc[
                "Manufacturing targets at reported level 5+", "numerator"
            ]
        ),
        "manufacturing_target_count": int(
            deep_audit.loc[
                "Manufacturing targets at reported level 5+", "denominator"
            ]
        ),
        "deep_manufacturing_top_two_count": int(
            deep_audit.loc[
                "Motherson + Hindalco share of deep manufacturing", "numerator"
            ]
        ),
        "deep_manufacturing_top_two_pct": float(
            deep_audit.loc[
                "Motherson + Hindalco share of deep manufacturing", "value_pct"
            ]
        ),
        "tata_communications_raw_rows": int(tata_communications["raw_source_rows"]),
        "tata_communications_entities": int(tata_communications["normalized_entities"]),
        "motherson_raw_rows": int(motherson["raw_source_rows"]),
        "motherson_entities": int(motherson["normalized_entities"]),
        **{key: float(value) for key, value in structural_metrics.items()},
        **{f"ownership_{key}": float(value) for key, value in ownership_metrics.items()},
        **{f"financial_{key}": float(value) for key, value in financial_metrics.items()},
        **{f"name_{key}": float(value) for key, value in name_metrics.items()},
        **evidence_metrics,
    }

    tables = {
        "01_sample_construction": construction,
        "02_parent_architecture": parent_table,
        "03_channel_concentration": concentration,
        "04_gateway_amplification": gateway_summary,
        "05_jurisdiction_roles": roles,
        "06_greedy_jurisdiction_cover": cover,
        "07_depth_distribution": depth_distribution,
        "08_depth_audit": depth_summary,
        "09_ownership_data_audit": ownership_table,
        "10_financial_data_audit": financial_table,
        "11_robustness_matrix": robustness,
        "12_missing_parent_nodes": missing_parents,
        "13_duplicate_evidence_clusters": evidence_detail,
        "14_evidence_classification": evidence_classification(),
    }
    plot_data = {
        "parent_architecture": parent_table,
        "channel_concentration": concentration,
        "gateway_points": gateways,
        "gateway_summary": gateway_summary,
        "jurisdiction_roles": roles,
        "depth_distribution": depth_distribution,
        "financial_coverage": entity_coverage(data),
        "robustness": robustness,
    }
    return FinalResults(tables=tables, metrics=key_metrics, plot_data=plot_data)
