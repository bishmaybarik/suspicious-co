#!/usr/bin/env python3
"""Reproduce statistics needed for the final cross-agent adjudication.

The script reads only the immutable research input and Codex's independently
constructed hierarchy tables.  It does not read or execute any Claude file.
It writes denominator, graph, name-signal, ownership-chain, and extraction-
reuse sensitivities under ``outputs/codex/final``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    Path.home()
    / ".agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta"
)
DEFAULT_CODEX_OUTPUT = ROOT / "outputs/codex"
DEFAULT_OUTPUT = DEFAULT_CODEX_OUTPUT / "final"
REVIEWED_CLAUDE_COMMIT = "79b342b1ae3a473fef40a5c8dc91fa937597185e"
HOLDING_NAME_PATTERN = re.compile(
    r"\b(?:HOLDING|HOLDINGS|HOLDCO|INVESTMENT|INVESTMENTS)\b"
)
TOP_THREE_UPSTREAM = {
    "NETHERLANDS",
    "UNITED STATES OF AMERICA",
    "MAURITIUS",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.10g", lineterminator="\n")


def percent(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else np.nan


def within_coefficient(
    frame: pd.DataFrame, outcome: str, treatment: str, fixed_effect: str
) -> float:
    """Return the fixed-effect coefficient from a within transformation."""

    work = frame[[outcome, treatment, fixed_effect]].dropna().copy()
    x = work[treatment].astype(float)
    y = work[outcome].astype(float)
    x_within = x - x.groupby(work[fixed_effect]).transform("mean")
    y_within = y - y.groupby(work[fixed_effect]).transform("mean")
    denominator = float((x_within * x_within).sum())
    if denominator == 0:
        return np.nan
    return float((x_within * y_within).sum() / denominator)


def outcome_only_demeaned_gap(
    frame: pd.DataFrame, outcome: str, treatment: str, fixed_effect: str
) -> float:
    """Reproduce the nonstandard outcome-only demeaning used by Claude."""

    work = frame[[outcome, treatment, fixed_effect]].dropna().copy()
    residual = work[outcome] - work.groupby(fixed_effect)[outcome].transform("mean")
    treated = work[treatment].astype(bool)
    return float(residual[treated].mean() - residual[~treated].mean())


def load_tables(codex_output: Path) -> dict[str, pd.DataFrame]:
    data = codex_output / "data"
    return {
        "occ": pd.read_csv(data / "entity_occurrences.csv"),
        "entities": pd.read_csv(data / "unique_entities_parent_scoped.csv"),
        "edges": pd.read_csv(data / "parent_child_edges.csv"),
        "paths": pd.read_csv(data / "ownership_paths.csv"),
        "steps": pd.read_csv(data / "ownership_path_steps.csv"),
    }


def chokepoint_sensitivity(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compare target-forest subtrees with a normalized-entity DAG audit."""

    occ = tables["occ"]
    entities = tables["entities"]
    edges = tables["edges"]
    target_weight = entities.set_index("group_entity_id")["target_occurrences"]
    rows: list[dict[str, Any]] = []

    for parent, parent_entities in entities.groupby("parent", sort=True):
        parent_edges = edges[edges["parent"].eq(parent)]
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
        roots = parent_edges.loc[
            parent_edges["parent_node_type"].eq("ultimate_parent"),
            "parent_node_id",
        ].unique()
        if len(roots) != 1:
            raise AssertionError(f"expected one ultimate-parent root for {parent}")
        root = roots[0]
        reachable_before = nx.descendants(graph, root) & entity_nodes

        observed_candidates: list[tuple[int, int, str]] = []
        dominator_candidates: list[tuple[int, str]] = []
        for node in observed_nodes:
            descendants = nx.descendants(graph, node) & entity_nodes
            weighted_descendants = int(target_weight.reindex(descendants).sum())
            observed_candidates.append((weighted_descendants, len(descendants), node))

            graph_without = graph.copy()
            graph_without.remove_node(node)
            reachable_after = nx.descendants(graph_without, root) & entity_nodes
            detached = (reachable_before - reachable_after) - {node}
            dominator_candidates.append((len(detached), node))

        top_target, top_entity, top_node = max(observed_candidates)
        top_detached, top_dominator = max(dominator_candidates)
        top_info = parent_edges[parent_edges["parent_node_id"].eq(top_node)].iloc[0]
        dom_info = parent_edges[
            parent_edges["parent_node_id"].eq(top_dominator)
        ].iloc[0]

        missing_candidates: list[tuple[int, str]] = []
        missing_nodes = set(
            parent_edges.loc[
                parent_edges["parent_node_type"].eq("unobserved_entity"),
                "parent_node_id",
            ]
        )
        for node in missing_nodes:
            descendants = nx.descendants(graph, node) & entity_nodes
            missing_candidates.append((len(descendants), node))
        missing_top = max(missing_candidates) if missing_candidates else (0, "")
        if missing_top[1]:
            missing_info = parent_edges[
                parent_edges["parent_node_id"].eq(missing_top[1])
            ].iloc[0]
            missing_name = missing_info["matched_parent_name"]
            missing_country = missing_info["matched_parent_country"]
        else:
            missing_name = ""
            missing_country = ""

        n_targets = int(parent_entities["target_occurrences"].sum())
        n_entities = len(parent_entities)
        rows.append(
            {
                "parent": parent,
                "target_occurrences": n_targets,
                "normalized_entities": n_entities,
                "observed_level0_targets": int(
                    occ[occ["parent"].eq(parent)]["level"].eq(0).sum()
                ),
                "largest_observed_subtree_target_pct": percent(
                    top_target, n_targets - 1
                ),
                "largest_observed_subtree_entity_pct": percent(
                    top_entity, n_entities - 1
                ),
                "largest_observed_subtree_name": top_info["matched_parent_name"],
                "largest_observed_subtree_country": top_info[
                    "matched_parent_country"
                ],
                "normalized_dag_dominator_entity_pct": percent(
                    top_detached, n_entities - 1
                ),
                "normalized_dag_dominator_name": dom_info["matched_parent_name"],
                "root_reachable_entities": len(reachable_before),
                "root_reachable_entity_pct": percent(
                    len(reachable_before), n_entities
                ),
                "largest_unobserved_parent_subtree_entities": missing_top[0],
                "largest_unobserved_parent_name": missing_name,
                "largest_unobserved_parent_country": missing_country,
            }
        )

    result = pd.DataFrame(rows)
    return result[result["target_occurrences"].ge(15)].sort_values(
        "largest_observed_subtree_entity_pct", ascending=False
    )


