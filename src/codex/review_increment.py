#!/usr/bin/env python3
"""Independently review cross-agent claims and extend the empirical search.

This script never reads another agent's generated files. It reads the immutable
Stata input and the hierarchy representation produced during Codex blind
discovery, then writes review diagnostics and two new analyses under
``outputs/codex/review``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-review-matplotlib-cache")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import fisher_exact


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    Path.home()
    / ".agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta"
)
DEFAULT_CODEX_OUTPUT = ROOT / "outputs/codex"
DEFAULT_OUTPUT = DEFAULT_CODEX_OUTPUT / "review"
REVIEWED_COMMIT = "5ab6cb5944ad6fe8193f03b71f7a918ac4d24076"

# This reproduces the other agent's declared 19-place list after applying the
# spelling-only country normalization used in the Codex blind-discovery graph.
# It is an estimand, not a legal or normative classification.
DECLARED_CENTRES = {
    "NETHERLANDS",
    "MAURITIUS",
    "SINGAPORE",
    "CYPRUS",
    "LUXEMBOURG",
    "JERSEY",
    "GUERNSEY",
    "ISLE OF MAN",
    "CAYMAN ISLANDS",
    "BRITISH VIRGIN ISLANDS",
    "BERMUDA",
    "BARBADOS",
    "PANAMA",
    "MARSHALL ISLANDS",
    "IFSC GIFT CITY",
    "SWITZERLAND",
    "IRELAND",
    "HONG KONG",
    "UNITED ARAB EMIRATES",
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


def safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return float(np.mean(values)) if values else np.nan


def within_parent_coefficient(
    frame: pd.DataFrame, outcome: str, treatment: str, parent: str = "parent"
) -> float:
    """Return the one-way fixed-effects coefficient using within transformation."""

    work = frame[[parent, outcome, treatment]].dropna().copy()
    x = work[treatment] - work.groupby(parent)[treatment].transform("mean")
    y = work[outcome] - work.groupby(parent)[outcome].transform("mean")
    denominator = float((x * x).sum())
    return float((x * y).sum() / denominator) if denominator else np.nan


def paired_parent_difference(
    frame: pd.DataFrame, outcome: str, treatment: str, parent: str = "parent"
) -> pd.Series:
    cells = frame.groupby([parent, treatment])[outcome].mean().unstack()
    if 0 not in cells or 1 not in cells:
        return pd.Series(dtype=float)
    cells = cells[[0, 1]].dropna()
    return cells[1] - cells[0]


def leave_one_parent_out(
    frame: pd.DataFrame, estimator: Any, parent: str = "parent"
) -> list[tuple[str, float]]:
    results: list[tuple[str, float]] = []
    for omitted in sorted(frame[parent].dropna().unique()):
        estimate = estimator(frame[frame[parent].ne(omitted)])
        if not pd.isna(estimate):
            results.append((str(omitted), float(estimate)))
    return results


def load_inputs(
    input_path: Path, codex_output: Path
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    raw = pd.read_stata(input_path, convert_categoricals=False)
    data = codex_output / "data"
    tables = {
        "occ": pd.read_csv(data / "entity_occurrences.csv"),
        "edges": pd.read_csv(data / "parent_child_edges.csv"),
        "edge_occ": pd.read_csv(data / "parent_child_edge_occurrences.csv"),
        "paths": pd.read_csv(data / "ownership_paths.csv"),
        "steps": pd.read_csv(data / "ownership_path_steps.csv"),
        "preferred": pd.read_csv(data / "preferred_financial_panel.csv"),
        "group_entities": pd.read_csv(data / "unique_entities_parent_scoped.csv"),
        "global_entities": pd.read_csv(data / "unique_entities_global.csv"),
    }
    return raw, tables


def structural_base(raw: pd.DataFrame) -> pd.DataFrame:
    structural = [
        "parent",
        "level",
        "entity_name",
        "entity_country",
        "immediate_parent",
        "immediate_parent_country",
        "stake",
        "sector_code",
        "sector_label",
        "uin",
    ]
    conflicts = raw.groupby("target_id")[structural].nunique(dropna=False).gt(1)
    if int(conflicts.sum().sum()) != 0:
        raise AssertionError("structural fields vary within target_id")
    return raw.sort_values("target_id", kind="mergesort").drop_duplicates("target_id")


def uin_multiplier_tables(
    base: pd.DataFrame, tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, dict[str, float]]:
    by_uin = base.groupby(["parent", "uin"]).size().rename("entities").reset_index()
    by_parent = base.groupby("parent").agg(
        entities=("target_id", "size"), uins=("uin", "nunique")
    )
    by_parent["entities_per_uin"] = by_parent["entities"] / by_parent["uins"]
    pooled_loo = leave_one_parent_out(
        base,
        lambda z: len(z) / z["uin"].nunique(),
    )
    roots = base[base["level"].eq(0)]
    rows = [
        {
            "estimand": "target occurrences per UIN",
            "numerator": len(base),
            "denominator": base["uin"].nunique(),
            "estimate": len(base) / base["uin"].nunique(),
            "unit": "target occurrence / UIN",
        },
        {
            "estimand": "parent-scoped normalized entities per UIN",
            "numerator": len(tables["group_entities"]),
            "denominator": base["uin"].nunique(),
            "estimate": len(tables["group_entities"]) / base["uin"].nunique(),
            "unit": "normalized entity / UIN",
        },
        {
            "estimand": "global normalized candidates per UIN",
            "numerator": len(tables["global_entities"]),
            "denominator": base["uin"].nunique(),
            "estimate": len(tables["global_entities"]) / base["uin"].nunique(),
            "unit": "global candidate / UIN",
        },
        {
            "estimand": "median target occurrences within UIN",
            "numerator": np.nan,
            "denominator": len(by_uin),
            "estimate": by_uin["entities"].median(),
            "unit": "UIN",
        },
        {
            "estimand": "equal-parent mean entities per UIN",
            "numerator": np.nan,
            "denominator": len(by_parent),
            "estimate": by_parent["entities_per_uin"].mean(),
            "unit": "ultimate parent",
        },
        {
            "estimand": "share of entities in ten largest UINs (%)",
            "numerator": by_uin.nlargest(10, "entities")["entities"].sum(),
            "denominator": len(base),
            "estimate": percent(
                by_uin.nlargest(10, "entities")["entities"].sum(), len(base)
            ),
            "unit": "target occurrence",
        },
        {
            "estimand": "share at reported level 2+ (%)",
            "numerator": int(base["level"].ge(2).sum()),
            "denominator": len(base),
            "estimate": percent(base["level"].ge(2).sum(), len(base)),
            "unit": "target occurrence",
        },
        {
            "estimand": "UINs with an observed level-0 target (%)",
            "numerator": roots["uin"].nunique(),
            "denominator": base["uin"].nunique(),
            "estimate": percent(roots["uin"].nunique(), base["uin"].nunique()),
            "unit": "UIN",
        },
    ]
    result = pd.DataFrame(rows)
    metrics = {
        "targets": float(len(base)),
        "uins": float(base["uin"].nunique()),
        "roots": float(len(roots)),
        "median_entities_per_uin": float(by_uin["entities"].median()),
        "pooled_entities_per_uin": float(len(base) / base["uin"].nunique()),
        "parent_equal_entities_per_uin": float(by_parent["entities_per_uin"].mean()),
        "loo_min": min(value for _, value in pooled_loo),
        "loo_max": max(value for _, value in pooled_loo),
    }
    return result, metrics


def gateway_amplification_tables(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    occ = tables["occ"]
    edges = tables["edges"]
    roots = occ[occ["level"].eq(0)].drop_duplicates("group_entity_id")
    roots = roots[
        ["parent", "group_entity_id", "entity_country_std", "uin", "entity_name"]
    ]
    records: list[dict[str, Any]] = []
    for parent, parent_edges in edges.groupby("parent"):
        graph = nx.DiGraph()
        graph.add_edges_from(
            parent_edges[["parent_node_id", "child_group_entity_id"]].itertuples(
                index=False, name=None
            )
        )
        for root in roots[roots["parent"].eq(parent)].itertuples(index=False):
            descendants = {
                node
                for node in nx.descendants(graph, root.group_entity_id)
                if str(node).startswith("pe_")
            }
            branch_sizes: list[int] = []
            for child in graph.successors(root.group_entity_id):
                branch = {child} | {
                    node
                    for node in nx.descendants(graph, child)
                    if str(node).startswith("pe_")
                }
                branch_sizes.append(len(branch & descendants))
            largest_branch = max(branch_sizes, default=0)
            records.append(
                {
                    "parent": parent,
                    "gateway_group_entity_id": root.group_entity_id,
                    "gateway_name": root.entity_name,
                    "gateway_country": root.entity_country_std,
                    "uin": root.uin,
                    "descendants": len(descendants),
                    "direct_child_branches": graph.out_degree(root.group_entity_id),
                    "largest_direct_child_branch": largest_branch,
                    "largest_branch_share": (
                        largest_branch / len(descendants) if descendants else np.nan
                    ),
                }
            )
    gateway = pd.DataFrame(records).sort_values(
        ["gateway_country", "descendants", "parent"],
        ascending=[True, False, True],
    )

    summary_rows: list[dict[str, Any]] = []
    for country, group in gateway.groupby("gateway_country"):
        if len(group) < 3:
            continue
        parent_means = group.groupby("parent")["descendants"].mean()
        loo = leave_one_parent_out(group, lambda z: z["descendants"].mean())
        balanced = group[group["largest_branch_share"].le(0.5)]
        summary_rows.append(
            {
                "gateway_country": country,
                "gateways": len(group),
                "parents": group["parent"].nunique(),
                "total_descendants": group["descendants"].sum(),
                "mean_descendants": group["descendants"].mean(),
                "median_descendants": group["descendants"].median(),
                "parent_equal_mean_descendants": parent_means.mean(),
                "largest_gateway_share_of_country_descendants": (
                    group["descendants"].max() / group["descendants"].sum()
                    if group["descendants"].sum()
                    else np.nan
                ),
                "largest_child_branches_share_of_descendants": (
                    group["largest_direct_child_branch"].sum()
                    / group["descendants"].sum()
                    if group["descendants"].sum()
                    else np.nan
                ),
                "gateways_without_majority_child_branch": len(balanced),
                "mean_descendants_without_majority_child_branch": balanced[
                    "descendants"
                ].mean(),
                "median_descendants_without_majority_child_branch": balanced[
                    "descendants"
                ].median(),
                "loo_min_mean_descendants": min(value for _, value in loo),
                "loo_max_mean_descendants": max(value for _, value in loo),
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        "mean_descendants", ascending=False
    )
    focus = summary.set_index("gateway_country")
    metrics = {
        "netherlands_mean": float(focus.loc["NETHERLANDS", "mean_descendants"]),
        "netherlands_median": float(
            focus.loc["NETHERLANDS", "median_descendants"]
        ),
        "netherlands_parent_equal": float(
            focus.loc["NETHERLANDS", "parent_equal_mean_descendants"]
        ),
        "netherlands_loo_min": float(
            focus.loc["NETHERLANDS", "loo_min_mean_descendants"]
        ),
        "netherlands_robust_subset_mean": float(
            focus.loc[
                "NETHERLANDS", "mean_descendants_without_majority_child_branch"
            ]
        ),
        "us_mean": float(
            focus.loc["UNITED STATES OF AMERICA", "mean_descendants"]
        ),
    }
    return gateway, summary, metrics


def path_has_declared_centre(path: Any) -> bool:
    countries = str(path).split(" > ")
    return bool(set(countries[:-1]) & DECLARED_CENTRES)


def conduit_exposure_tables(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    paths = tables["paths"].copy()
    paths["reached_through_declared_centre"] = paths["path_countries"].map(
        path_has_declared_centre
    )
    exposed = "reached_through_declared_centre"
    complete = paths[paths["path_status"].eq("complete_to_ultimate_parent")]
    nonroot = paths[paths["reported_level"].ge(1)]
    deep = paths[paths["reported_level"].ge(2)]
    group_unique = paths.sort_values(["parent", "target_id"]).drop_duplicates(
        "group_entity_id"
    )
    global_unique = paths.sort_values(["parent", "target_id"]).drop_duplicates(
        "global_entity_id"
    )
    pooled_loo = leave_one_parent_out(paths, lambda z: z[exposed].mean())

    observed_edges = tables["edges"][
        tables["edges"]["parent_node_type"].eq("observed_entity")
    ].copy()
    observed_edges["centre_parent"] = observed_edges["matched_parent_country"].isin(
        DECLARED_CENTRES
    )
    unique_parent_nodes = observed_edges.drop_duplicates(["parent", "parent_node_id"])
    roots = tables["occ"][tables["occ"]["level"].eq(0)]

    rows: list[dict[str, Any]] = []

    def append_share(name: str, frame: pd.DataFrame, note: str) -> None:
        rows.append(
            {
                "estimand": name,
                "numerator": int(frame[exposed].sum()),
                "denominator": len(frame),
                "percent": percent(frame[exposed].sum(), len(frame)),
                "note": note,
            }
        )

    append_share("all target paths", paths, "one observation per target_id")
    append_share(
        "complete observed paths",
        complete,
        "excludes paths ending at an unobserved named parent",
    )
    append_share("reported nonroot targets", nonroot, "excludes level-0 targets")
    append_share("reported level 2+ targets", deep, "more mechanically exposed")
    append_share(
        "parent-scoped normalized entities", group_unique, "one group_entity_id"
    )
    append_share(
        "global normalized candidates", global_unique, "one global_entity_id"
    )
    rows.extend(
        [
            {
                "estimand": "equal-parent mean exposure",
                "numerator": np.nan,
                "denominator": paths["parent"].nunique(),
                "percent": 100 * paths.groupby("parent")[exposed].mean().mean(),
                "note": "each ultimate-parent bucket receives equal weight",
            },
            {
                "estimand": "unique observed upstream nodes located in list",
                "numerator": int(unique_parent_nodes["centre_parent"].sum()),
                "denominator": len(unique_parent_nodes),
                "percent": percent(
                    unique_parent_nodes["centre_parent"].sum(), len(unique_parent_nodes)
                ),
                "note": "node-weighted alternative; no descendant repetition",
            },
            {
                "estimand": "outgoing observed edges from a listed centre",
                "numerator": int(observed_edges["centre_parent"].sum()),
                "denominator": len(observed_edges),
                "percent": percent(
                    observed_edges["centre_parent"].sum(), len(observed_edges)
                ),
                "note": "edge-weighted alternative",
            },
            {
                "estimand": "level-0 roots located in list",
                "numerator": int(roots["entity_country_std"].isin(DECLARED_CENTRES).sum()),
                "denominator": len(roots),
                "percent": percent(
                    roots["entity_country_std"].isin(DECLARED_CENTRES).sum(), len(roots)
                ),
                "note": "gateway-node alternative",
            },
        ]
    )
    sensitivity = pd.DataFrame(rows)
    parent = (
        paths.groupby("parent")
        .agg(
            targets=("target_id", "size"),
            exposed_targets=(exposed, "sum"),
            exposure_share=(exposed, "mean"),
            complete_paths=(
                "path_status",
                lambda values: values.eq("complete_to_ultimate_parent").sum(),
            ),
        )
        .reset_index()
    )
    parent["exposure_percent"] = 100 * parent["exposure_share"]
    parent["complete_path_percent"] = 100 * parent["complete_paths"] / parent["targets"]
    parent = parent.sort_values("exposure_percent", ascending=False)

    missing_edges = tables["edge_occ"][
        tables["edge_occ"]["link_status"].eq("unobserved_parent")
    ]
    metrics = {
        "path_exposure_percent": percent(paths[exposed].sum(), len(paths)),
        "complete_path_exposure_percent": percent(
            complete[exposed].sum(), len(complete)
        ),
        "parent_equal_percent": 100 * paths.groupby("parent")[exposed].mean().mean(),
        "loo_min_percent": 100 * min(value for _, value in pooled_loo),
        "loo_max_percent": 100 * max(value for _, value in pooled_loo),
        "unique_upstream_node_percent": percent(
            unique_parent_nodes["centre_parent"].sum(), len(unique_parent_nodes)
        ),
        "unobserved_parent_edges": float(len(missing_edges)),
        "unobserved_parent_edges_with_reported_country": float(
            missing_edges["reported_immediate_parent_country"].notna().sum()
        ),
    }
    return sensitivity, parent, metrics


def vintage_tables(
    base: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    uin = base[["uin", "parent"]].drop_duplicates("uin").copy()
    uin["length"] = uin["uin"].str.len()
    uin["office"] = uin["uin"].str.slice(0, 2)
    uin["type_character"] = uin["uin"].str.slice(2, 3)
    uin["series"] = uin["uin"].str.slice(3, 5)
    uin["decoded_year"] = pd.to_numeric(
        uin["uin"].str.slice(5, 9), errors="coerce"
    )
    uin["serial"] = uin["uin"].str.slice(9, 13)
    roots = base[base["level"].eq(0)].copy()
    roots["decoded_year"] = pd.to_numeric(
        roots["uin"].str.slice(5, 9), errors="coerce"
    )
    roots["vintage"] = pd.cut(
        roots["decoded_year"],
        [1988, 2004, 2010, 2015, 2020, 2026],
        labels=["<=2004", "2005-10", "2011-15", "2016-20", "2021-25"],
    )
    focus = ["MAURITIUS", "NETHERLANDS", "SINGAPORE", "IFSC GIFT CITY"]
    vintage_rows: list[dict[str, Any]] = []
    for vintage, group in roots.groupby("vintage", observed=True):
        for country in focus:
            count = int(group["entity_country"].eq(country).sum())
            vintage_rows.append(
                {
                    "vintage": str(vintage),
                    "gateway_country": country,
                    "gateway_count": count,
                    "all_gateways": len(group),
                    "share_percent": percent(count, len(group)),
                    "parents": group.loc[
                        group["entity_country"].eq(country), "parent"
                    ].nunique(),
                }
            )
    vintage = pd.DataFrame(vintage_rows)

    roots["era"] = np.select(
        [roots["decoded_year"].le(2010), roots["decoded_year"].ge(2016)],
        ["early <=2010", "late >=2016"],
        default="middle 2011-15",
    )
    contrast_rows: list[dict[str, Any]] = []
    for country in focus:
        early = roots[roots["era"].eq("early <=2010")]
        late = roots[roots["era"].eq("late >=2016")]
        table = np.array(
            [
                [early["entity_country"].eq(country).sum(), early["entity_country"].ne(country).sum()],
                [late["entity_country"].eq(country).sum(), late["entity_country"].ne(country).sum()],
            ]
        )
        # scipy reports row-1 odds / row-2 odds. Reverse the rows so the named
        # estimand is late relative to early while retaining the two-sided test.
        odds_ratio, p_value = fisher_exact(table[::-1])
        country_loo: list[float] = []
        for omitted in sorted(roots["parent"].unique()):
            kept = roots[roots["parent"].ne(omitted)]
            kept_early = kept[kept["era"].eq("early <=2010")]
            kept_late = kept[kept["era"].eq("late >=2016")]
            country_loo.append(
                kept_late["entity_country"].eq(country).mean()
                - kept_early["entity_country"].eq(country).mean()
            )
        paired: list[float] = []
        for _, parent_group in roots.groupby("parent"):
            parent_early = parent_group[parent_group["era"].eq("early <=2010")]
            parent_late = parent_group[parent_group["era"].eq("late >=2016")]
            if len(parent_early) and len(parent_late):
                paired.append(
                    parent_late["entity_country"].eq(country).mean()
                    - parent_early["entity_country"].eq(country).mean()
                )
        contrast_rows.append(
            {
                "gateway_country": country,
                "early_count": int(table[0, 0]),
                "early_denominator": int(table[0].sum()),
                "early_share_percent": percent(table[0, 0], table[0].sum()),
                "late_count": int(table[1, 0]),
                "late_denominator": int(table[1].sum()),
                "late_share_percent": percent(table[1, 0], table[1].sum()),
                "late_minus_early_pp": 100
                * (table[1, 0] / table[1].sum() - table[0, 0] / table[0].sum()),
                "odds_ratio_late_vs_early": odds_ratio,
                "fisher_exact_two_sided_p": p_value,
                "loo_min_change_pp": 100 * min(country_loo),
                "loo_max_change_pp": 100 * max(country_loo),
                "parents_observed_in_both_eras": len(paired),
                "equal_parent_change_pp": 100 * safe_mean(paired),
            }
        )
    contrasts = pd.DataFrame(contrast_rows)
    format_checks = pd.DataFrame(
        [
            {
                "check": "all UIN strings have length 13",
                "numerator": int(uin["length"].eq(13).sum()),
                "denominator": len(uin),
                "result": bool(uin["length"].eq(13).all()),
            },
            {
                "check": "positions 6-9 parse to 1980-2026",
                "numerator": int(uin["decoded_year"].between(1980, 2026).sum()),
                "denominator": len(uin),
                "result": bool(uin["decoded_year"].between(1980, 2026).all()),
            },
            {
                "check": "last four positions are digits",
                "numerator": int(uin["serial"].str.fullmatch(r"\d{4}").sum()),
                "denominator": len(uin),
                "result": bool(uin["serial"].str.fullmatch(r"\d{4}").all()),
            },
            {
                "check": "UINs with observed level-0 entity",
                "numerator": roots["uin"].nunique(),
                "denominator": len(uin),
                "result": roots["uin"].nunique() == len(uin),
            },
        ]
    )
    contrast_index = contrasts.set_index("gateway_country")
    metrics = {
        "root_uins": float(roots["uin"].nunique()),
        "all_uins": float(len(uin)),
        "mauritius_early_percent": float(
            contrast_index.loc["MAURITIUS", "early_share_percent"]
        ),
        "mauritius_late_percent": float(
            contrast_index.loc["MAURITIUS", "late_share_percent"]
        ),
        "mauritius_fisher_p": float(
            contrast_index.loc["MAURITIUS", "fisher_exact_two_sided_p"]
        ),
        "singapore_fisher_p": float(
            contrast_index.loc["SINGAPORE", "fisher_exact_two_sided_p"]
        ),
        "gift_fisher_p": float(
            contrast_index.loc["IFSC GIFT CITY", "fisher_exact_two_sided_p"]
        ),
    }
    return vintage, contrasts, format_checks, metrics


def coverage_tables(
    raw: pd.DataFrame, tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    coverage = (
        raw.groupby("target_id")
        .agg(
            parent=("parent", "first"),
            level=("level", "first"),
            any_ready=("ready_for_valuation", "max"),
            any_source=("source_found", "max"),
            any_variables_parsed=("variables_parsed", "max"),
            any_equity=("equity", lambda values: values.notna().any()),
        )
        .reset_index()
    )
    path_fields = tables["paths"][
        ["target_id", "path_status", "reconstructed_level"]
    ]
    coverage = coverage.merge(path_fields, on="target_id", how="left")
    preferred = tables["preferred"]
    for source, outcome in [
        ("balance_ready", "any_balance_ready"),
        ("balance_basic_plausible", "any_basic_plausible"),
        ("pl_valid", "any_pl_valid"),
    ]:
        mapping = preferred.groupby("target_id")[source].max()
        coverage[outcome] = (
            coverage["target_id"].map(mapping).fillna(False).astype(bool)
        )
    coverage["deep_reported"] = coverage["level"].ge(3).astype(int)
    coverage["deep_graph"] = coverage["reconstructed_level"].ge(3).astype(int)

    rows: list[dict[str, Any]] = []
    for outcome in ["any_ready", "any_basic_plausible", "any_pl_valid"]:
        frame = coverage.copy()
        raw_cells = frame.groupby("deep_reported")[outcome].mean()
        paired = paired_parent_difference(frame, outcome, "deep_reported")
        loo = leave_one_parent_out(
            frame,
            lambda z: within_parent_coefficient(z, outcome, "deep_reported"),
        )
        complete = frame[frame["path_status"].eq("complete_to_ultimate_parent")]
        graph_cells = complete.groupby("deep_graph")[outcome].mean()
        rows.append(
            {
                "outcome": outcome,
                "positive_entities": int(frame[outcome].sum()),
                "all_entities": len(frame),
                "entity_rate_percent": 100 * frame[outcome].mean(),
                "parent_equal_rate_percent": 100
                * frame.groupby("parent")[outcome].mean().mean(),
                "reported_shallow_rate_percent": 100 * raw_cells.get(0, np.nan),
                "reported_deep_rate_percent": 100 * raw_cells.get(1, np.nan),
                "reported_raw_deep_minus_shallow_pp": 100
                * (raw_cells.get(1, np.nan) - raw_cells.get(0, np.nan)),
                "reported_parent_fe_pp": 100
                * within_parent_coefficient(frame, outcome, "deep_reported"),
                "reported_equal_parent_paired_difference_pp": 100 * paired.mean(),
                "reported_paired_parent_median_difference_pp": 100 * paired.median(),
                "parents_with_both_depth_cells": len(paired),
                "fe_loo_min_pp": 100 * min(value for _, value in loo),
                "fe_loo_max_pp": 100 * max(value for _, value in loo),
                "complete_graph_shallow_rate_percent": 100
                * graph_cells.get(0, np.nan),
                "complete_graph_deep_rate_percent": 100
                * graph_cells.get(1, np.nan),
                "complete_graph_parent_fe_pp": 100
                * within_parent_coefficient(complete, outcome, "deep_graph"),
            }
        )
    selection = pd.DataFrame(rows)
    parent = (
        coverage.groupby("parent")
        .agg(
            entities=("target_id", "size"),
            ready_entities=("any_ready", "sum"),
            ready_rate=("any_ready", "mean"),
            source_entities=("any_source", "sum"),
            parsed_equity_entities=("any_equity", "sum"),
        )
        .reset_index()
    )
    parent["ready_percent"] = 100 * parent["ready_rate"]
    parent = parent.sort_values("ready_percent", ascending=False)
    coverage_ids = coverage.merge(
        tables["occ"][["target_id", "group_entity_id", "global_entity_id"]],
        on="target_id",
        how="left",
    )
    counting_rows: list[dict[str, Any]] = []
    for entity_key in ["target_id", "group_entity_id", "global_entity_id"]:
        unique = (
            coverage_ids.sort_values(["parent", "target_id"])
            .groupby(entity_key, as_index=False)
            .agg(any_ready=("any_ready", "max"), parent=("parent", "first"))
        )
        counting_rows.append(
            {
                "counting_unit": entity_key,
                "entities": len(unique),
                "ready_entities": int(unique["any_ready"].sum()),
                "ready_percent": 100 * unique["any_ready"].mean(),
                "equal_parent_ready_percent": 100
                * unique.groupby("parent")["any_ready"].mean().mean(),
            }
        )
    counting = pd.DataFrame(counting_rows)
    ready = selection.set_index("outcome").loc["any_ready"]
    metrics = {
        "source_entities": float(coverage["any_source"].sum()),
        "equity_entities": float(coverage["any_equity"].sum()),
        "ready_entities": float(coverage["any_ready"].sum()),
        "ready_percent": float(100 * coverage["any_ready"].mean()),
        "ready_parent_equal_percent": float(
            100 * coverage.groupby("parent")["any_ready"].mean().mean()
        ),
        "raw_depth_gap_pp": float(ready["reported_raw_deep_minus_shallow_pp"]),
        "parent_fe_depth_gap_pp": float(ready["reported_parent_fe_pp"]),
        "parent_fe_loo_min_pp": float(ready["fe_loo_min_pp"]),
        "parent_fe_loo_max_pp": float(ready["fe_loo_max_pp"]),
    }
    return selection, parent, counting, metrics


def mismatch_tables(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    paths = tables["paths"]
    complete = paths[paths["path_status"].eq("complete_to_ultimate_parent")].copy()
    complete["mismatch"] = complete[
        "reported_level_matches_reconstruction"
    ].eq(0)
    complete["reconstructed_minus_reported"] = (
        complete["reconstructed_level"] - complete["reported_level"]
    )
    parent = (
        complete.groupby("parent")
        .agg(
            complete_paths=("target_id", "size"),
            mismatches=("mismatch", "sum"),
            mismatch_rate=("mismatch", "mean"),
            maximum_reported_level=("reported_level", "max"),
            maximum_reconstructed_level=("reconstructed_level", "max"),
        )
        .reset_index()
    )
    parent["mismatch_percent"] = 100 * parent["mismatch_rate"]
    parent = parent.sort_values("mismatches", ascending=False)
    loo = leave_one_parent_out(complete, lambda z: z["mismatch"].mean())
    variants: list[dict[str, Any]] = []
    for entity_key in ["target_id", "group_entity_id", "global_entity_id"]:
        unique = complete.sort_values(["parent", "target_id"]).drop_duplicates(
            entity_key
        )
        variants.append(
            {
                "counting_unit": entity_key,
                "mismatches": int(unique["mismatch"].sum()),
                "assessable_paths": len(unique),
                "mismatch_percent": percent(unique["mismatch"].sum(), len(unique)),
            }
        )
    variants.extend(
        [
            {
                "counting_unit": "all targets; incomplete assumed matching",
                "mismatches": int(complete["mismatch"].sum()),
                "assessable_paths": len(paths),
                "mismatch_percent": percent(complete["mismatch"].sum(), len(paths)),
            },
            {
                "counting_unit": "all targets; incomplete assumed mismatching",
                "mismatches": int(
                    complete["mismatch"].sum() + len(paths) - len(complete)
                ),
                "assessable_paths": len(paths),
                "mismatch_percent": percent(
                    complete["mismatch"].sum() + len(paths) - len(complete), len(paths)
                ),
            },
            {
                "counting_unit": "equal-parent mean on complete paths",
                "mismatches": np.nan,
                "assessable_paths": complete["parent"].nunique(),
                "mismatch_percent": 100
                * complete.groupby("parent")["mismatch"].mean().mean(),
            },
        ]
    )
    sensitivity = pd.DataFrame(variants)
    motherson = parent[parent["parent"].eq("SAMVARDHANA MOTHERSON INTERNATI")].iloc[
        0
    ]
    metrics = {
        "complete_paths": float(len(complete)),
        "mismatches": float(complete["mismatch"].sum()),
        "mismatch_percent": percent(complete["mismatch"].sum(), len(complete)),
        "motherson_mismatches": float(motherson["mismatches"]),
        "motherson_share_of_mismatches_percent": percent(
            motherson["mismatches"], complete["mismatch"].sum()
        ),
        "parent_equal_percent": float(
            100 * complete.groupby("parent")["mismatch"].mean().mean()
        ),
        "loo_min_percent": 100 * min(value for _, value in loo),
        "loo_max_percent": 100 * max(value for _, value in loo),
        "all_differences_negative": bool(
            complete.loc[
                complete["mismatch"], "reconstructed_minus_reported"
            ].lt(0).all()
        ),
    }
    return sensitivity, parent, metrics


def concentration_summary(frame: pd.DataFrame, channel: str) -> pd.DataFrame:
    usable = frame.dropna(subset=[channel]).copy()
    by_channel = (
        usable.groupby(["parent", channel])
        .agg(entities=("target_id", "nunique"))
        .reset_index()
    )
    totals = usable.groupby("parent")["target_id"].nunique()
    top = by_channel.groupby("parent")["entities"].max()
    hhi = (
        by_channel.assign(
            share=lambda data: data["entities"]
            / data.groupby("parent")["entities"].transform("sum")
        )
        .assign(square=lambda data: data["share"] ** 2)
        .groupby("parent")["square"]
        .sum()
    )
    return pd.DataFrame(
        {
            "covered_entities": totals,
            "largest_channel_entities": top,
            "largest_channel_share": top / totals,
            "channel_hhi": hhi,
            "effective_channels": 1 / hhi,
        }
    )


def gateway_dependency_tables(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    occ = tables["occ"].copy()
    roots = occ[occ["level"].eq(0)][
        ["uin", "target_id", "entity_name", "entity_country_std"]
    ].drop_duplicates("uin")
    root_map = roots.set_index("uin")

    uin_concentration = concentration_summary(occ, "uin")
    parent_base = occ.groupby("parent").agg(
        target_entities=("target_id", "nunique"),
        destination_countries=("entity_country_std", "nunique"),
        uins=("uin", "nunique"),
    )
    top_uin = (
        occ.groupby(["parent", "uin"])
        .agg(entities=("target_id", "nunique"))
        .reset_index()
        .sort_values(["parent", "entities", "uin"], ascending=[True, False, True])
        .drop_duplicates("parent")
        .set_index("parent")
    )
    parent = parent_base.join(
        top_uin[["uin", "entities"]].rename(
            columns={"uin": "largest_uin", "entities": "largest_uin_entities"}
        )
    ).join(
        uin_concentration[
            ["largest_channel_share", "channel_hhi", "effective_channels"]
        ].rename(
            columns={
                "largest_channel_share": "largest_uin_share",
                "channel_hhi": "uin_hhi",
                "effective_channels": "effective_uins",
            }
        )
    )
    parent["largest_uin_root_target_id"] = parent["largest_uin"].map(
        root_map["target_id"]
    )
    parent["largest_uin_root_name"] = parent["largest_uin"].map(
        root_map["entity_name"]
    )
    parent["largest_uin_root_country"] = parent["largest_uin"].map(
        root_map["entity_country_std"]
    )
    parent["largest_uin_has_observed_root"] = parent[
        "largest_uin_root_target_id"
    ].notna()

    steps = tables["steps"]
    gateway_map = steps[
        steps["path_status"].eq("complete_to_ultimate_parent")
        & steps["node_kind"].eq("observed_entity")
        & steps["step_from_upstream"].eq(1)
    ][
        ["terminal_target_id", "parent", "target_id", "entity_name", "country"]
    ].rename(
        columns={
            "target_id": "graph_gateway_target_id",
            "entity_name": "graph_gateway_name",
            "country": "graph_gateway_country",
        }
    )
    graph_occ = occ.merge(
        gateway_map,
        left_on=["target_id", "parent"],
        right_on=["terminal_target_id", "parent"],
        how="left",
    )
    graph_concentration = concentration_summary(
        graph_occ, "graph_gateway_target_id"
    ).rename(
        columns={
            "covered_entities": "graph_complete_entities",
            "largest_channel_entities": "largest_graph_gateway_entities",
            "largest_channel_share": "largest_graph_gateway_share",
            "channel_hhi": "graph_gateway_hhi",
            "effective_channels": "effective_graph_gateways",
        }
    )
    graph_top = (
        graph_occ.dropna(subset=["graph_gateway_target_id"])
        .groupby(
            [
                "parent",
                "graph_gateway_target_id",
                "graph_gateway_name",
                "graph_gateway_country",
            ]
        )
        .agg(entities=("target_id", "nunique"))
        .reset_index()
        .sort_values(
            ["parent", "entities", "graph_gateway_target_id"],
            ascending=[True, False, True],
        )
        .drop_duplicates("parent")
        .set_index("parent")
    )
    parent = parent.join(graph_concentration).join(
        graph_top[
            [
                "graph_gateway_target_id",
                "graph_gateway_name",
                "graph_gateway_country",
            ]
        ]
    )
    parent["graph_complete_share"] = (
        parent["graph_complete_entities"] / parent["target_entities"]
    )
    parent["largest_uin_share_percent"] = 100 * parent["largest_uin_share"]
    parent["largest_graph_gateway_share_percent"] = (
        100 * parent["largest_graph_gateway_share"]
    )
    parent["graph_complete_percent"] = 100 * parent["graph_complete_share"]
    parent = parent.reset_index().sort_values(
        "largest_uin_share", ascending=False
    )

    sensitivity_rows: list[dict[str, Any]] = []
    for entity_key in ["target_id", "group_entity_id", "global_entity_id"]:
        unique = occ.sort_values(["parent", "uin", "target_id"]).drop_duplicates(
            entity_key
        )
        concentration = concentration_summary(unique, "uin")
        sensitivity_rows.append(
            {
                "method": "UIN channel",
                "entity_counting": entity_key,
                "entities": len(unique),
                "pooled_largest_channel_share_percent": percent(
                    concentration["largest_channel_entities"].sum(),
                    concentration["covered_entities"].sum(),
                ),
                "equal_parent_largest_channel_share_percent": 100
                * concentration["largest_channel_share"].mean(),
                "median_parent_largest_channel_share_percent": 100
                * concentration["largest_channel_share"].median(),
            }
        )
    graph_conc = concentration_summary(graph_occ, "graph_gateway_target_id")
    sensitivity_rows.append(
        {
            "method": "complete graph first-hop gateway",
            "entity_counting": "target_id",
            "entities": int(graph_conc["covered_entities"].sum()),
            "pooled_largest_channel_share_percent": percent(
                graph_conc["largest_channel_entities"].sum(),
                graph_conc["covered_entities"].sum(),
            ),
            "equal_parent_largest_channel_share_percent": 100
            * graph_conc["largest_channel_share"].mean(),
            "median_parent_largest_channel_share_percent": 100
            * graph_conc["largest_channel_share"].median(),
        }
    )
    sensitivity = pd.DataFrame(sensitivity_rows)

    uin_loo: list[float] = []
    indexed = parent.set_index("parent")
    for omitted in indexed.index:
        kept = indexed.drop(index=omitted)
        uin_loo.append(
            kept["largest_uin_entities"].sum() / kept["target_entities"].sum()
        )
    diversified = parent[parent["destination_countries"].ge(20)]
    metrics = {
        "pooled_top_uin_percent": percent(
            parent["largest_uin_entities"].sum(), parent["target_entities"].sum()
        ),
        "parent_equal_top_uin_percent": 100 * parent["largest_uin_share"].mean(),
        "median_parent_top_uin_percent": 100 * parent["largest_uin_share"].median(),
        "uin_loo_min_percent": 100 * min(uin_loo),
        "uin_loo_max_percent": 100 * max(uin_loo),
        "diversified_parent_count": float(len(diversified)),
        "diversified_parent_equal_top_uin_percent": 100
        * diversified["largest_uin_share"].mean(),
        "graph_pooled_top_gateway_percent": percent(
            graph_conc["largest_channel_entities"].sum(),
            graph_conc["covered_entities"].sum(),
        ),
        "graph_coverage_percent": percent(
            graph_conc["covered_entities"].sum(), len(occ)
        ),
    }
    return parent, sensitivity, metrics


def stake_depth_tables(
    tables: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    paths = tables["paths"][
        ["target_id", "path_status", "reconstructed_level"]
    ]
    frame = tables["occ"].merge(paths, on="target_id", how="left")
    frame = frame[frame["level"].gt(0)].copy()
    frame["positive_stake"] = frame["stake"].gt(0)
    frame["fully_owned"] = frame["stake"].ge(99.5)
    frame["reported_deep"] = frame["level"].ge(2).astype(int)
    frame["graph_deep"] = frame["reconstructed_level"].ge(2).astype(int)
    frame["uin_third_character"] = frame["uin"].str.slice(2, 3)

    sample_masks = {
        "all positive recorded stakes": frame["positive_stake"],
        "exclude Reliance Industries": frame["positive_stake"]
        & frame["parent"].ne("RELIANCE INDUSTRIES LTD"),
        "exclude UIN third-character P": frame["positive_stake"]
        & frame["uin_third_character"].ne("P"),
        "exclude Breakthrough Energy child edges": frame["positive_stake"]
        & ~frame["immediate_parent"].str.upper().str.contains(
            "BREAKTHROUGH ENERGY VENTURES", na=False
        ),
        "complete paths only": frame["positive_stake"]
        & frame["path_status"].eq("complete_to_ultimate_parent"),
    }
    rows: list[dict[str, Any]] = []
    for sample, mask in sample_masks.items():
        selected = frame[mask].copy()
        cells = selected.groupby("reported_deep")["fully_owned"].mean()
        parent_cells = selected.groupby(["parent", "reported_deep"])[
            "fully_owned"
        ].mean()
        parent_equal = parent_cells.groupby("reported_deep").mean()
        paired = paired_parent_difference(
            selected, "fully_owned", "reported_deep"
        )
        loo = leave_one_parent_out(
            selected,
            lambda z: z.groupby("reported_deep")["fully_owned"].mean().diff().iloc[-1]
            if z["reported_deep"].nunique() == 2
            else np.nan,
        )
        rows.append(
            {
                "sample": sample,
                "level1_positive_stakes": int(selected["reported_deep"].eq(0).sum()),
                "level2plus_positive_stakes": int(selected["reported_deep"].eq(1).sum()),
                "level1_full_ownership_percent": 100 * cells.get(0, np.nan),
                "level2plus_full_ownership_percent": 100 * cells.get(1, np.nan),
                "entity_weighted_difference_pp": 100
                * (cells.get(1, np.nan) - cells.get(0, np.nan)),
                "parent_equal_level1_percent": 100 * parent_equal.get(0, np.nan),
                "parent_equal_level2plus_percent": 100
                * parent_equal.get(1, np.nan),
                "parent_equal_difference_pp": 100
                * (parent_equal.get(1, np.nan) - parent_equal.get(0, np.nan)),
                "paired_parent_difference_pp": 100 * paired.mean(),
                "paired_parent_median_difference_pp": 100 * paired.median(),
                "parents_with_both_depth_cells": len(paired),
                "loo_min_entity_difference_pp": 100 * min(value for _, value in loo),
                "loo_max_entity_difference_pp": 100 * max(value for _, value in loo),
            }
        )
    sensitivity = pd.DataFrame(rows)

    bounds_rows: list[dict[str, Any]] = []
    for depth, group in frame.groupby("reported_deep"):
        positive = group[group["positive_stake"]]
        known_full = int(positive["fully_owned"].sum())
        zeros = int(group["stake"].eq(0).sum())
        bounds_rows.append(
            {
                "depth_band": "level 2+" if depth else "level 1",
                "all_edges": len(group),
                "positive_recorded_stakes": len(positive),
                "zero_stakes_treated_as_unknown": zeros,
                "known_full_ownership_edges": known_full,
                "complete_case_full_ownership_percent": percent(
                    known_full, len(positive)
                ),
                "full_ownership_percent_if_zeros_not_full": percent(
                    known_full, len(group)
                ),
                "full_ownership_percent_if_zeros_full": percent(
                    known_full + zeros, len(group)
                ),
            }
        )
    bounds = pd.DataFrame(bounds_rows)

    positive = frame[frame["positive_stake"]].copy()
    parent_cells = (
        positive.groupby(["parent", "reported_deep"])
        .agg(
            edges=("target_id", "size"),
            full_ownership_rate=("fully_owned", "mean"),
            mean_stake=("stake", "mean"),
        )
        .reset_index()
    )
    parent_wide = parent_cells.pivot(
        index="parent", columns="reported_deep", values="full_ownership_rate"
    ).rename(columns={0: "level1_full_rate", 1: "level2plus_full_rate"})
    parent_wide["level2plus_minus_level1_pp"] = 100 * (
        parent_wide.get("level2plus_full_rate") - parent_wide.get("level1_full_rate")
    )
    parent_wide = parent_wide.reset_index().sort_values(
        "level2plus_minus_level1_pp", ascending=False
    )

    graph = frame[
        frame["positive_stake"]
        & frame["path_status"].eq("complete_to_ultimate_parent")
        & frame["reconstructed_level"].ge(1)
    ]
    graph_cells = graph.groupby("graph_deep")["fully_owned"].mean()
    graph_paired = paired_parent_difference(graph, "fully_owned", "graph_deep")
    base_row = sensitivity.set_index("sample").loc["all positive recorded stakes"]
    metrics = {
        "positive_nonroot_stakes": float(len(positive)),
        "zero_nonroot_stakes": float(frame["stake"].eq(0).sum()),
        "level1_full_percent": float(base_row["level1_full_ownership_percent"]),
        "level2plus_full_percent": float(
            base_row["level2plus_full_ownership_percent"]
        ),
        "entity_weighted_gap_pp": float(base_row["entity_weighted_difference_pp"]),
        "parent_equal_gap_pp": float(base_row["parent_equal_difference_pp"]),
        "paired_parent_gap_pp": float(base_row["paired_parent_difference_pp"]),
        "exclude_reliance_gap_pp": float(
            sensitivity.set_index("sample").loc[
                "exclude Reliance Industries", "entity_weighted_difference_pp"
            ]
        ),
        "graph_entity_gap_pp": 100
        * (graph_cells.get(1, np.nan) - graph_cells.get(0, np.nan)),
        "graph_paired_parent_gap_pp": 100 * graph_paired.mean(),
    }
    return sensitivity, bounds, parent_wide, metrics


def make_figures(
    gateway_parent: pd.DataFrame,
    stake_sensitivity: pd.DataFrame,
    stake_parent: pd.DataFrame,
    output: Path,
) -> None:
    figure_dir = output / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    figure, axis = plt.subplots(figsize=(14, 9))
    plot = gateway_parent.copy()
    sizes = 35 + 3.2 * plot["target_entities"]
    scatter = axis.scatter(
        plot["destination_countries"],
        100 * plot["largest_uin_share"],
        s=sizes,
        c=plot["uins"],
        cmap="viridis_r",
        alpha=0.82,
        edgecolor="white",
        linewidth=0.8,
    )
    for row in plot.itertuples(index=False):
        if row.destination_countries >= 20 and row.largest_uin_share >= 0.8:
            axis.annotate(
                str(row.parent).replace(" LIMITED", "").replace(" LTD", ""),
                (row.destination_countries, 100 * row.largest_uin_share),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
            )
    axis.axhline(
        100 * plot["largest_uin_share"].mean(),
        color="#8c2d04",
        linestyle="--",
        linewidth=1.5,
        label="equal-parent mean",
    )
    axis.set(
        xlabel="Distinct destination jurisdictions in parent group",
        ylabel="Share of group targets carrying its largest UIN (%)",
        title="Geographic breadth can coexist with one dominant UIN channel",
    )
    colorbar = figure.colorbar(scatter, ax=axis, pad=0.02)
    colorbar.set_label("Number of UINs in parent group")
    axis.legend(loc="lower left", frameon=True)
    figure.tight_layout()
    figure.savefig(
        figure_dir / "gateway_dependency_landscape.png",
        dpi=180,
        metadata={"Software": "src/codex/review_increment.py"},
    )
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(16, 8))
    focus_order = [
        "all positive recorded stakes",
        "exclude Reliance Industries",
        "exclude UIN third-character P",
        "exclude Breakthrough Energy child edges",
    ]
    focus = stake_sensitivity.set_index("sample").loc[focus_order].reset_index()
    labels = [
        "All positive stakes",
        "Exclude Reliance",
        "Exclude UIN char. P",
        "Exclude BEV child edges",
    ]
    positions = np.arange(len(focus))
    width = 0.36
    axes[0].barh(
        positions - width / 2,
        focus["level1_full_ownership_percent"],
        height=width,
        color="#3182bd",
        label="Reported level 1",
    )
    axes[0].barh(
        positions + width / 2,
        focus["level2plus_full_ownership_percent"],
        height=width,
        color="#e6550d",
        label="Reported level 2+",
    )
    axes[0].set_yticks(positions, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 100)
    axes[0].set_xlabel("Fully owned among positive recorded stakes (%)")
    axes[0].set_title("Pooled depth gradient is sample-sensitive")
    axes[0].legend(loc="lower right", fontsize=10)

    parent_plot = stake_parent.dropna(
        subset=["level2plus_minus_level1_pp"]
    ).sort_values("level2plus_minus_level1_pp")
    colors = np.where(
        parent_plot["parent"].eq("RELIANCE INDUSTRIES LTD"), "#b2182b", "#6baed6"
    )
    axes[1].barh(
        np.arange(len(parent_plot)),
        parent_plot["level2plus_minus_level1_pp"],
        color=colors,
    )
    axes[1].axvline(0, color="black", linewidth=1)
    axes[1].set_yticks(
        np.arange(len(parent_plot)),
        [str(value)[:27] for value in parent_plot["parent"]],
        fontsize=8,
    )
    axes[1].set_xlabel("Level 2+ minus level 1 full-ownership rate (pp)")
    axes[1].set_title("Within-parent differences cluster near zero")
    figure.suptitle(
        "Ownership stakes: entity weighting and parent weighting answer different questions",
        y=1.01,
    )
    figure.tight_layout()
    figure.savefig(
        figure_dir / "ownership_stake_depth_sensitivity.png",
        dpi=180,
        bbox_inches="tight",
        metadata={"Software": "src/codex/review_increment.py"},
    )
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--codex-output", type=Path, default=DEFAULT_CODEX_OUTPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw, tables = load_inputs(args.input, args.codex_output)
    base = structural_base(raw)
    if len(base) != len(tables["occ"]):
        raise AssertionError("raw and blind-discovery target counts differ")

    uin_multiplier, uin_metrics = uin_multiplier_tables(base, tables)
    gateway_roots, gateway_summary, gateway_metrics = gateway_amplification_tables(
        tables
    )
    conduit_sensitivity, conduit_parent, conduit_metrics = conduit_exposure_tables(
        tables
    )
    vintage, vintage_contrasts, uin_format, vintage_metrics = vintage_tables(base)
    coverage_selection, coverage_parent, coverage_counting, coverage_metrics = (
        coverage_tables(raw, tables)
    )
    mismatch_sensitivity, mismatch_parent, mismatch_metrics = mismatch_tables(tables)
    gateway_parent, gateway_dependency_sensitivity, dependency_metrics = (
        gateway_dependency_tables(tables)
    )
    stake_sensitivity, stake_bounds, stake_parent, stake_metrics = stake_depth_tables(
        tables
    )

    table_dir = args.output / "tables"
    outputs = {
        "uin_multiplier_sensitivity.csv": uin_multiplier,
        "gateway_root_descendants.csv": gateway_roots,
        "gateway_amplification_review.csv": gateway_summary,
        "conduit_exposure_sensitivity.csv": conduit_sensitivity,
        "conduit_exposure_by_parent.csv": conduit_parent,
        "gateway_vintage_review.csv": vintage,
        "gateway_vintage_contrasts.csv": vintage_contrasts,
        "uin_format_internal_checks.csv": uin_format,
        "coverage_selection_review.csv": coverage_selection,
        "coverage_by_parent_review.csv": coverage_parent,
        "coverage_counting_sensitivity.csv": coverage_counting,
        "depth_mismatch_sensitivity.csv": mismatch_sensitivity,
        "depth_mismatch_by_parent.csv": mismatch_parent,
        "gateway_dependency_by_parent.csv": gateway_parent,
        "gateway_dependency_sensitivity.csv": gateway_dependency_sensitivity,
        "stake_depth_sensitivity.csv": stake_sensitivity,
        "stake_zero_bounds.csv": stake_bounds,
        "stake_depth_by_parent.csv": stake_parent,
    }
    for filename, frame in outputs.items():
        write_csv(frame, table_dir / filename)

    make_figures(gateway_parent, stake_sensitivity, stake_parent, args.output)

    metrics = {
        "reviewed_commit": REVIEWED_COMMIT,
        "input_sha256": sha256_file(args.input),
        "uin_multiplier": uin_metrics,
        "gateway_amplification": gateway_metrics,
        "conduit_exposure": conduit_metrics,
        "gateway_vintage": vintage_metrics,
        "coverage_selection": coverage_metrics,
        "depth_mismatch": mismatch_metrics,
        "gateway_dependency_new": dependency_metrics,
        "stake_depth_new": stake_metrics,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output / "review_metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    files = sorted(
        path
        for path in args.output.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "reviewed_commit": REVIEWED_COMMIT,
        "input_sha256": sha256_file(args.input),
        "files": {
            str(path.relative_to(args.output)): sha256_file(path) for path in files
        },
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
