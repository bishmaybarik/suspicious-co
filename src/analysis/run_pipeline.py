#!/usr/bin/env python3
"""Build the complete canonical analysis, outputs, and research handoff."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/suspicious-co-matplotlib")

import matplotlib
import networkx
import numpy
import pandas

from .config import (
    DICTIONARY_PATH,
    DICTIONARY_SHA256,
    FIGURE_DIR,
    INPUT_PATH,
    INPUT_SHA256,
    OUTPUT_ROOT,
    ROOT,
    TABLE_DIR,
)
from .data_model import AnalysisData, build_analysis_data, sha256_file
from .figures import make_figures
from .rendering import write_outputs
from .statistics import FinalResults, build_final_results


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_central_invariants(data: AnalysisData, results: FinalResults) -> None:
    metrics = results.metrics
    require(len(data.raw) == 3742, "unexpected raw-row count")
    require(len(data.preferred) == 3567, "unexpected preferred-row count")
    require(len(data.occurrences) == 1834, "unexpected target count")
    require(len(data.group_entities) == 1830, "unexpected parent-entity count")
    require(len(data.global_entities) == 1818, "unexpected global-entity count")
    require(data.occurrences["uin"].nunique() == 186, "unexpected UIN count")
    require(data.occurrences["parent"].nunique() == 28, "unexpected parent count")
    require(int(data.occurrences["level"].eq(0).sum()) == 184, "unexpected root count")
    require(int(data.edges["reported_level"].gt(0).sum()) == 1650, "unexpected nonroot-edge count")
    require(int(data.edges["parent_node_type"].eq("unobserved_entity").sum()) == 78, "unexpected missing-parent edge count")
    require(int(data.edges.loc[data.edges["parent_node_type"].eq("unobserved_entity"), "parent_node_id"].nunique()) == 18, "unexpected normalized missing-parent count")
    require(int(data.paths["path_status"].eq("complete_to_ultimate_parent").sum()) == 1687, "unexpected complete-path count")
    require(int(data.paths["reported_level_matches_reconstruction"].eq(0).sum()) == 236, "unexpected depth-mismatch count")
    require(int(data.edges.loc[data.edges["reported_level"].gt(0), "cross_border_edge"].sum()) == 951, "unexpected cross-border count")
    require(int(data.preferred["ready_for_valuation"].eq(1).sum()) == 560, "unexpected ready-row count")
    require(metrics["valuation_ready_targets"] == 265, "unexpected ready-target count")
    construction = results.tables["01_sample_construction"].set_index("stage")
    require(
        int(construction.loc["Targets with parsed balance sheet", "count"]) == 444,
        "unexpected parsed-balance-sheet target count",
    )
    require(metrics["zero_nonroot_stakes"] == 406, "unexpected zero-stake count")
    require(metrics["repeated_signatures"] == 51, "unexpected repeated-signature count")
    require(metrics["proven_reuse_clusters"] == 33, "unexpected evidence-reuse count")
    depth_audit = results.tables["08_depth_audit"].set_index("statistic")
    require(
        int(depth_audit.loc["Manufacturing targets at reported level 5+", "numerator"])
        == 242,
        "unexpected deep-manufacturing count",
    )
    require(
        int(
            depth_audit.loc[
                "Motherson + Hindalco share of deep manufacturing", "numerator"
            ]
        )
        == 240,
        "unexpected parent concentration in deep manufacturing",
    )
    require(abs(metrics["cross_border_pooled_pct"] - 57.6363636364) < 1e-8, "cross-border estimate drifted")
    require(abs(metrics["modal_uin_pooled_pct"] - 59.7055616140) < 1e-8, "modal-UIN estimate drifted")
    require(abs(metrics["largest_observed_subtree_median_pct"] - 43.2) < 0.1, "observed-subtree median drifted")
    require(abs(metrics["strict_dag_dominator_median_pct"] - 41.72) < 0.1, "DAG-dominator median drifted")
    require(abs(metrics["top_three_upstream_pooled_pct"] - 62.15921483) < 1e-8, "three-country cover drifted")


def output_hashes(output_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            hashes[str(path.relative_to(output_root))] = sha256_file(path)
    return hashes


def write_manifest(
    output_root: Path,
    input_path: Path,
    dictionary_path: Path,
    results: FinalResults,
) -> None:
    manifest = {
        "pipeline": "src.analysis.run_pipeline",
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
        },
        "dictionary": {
            "path": str(dictionary_path),
            "sha256": sha256_file(dictionary_path),
        },
        "software": {
            "python": platform.python_version(),
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "networkx": networkx.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "central_metrics": results.metrics,
        "output_sha256": output_hashes(output_root),
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build(
    input_path: Path,
    dictionary_path: Path,
    output_root: Path,
    report_root: Path,
    clean: bool = False,
) -> FinalResults:
    require(input_path.is_file(), f"input not found: {input_path}")
    require(dictionary_path.is_file(), f"dictionary not found: {dictionary_path}")
    require(sha256_file(input_path) == INPUT_SHA256, "immutable input hash mismatch")
    require(
        sha256_file(dictionary_path) == DICTIONARY_SHA256,
        "immutable dictionary hash mismatch",
    )
    if clean and output_root.exists():
        # The target is an explicit pipeline-owned directory, never a glob or
        # environment-expanded path.
        shutil.rmtree(output_root)
    table_dir = output_root / "tables"
    figure_dir = output_root / "figures"
    data = build_analysis_data(input_path)
    results = build_final_results(data)
    validate_central_invariants(data, results)
    write_outputs(
        results,
        table_dir,
        input_path,
        dictionary_path,
        report_root=report_root,
    )
    make_figures(results, figure_dir)
    write_manifest(output_root, input_path, dictionary_path, results)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--dictionary", type=Path, default=DICTIONARY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=ROOT)
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = build(
        args.input,
        args.dictionary,
        args.output,
        args.report_root,
        clean=args.clean,
    )
    print(json.dumps(results.metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