def upstream_sets(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Attach each target's set of strictly upstream reported countries."""

    occ = tables["occ"]
    paths = tables["paths"]
    steps = tables["steps"]
    strict_steps = steps[steps["step_from_terminal"].gt(0)]
    country_sets = strict_steps.groupby("terminal_target_id")["country"].agg(
        lambda values: frozenset(values.dropna())
    )
    frame = occ[
        ["target_id", "parent", "group_entity_id", "immediate_parent"]
    ].copy()
    frame["upstream_countries"] = frame["target_id"].map(country_sets)
    frame["upstream_countries"] = frame["upstream_countries"].map(
        lambda value: value if isinstance(value, frozenset) else frozenset()
    )
    status = paths.set_index("target_id")["path_status"]
    frame["complete_path"] = frame["target_id"].map(status).eq(
        "complete_to_ultimate_parent"
    )
    return frame


def country_criticality(upstream: pd.DataFrame) -> pd.DataFrame:
    """Measure descendant exposure with parent balance and LOO bounds."""

    countries = sorted(
        set().union(*upstream["upstream_countries"].tolist()) - {"INDIA"}
    )
    parents = sorted(upstream["parent"].unique())
    rows: list[dict[str, Any]] = []
    for country in countries:
        exposed = upstream["upstream_countries"].map(lambda x: country in x)
        if int(exposed.sum()) < 5:
            continue
        parent_rates = upstream.assign(exposed=exposed).groupby("parent")[
            "exposed"
        ].mean()
        loo = [
            percent(
                exposed[upstream["parent"].ne(parent)].sum(),
                upstream["parent"].ne(parent).sum(),
            )
            for parent in parents
        ]
        rows.append(
            {
                "jurisdiction": country,
                "target_paths_below": int(exposed.sum()),
                "target_paths": len(upstream),
                "pooled_pct": percent(exposed.sum(), len(upstream)),
                "equal_parent_pct": 100.0 * parent_rates.mean(),
                "loo_min_pct": min(loo),
                "loo_max_pct": max(loo),
                "parents_affected": int(upstream.loc[exposed, "parent"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("target_paths_below", ascending=False)


def greedy_country_cover(
    frame: pd.DataFrame, sample: str, max_steps: int = 8
) -> pd.DataFrame:
    """Return the greedy cover sequence for sets of upstream countries."""

    countries = sorted(
        set().union(*frame["upstream_countries"].tolist()) - {"INDIA"}
    )
    remaining = set(frame.index)
    rows: list[dict[str, Any]] = []
    for step in range(1, max_steps + 1):
        candidates = [
            (
                sum(
                    country in frame.at[index, "upstream_countries"]
                    for index in remaining
                ),
                country,
            )
            for country in countries
        ]
        newly_covered, country = max(candidates)
        if newly_covered == 0:
            break
        remaining = {
            index
            for index in remaining
            if country not in frame.at[index, "upstream_countries"]
        }
        rows.append(
            {
                "sample": sample,
                "step": step,
                "jurisdiction": country,
                "newly_covered": newly_covered,
                "cumulative_pct": percent(
                    len(frame) - len(remaining), len(frame)
                ),
            }
        )
    return pd.DataFrame(rows)


def top_three_sensitivity(upstream: pd.DataFrame) -> pd.DataFrame:
    """Audit the three-country union under alternative path denominators."""

    samples: list[tuple[str, pd.DataFrame]] = [
        ("all target paths", upstream),
        ("complete target paths", upstream[upstream["complete_path"]]),
        (
            "exclude Breakthrough children",
            upstream[
                ~upstream["immediate_parent"].str.contains(
                    "BREAKTHROUGH", case=False, na=False
                )
            ],
        ),
    ]
    normalized = (
        upstream.groupby(["group_entity_id", "parent"], as_index=False)
        .agg(
            upstream_countries=(
                "upstream_countries",
                lambda values: frozenset().union(*values),
            )
        )
        .assign(complete_path=True, immediate_parent="")
    )
    samples.append(("parent-scoped normalized entities", normalized))

    rows: list[dict[str, Any]] = []
    for label, frame in samples:
        exposed = frame["upstream_countries"].map(
            lambda values: bool(values & TOP_THREE_UPSTREAM)
        )
        parent_rates = frame.assign(exposed=exposed).groupby("parent")[
            "exposed"
        ].mean()
        loo = [
            percent(
                exposed[frame["parent"].ne(parent)].sum(),
                frame["parent"].ne(parent).sum(),
            )
            for parent in sorted(frame["parent"].unique())
        ]
        rows.append(
            {
                "sample": label,
                "numerator": int(exposed.sum()),
                "denominator": len(frame),
                "pooled_pct": percent(exposed.sum(), len(frame)),
                "equal_parent_pct": 100.0 * parent_rates.mean(),
                "median_parent_pct": 100.0 * parent_rates.median(),
                "loo_min_pct": min(loo),
                "loo_max_pct": max(loo),
                "parents_with_zero_pct": int(parent_rates.eq(0).sum()),
                "parents_above_50_pct": int(parent_rates.gt(0.5).sum()),
            }
        )
    return pd.DataFrame(rows)


def clean_name(value: Any) -> str:
    return re.sub(r"[^A-Z0-9 ]", " ", str(value).upper())


def name_signal_for_frame(
    frame: pd.DataFrame,
    holder_nodes: set[str],
    sample: str,
    name_column: str,
    country_column: str,
) -> dict[str, Any]:
    work = frame.copy()
    work["holding_name"] = work[name_column].map(
        lambda value: bool(HOLDING_NAME_PATTERN.search(clean_name(value)))
    )
    work["is_holder"] = work["group_entity_id"].isin(holder_nodes).astype(int)
    work["parent_country_cell"] = (
        work["parent"].astype(str) + "\x1f" + work[country_column].astype(str)
    )
    flag = work["holding_name"]
    raw_gap = work.loc[flag, "is_holder"].mean() - work.loc[~flag, "is_holder"].mean()
    fe = within_coefficient(
        work, "is_holder", "holding_name", "parent_country_cell"
    )
    claude_adjustment = outcome_only_demeaned_gap(
        work, "is_holder", "holding_name", "parent_country_cell"
    )
    loo = []
    for parent in sorted(work["parent"].unique()):
        kept = work[work["parent"].ne(parent)]
        estimate = within_coefficient(
            kept, "is_holder", "holding_name", "parent_country_cell"
        )
        if not pd.isna(estimate):
            loo.append(estimate)
    cell_variation = work.groupby("parent_country_cell")["holding_name"].nunique()
    informative_cells = set(cell_variation[cell_variation.eq(2)].index)
    informative = work[work["parent_country_cell"].isin(informative_cells)]

    parent_gaps = []
    for _, parent_frame in work.groupby("parent"):
        if parent_frame["holding_name"].nunique() == 2:
            parent_gaps.append(
                parent_frame.loc[parent_frame["holding_name"], "is_holder"].mean()
                - parent_frame.loc[~parent_frame["holding_name"], "is_holder"].mean()
            )
    return {
        "sample": sample,
        "denominator": len(work),
        "holding_name_entities": int(flag.sum()),
        "parents_with_holding_name": int(work.loc[flag, "parent"].nunique()),
        "holder_rate_holding_name_pct": 100.0 * work.loc[flag, "is_holder"].mean(),
        "holder_rate_other_name_pct": 100.0 * work.loc[~flag, "is_holder"].mean(),
        "raw_gap_pp": 100.0 * raw_gap,
        "outcome_only_demeaned_gap_pp": 100.0 * claude_adjustment,
        "proper_parent_country_fe_pp": 100.0 * fe,
        "proper_fe_loo_min_pp": 100.0 * min(loo),
        "proper_fe_loo_max_pp": 100.0 * max(loo),
        "informative_parent_country_cells": len(informative_cells),
        "observations_in_informative_cells": len(informative),
        "parents_in_informative_cells": informative["parent"].nunique(),
        "equal_parent_raw_gap_pp": 100.0 * np.mean(parent_gaps),
        "median_parent_raw_gap_pp": 100.0 * np.median(parent_gaps),
    }


def name_signal_sensitivity(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    edges = tables["edges"]
    holder_nodes = set(
        edges.loc[
            edges["parent_node_type"].eq("observed_entity"), "parent_node_id"
        ]
    )
    rows = [
        name_signal_for_frame(
            tables["occ"],
            holder_nodes,
            "target occurrences",
            "entity_name",
            "entity_country_std",
        ),
        name_signal_for_frame(
            tables["entities"],
            holder_nodes,
            "parent-scoped normalized entities",
            "canonical_entity_name",
            "entity_country",
        ),
    ]
    return pd.DataFrame(rows)


def positive_chain_table(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Construct cumulative stakes only for paths reaching the Indian root."""

    occ = tables["occ"]
    paths = tables["paths"]
    stake = occ.set_index("target_id")["stake"].to_dict()
    rows: list[dict[str, Any]] = []
    orphan_stop_positive = 0

    for path in paths.itertuples(index=False):
        if path.reported_level <= 0:
            continue
        target_ids = (
            []
            if pd.isna(path.path_target_ids)
            else str(path.path_target_ids).split(" > ")
        )
        if path.path_status == "complete_to_ultimate_parent":
            chain_target_ids = target_ids[1:]
        else:
            chain_target_ids = target_ids
        stakes = [stake.get(target_id, np.nan) for target_id in chain_target_ids]
        all_positive = bool(stakes) and all(
            pd.notna(value) and value > 0 for value in stakes
        )
        root_complete_positive = (
            path.path_status == "complete_to_ultimate_parent" and all_positive
        )
        if all_positive:
            orphan_stop_positive += 1
        cumulative = (
            100.0 * float(np.prod(np.asarray(stakes) / 100.0))
            if root_complete_positive
            else np.nan
        )
        rows.append(
            {
                "target_id": path.target_id,
                "parent": path.parent,
                "reported_level": path.reported_level,
                "reconstructed_level": path.reconstructed_level,
                "root_complete": path.path_status == "complete_to_ultimate_parent",
                "root_complete_positive_chain": root_complete_positive,
                "cumulative_ownership": cumulative,
            }
        )

    chain = pd.DataFrame(rows)
    complete = chain[chain["root_complete_positive_chain"]].copy()
    complete["deep"] = complete["reported_level"].ge(3).astype(int)
    completion_by_level = (
        chain.groupby("reported_level")
        .agg(
            nonroot_targets=("target_id", "size"),
            root_complete_pct=("root_complete", lambda x: 100.0 * x.mean()),
            root_complete_positive_pct=(
                "root_complete_positive_chain",
                lambda x: 100.0 * x.mean(),
            ),
        )
        .reset_index()
    )
    cumulative_by_level = (
        complete.groupby("reported_level")["cumulative_ownership"]
        .agg(
            n="size",
            median="median",
            mean="mean",
            pct_at_100=lambda x: 100.0 * x.gt(99.99).mean(),
            pct_below_50=lambda x: 100.0 * x.lt(50).mean(),
        )
        .reset_index()
    )

    positive_edges = occ[occ["level"].gt(0) & occ["stake"].gt(0)].copy()
    positive_edges["deep"] = positive_edges["level"].ge(3).astype(int)
    positive_edges["parent_fe"] = positive_edges["parent"]
    single_edge_fe = within_coefficient(
        positive_edges, "stake", "deep", "parent_fe"
    )
    single_edge_outcome_only = outcome_only_demeaned_gap(
        positive_edges, "stake", "deep", "parent_fe"
    )
    paired = (
        positive_edges.groupby(["parent", "deep"])["stake"]
        .mean()
        .unstack()
        .dropna()
    )
    complete["parent_fe"] = complete["parent"]
    cumulative_fe = within_coefficient(
        complete, "cumulative_ownership", "deep", "parent_fe"
    )
    cumulative_outcome_only = outcome_only_demeaned_gap(
        complete, "cumulative_ownership", "deep", "parent_fe"
    )
    summary = pd.DataFrame(
        [
            {
                "statistic": "nonroot target occurrences",
                "value": len(chain),
            },
            {
                "statistic": "paths reaching ultimate parent",
                "value": int(chain["root_complete"].sum()),
            },
            {
                "statistic": "root-complete paths with all positive stakes",
                "value": len(complete),
            },
            {
                "statistic": "positive chains if orphan termination is accepted",
                "value": orphan_stop_positive,
            },
            {
                "statistic": "root-complete positive-chain share pct",
                "value": 100.0 * chain["root_complete_positive_chain"].mean(),
            },
            {
                "statistic": "median cumulative ownership pct",
                "value": complete["cumulative_ownership"].median(),
            },
            {
                "statistic": "chains at cumulative 100 pct",
                "value": 100.0 * complete["cumulative_ownership"].gt(99.99).mean(),
            },
            {
                "statistic": "single-edge raw deep-minus-shallow pp",
                "value": positive_edges.loc[
                    positive_edges["deep"].eq(1), "stake"
                ].mean()
                - positive_edges.loc[
                    positive_edges["deep"].eq(0), "stake"
                ].mean(),
            },
            {
                "statistic": "single-edge outcome-only demeaned gap pp",
                "value": single_edge_outcome_only,
            },
            {
                "statistic": "single-edge proper parent FE gap pp",
                "value": single_edge_fe,
            },
            {
                "statistic": "single-edge equal-parent paired gap pp",
                "value": (paired[1] - paired[0]).mean(),
            },
            {
                "statistic": "single-edge median-parent paired gap pp",
                "value": (paired[1] - paired[0]).median(),
            },
            {
                "statistic": "cumulative raw deep-minus-shallow pp",
                "value": complete.loc[
                    complete["deep"].eq(1), "cumulative_ownership"
                ].mean()
                - complete.loc[
                    complete["deep"].eq(0), "cumulative_ownership"
                ].mean(),
            },
            {
                "statistic": "cumulative outcome-only demeaned gap pp",
                "value": cumulative_outcome_only,
            },
            {
                "statistic": "cumulative proper parent FE gap pp",
                "value": cumulative_fe,
            },
        ]
    )
    return summary, completion_by_level, cumulative_by_level


def duplicate_evidence_audit(raw: pd.DataFrame) -> pd.DataFrame:
    """Test whether repeated numeric signatures reuse the same evidence."""

    preferred = raw[raw["preferred_for_target_year"].eq(1)].copy()
    parsed = preferred.dropna(
        subset=["total_assets", "total_liabilities", "equity"]
    ).copy()
    signature = [
        "fiscal_year",
        "currency",
        "units",
        "total_assets",
        "total_liabilities",
        "equity",
    ]
    parsed["signature_id"] = parsed.groupby(
        signature, dropna=False, sort=False
    ).ngroup()
    signature_sizes = parsed.groupby("signature_id").size()
    duplicate_ids = set(signature_sizes[signature_sizes.gt(1)].index)
    duplicates = parsed[parsed["signature_id"].isin(duplicate_ids)]

    detail_rows: list[dict[str, Any]] = []
    for signature_id, group in duplicates.groupby("signature_id"):
        same_url = group["source_url"].nunique(dropna=False) == 1
        different_names = group["entity_name"].nunique(dropna=False) > 1
        evidence_identical = all(
            group[column].nunique(dropna=False) == 1
            for column in [
                "total_assets_evidence",
                "total_liabilities_evidence",
                "equity_evidence",
            ]
        )
        detail_rows.append(
            {
                "signature_id": signature_id,
                "rows": len(group),
                "same_source_url": same_url,
                "different_entity_names": different_names,
                "same_url_different_names": same_url and different_names,
                "all_core_evidence_identical": evidence_identical,
                "ready_rows": int(group["ready_for_valuation"].eq(1).sum()),
            }
        )
    detail = pd.DataFrame(detail_rows)

    ready = parsed[parsed["ready_for_valuation"].eq(1)].copy()
    ready_sizes = ready.groupby("signature_id").size()
    ready_duplicate_ids = set(ready_sizes[ready_sizes.gt(1)].index)
    ready_duplicates = ready[ready["signature_id"].isin(ready_duplicate_ids)]
    artifact_ready_ids = []
    for signature_id in ready_duplicate_ids:
        ready_group = ready[ready["signature_id"].eq(signature_id)]
        full_group = parsed[parsed["signature_id"].eq(signature_id)]
        if (
            ready_group["entity_name"].nunique(dropna=False) > 1
            and full_group["source_url"].nunique(dropna=False) == 1
        ):
            artifact_ready_ids.append(signature_id)

    all_ready = preferred[preferred["ready_for_valuation"].eq(1)].copy()
    duplicate_ready_flag = all_ready.index.isin(duplicates.index)
    sign_flag = ~(
        all_ready["total_assets"].gt(0)
        & all_ready["total_liabilities"].ge(0)
    )
    artifact_ready_flag = all_ready.index.isin(
        ready[ready["signature_id"].isin(artifact_ready_ids)].index
    )
    same_url_different = detail[detail["same_url_different_names"]]

    rows = [
        ("preferred target-year rows", len(preferred)),
        ("parsed rows with three core balance variables", len(parsed)),
        ("repeated numeric signatures", len(duplicate_ids)),
        ("rows in repeated numeric signatures", len(duplicates)),
        ("same-URL repeated signatures", int(detail["same_source_url"].sum())),
        (
            "repeated signatures with different entity names",
            int(detail["different_entity_names"].sum()),
        ),
        (
            "same-URL different-name signatures",
            len(same_url_different),
        ),
        (
            "same-URL different-name signatures with identical core evidence",
            int(same_url_different["all_core_evidence_identical"].sum()),
        ),
        ("ready rows in any repeated signature", int(duplicate_ready_flag.sum())),
        ("sign-implausible ready rows", int(sign_flag.sum())),
        (
            "ready rows flagged by repeated signature or sign",
            int((duplicate_ready_flag | sign_flag).sum()),
        ),
        (
            "ready rows unflagged by repeated signature and sign",
            int((~duplicate_ready_flag & ~sign_flag).sum()),
        ),
        (
            "different-name repeated-ready signature clusters",
            len(artifact_ready_ids),
        ),
        (
            "ready rows in different-name repeated-ready clusters",
            len(ready_duplicates[ready_duplicates["signature_id"].isin(artifact_ready_ids)]),
        ),
        (
            "ready rows flagged by strict artifact subset or sign",
            int((artifact_ready_flag | sign_flag).sum()),
        ),
        (
            "ready rows unflagged by strict artifact subset and sign",
            int((~artifact_ready_flag & ~sign_flag).sum()),
        ),
    ]
    return pd.DataFrame(rows, columns=["statistic", "value"])


def classification_ledger() -> pd.DataFrame:
    """Return the final evidence classification used in the written review."""

    rows = [
        (
            "X-F001",
            "Denominator and panel-length distortion",
            "CORE RESULT",
            "Raw rows are not firms; parent and country estimates require entity and parent-balanced denominators.",
        ),
        (
            "X-F005 / C-F004",
            "Multidimensional parent architectures",
            "CORE RESULT",
            "Size, depth, branching, geography, and stake describe different group architectures.",
        ),
        (
            "X-F018 / C-F018",
            "Dominant mapping channels and observed subtrees",
            "CORE RESULT",
            "Concentration survives parent balance, entity normalization, and a normalized-DAG sensitivity.",
        ),
        (
            "X-F007 / C-F002 / C-F006",
            "Gateway-jurisdiction topology",
            "CORE RESULT",
            "Dutch and Mauritian intermediary roles survive unique-node, edge, path, parent-weighted, and LOO checks.",
        ),
        (
            "X-F004 / X-F006 / C-F017",
            "Depth measurement and parent concentration",
            "CORE RESULT",
            "Reported depth is not graph distance, and pooled deep/sector patterns are driven by a few groups.",
        ),
        (
            "X-F008",
            "Cross-border nonroot edges",
            "SUPPORTING RESULT",
            "A majority result is stable to parent weighting and leave-one-parent-out analysis.",
        ),
        (
            "X-F010 / X-F019 / C-F021",
            "Stake zeros and ownership-depth composition",
            "SUPPORTING RESULT",
            "Zeros are unsafe and the pooled ownership gradient is largely parent composition; cumulative no-dilution is not established.",
        ),
        (
            "X-F011 / X-F012 / X-F013 / X-F017 / C-F014",
            "Financial selection and extraction contamination",
            "SUPPORTING RESULT",
            "Coverage is selected and duplicate evidence prevents population financial claims.",
        ),
        (
            "C-F020",
            "Holding-type names predict observed graph role",
            "SUPPORTING RESULT",
            "The proper parent-country fixed-effect estimate is large but needs out-of-sample legal-role validation.",
        ),
        (
            "X-F002 / C-F001",
            "UIN and legal entity are different units",
            "SUPPORTING RESULT",
            "The mapping multiplicity is exact, but UIN scope and the skewed mean require careful language.",
        ),
        (
            "X-F003 / C-F012",
            "Parent exposure and global company counts differ",
            "SUPPORTING RESULT",
            "Shared and multi-path entity candidates require separate parent-exposure and global-company estimands.",
        ),
        (
            "C-F019",
            "Three-country descendant cover",
            "INTERESTING DESCRIPTIVE FACT",
            "The pooled cover is large but falls under equal-parent weighting and repeats ancestors by descendant.",
        ),
        (
            "X-F014",
            "US resident-entity prominence",
            "INTERESTING DESCRIPTIVE FACT",
            "The US is the largest resident jurisdiction but is not similarly overrepresented as an intermediary.",
        ),
        (
            "C-F010 / C-F011 / C-F012",
            "Round trips, vessel SPVs, and mirrored consortium paths",
            "INTERESTING DESCRIPTIVE FACT",
            "Small, interpretable motifs are useful examples but not general results.",
        ),
        (
            "C-F003",
            "Fixed 19-jurisdiction conduit share",
            "FRAGILE",
            "The descendant-weighted fact reproduces after a missing-country correction, but the list and weighting define the magnitude.",
        ),
        (
            "C-F021 (positive claim)",
            "Layering does not dilute ownership",
            "FRAGILE",
            "Only 962 complete paths have all-positive stakes; zeros and orphan paths make the selected-chain conclusion unsafe.",
        ),
        (
            "C-F022",
            "Netherlands-Mauritius regional routing split",
            "FRAGILE",
            "Several modal routes are parent- and subtree-weighted and weaken under equal-parent destination shares.",
        ),
        (
            "C-F008 / C-F009",
            "UIN decoding and gateway vintage",
            "UNRESOLVED",
            "String regularities reproduce, but substring semantics and policy timing need authoritative external evidence.",
        ),
        (
            "X-F006 sector generalization",
            "Manufacturing entities are generally deeper",
            "REJECTED",
            "Two parents supply 240 of 242 deep manufacturing targets.",
        ),
        (
            "Financial outcome patterns",
            "Depth or jurisdiction predicts financial health",
            "REJECTED",
            "Selection, missing units, duplicate extraction, and small valid samples preclude the claim.",
        ),
        (
            "Institutional interpretations",
            "Tax, legal, regulatory, or misconduct mechanism",
            "UNRESOLVED",
            "The dataset contains topology, not intent, legal treatment, or causal policy evidence.",
        ),
    ]
    return pd.DataFrame(
        rows, columns=["source_findings", "candidate", "classification", "reason"]
    )


def build_outputs(input_path: Path, codex_output: Path, output: Path) -> None:
    raw = pd.read_stata(input_path, convert_categoricals=False)
    tables = load_tables(codex_output)

    chokepoints = chokepoint_sensitivity(tables)
    upstream = upstream_sets(tables)
    criticality = country_criticality(upstream)
    cover_tables = [
        greedy_country_cover(upstream, "all target paths"),
        greedy_country_cover(
            upstream[upstream["complete_path"]], "complete target paths"
        ),
        greedy_country_cover(
            upstream[
                ~upstream["immediate_parent"].str.contains(
                    "BREAKTHROUGH", case=False, na=False
                )
            ],
            "exclude Breakthrough children",
        ),
    ]
    top_three = top_three_sensitivity(upstream)
    name_signal = name_signal_sensitivity(tables)
    chain_summary, completion_by_level, cumulative_by_level = positive_chain_table(
        tables
    )
    duplicate_audit = duplicate_evidence_audit(raw)
    ledger = classification_ledger()

    write_csv(chokepoints, output / "chokepoint_sensitivity.csv")
    write_csv(criticality, output / "jurisdiction_criticality.csv")
    write_csv(pd.concat(cover_tables), output / "greedy_jurisdiction_cover.csv")
    write_csv(top_three, output / "top_three_cover_sensitivity.csv")
    write_csv(name_signal, output / "name_signal_sensitivity.csv")
    write_csv(chain_summary, output / "ownership_chain_summary.csv")
    write_csv(completion_by_level, output / "ownership_chain_completion_by_level.csv")
    write_csv(cumulative_by_level, output / "cumulative_ownership_by_level.csv")
    write_csv(duplicate_audit, output / "duplicate_evidence_audit.csv")
    write_csv(ledger, output / "classification_ledger.csv")

    large = chokepoints
    all_top_three = top_three[top_three["sample"].eq("all target paths")].iloc[0]
    name_targets = name_signal[name_signal["sample"].eq("target occurrences")].iloc[0]
    chain_values = chain_summary.set_index("statistic")["value"]
    duplicate_values = duplicate_audit.set_index("statistic")["value"]
    metrics = {
        "reviewed_claude_commit": REVIEWED_CLAUDE_COMMIT,
        "input_sha256": sha256_file(input_path),
        "target_occurrences": len(tables["occ"]),
        "parent_scoped_normalized_entities": len(tables["entities"]),
        "large_parent_groups": len(large),
        "largest_observed_subtree_median_entity_pct": float(
            large["largest_observed_subtree_entity_pct"].median()
        ),
        "normalized_dag_dominator_median_entity_pct": float(
            large["normalized_dag_dominator_entity_pct"].median()
        ),
        "top_three_upstream_target_paths": int(all_top_three["numerator"]),
        "top_three_upstream_pooled_pct": float(all_top_three["pooled_pct"]),
        "top_three_upstream_equal_parent_pct": float(
            all_top_three["equal_parent_pct"]
        ),
        "holding_name_raw_gap_pp": float(name_targets["raw_gap_pp"]),
        "holding_name_parent_country_fe_pp": float(
            name_targets["proper_parent_country_fe_pp"]
        ),
        "complete_positive_ownership_chains": int(
            chain_values["root-complete paths with all positive stakes"]
        ),
        "orphan_accepting_positive_ownership_chains": int(
            chain_values["positive chains if orphan termination is accepted"]
        ),
        "duplicate_signature_clusters": int(
            duplicate_values["repeated numeric signatures"]
        ),
        "same_url_different_name_artifact_clusters": int(
            duplicate_values[
                "same-URL different-name signatures with identical core evidence"
            ]
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "adjudication_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--codex-output", type=Path, default=DEFAULT_CODEX_OUTPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_outputs(args.input, args.codex_output, args.output)
    print(f"Wrote final adjudication diagnostics to {args.output}")


if __name__ == "__main__":
    main()
