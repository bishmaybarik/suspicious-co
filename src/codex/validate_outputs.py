#!/usr/bin/env python3
"""Validate hierarchy invariants and optionally rebuild all CSVs in isolation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "outputs/codex"
PIPELINE = ROOT / "src/codex/research_pipeline.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(output: Path) -> dict[str, int]:
    data = output / "data"
    tables = output / "tables"
    metrics = json.loads((output / "key_metrics.json").read_text(encoding="utf-8"))

    occurrences = pd.read_csv(data / "entity_occurrences.csv")
    group_entities = pd.read_csv(data / "unique_entities_parent_scoped.csv")
    global_entities = pd.read_csv(data / "unique_entities_global.csv")
    edge_occurrences = pd.read_csv(data / "parent_child_edge_occurrences.csv")
    logical_edges = pd.read_csv(data / "parent_child_edges.csv")
    paths = pd.read_csv(data / "ownership_paths.csv")
    path_steps = pd.read_csv(data / "ownership_path_steps.csv")
    preferred = pd.read_csv(data / "preferred_financial_panel.csv")
    invariance = pd.read_csv(tables / "structural_invariance.csv")
    denominators = pd.read_csv(tables / "row_denominators.csv").set_index("denominator")

    expected = metrics["counts"]
    require(len(occurrences) == expected["target_occurrences"], "target count mismatch")
    require(occurrences["target_id"].is_unique, "target_id is not unique in occurrences")
    require(
        len(group_entities) == expected["parent_scoped_normalized_entities"],
        "parent-scoped entity count mismatch",
    )
    require(group_entities["group_entity_id"].is_unique, "group entity IDs not unique")
    require(
        len(global_entities) == expected["global_normalized_entities"],
        "global entity count mismatch",
    )
    require(global_entities["global_entity_id"].is_unique, "global IDs not unique")
    require(len(edge_occurrences) == len(occurrences), "one edge per target violated")
    require(edge_occurrences["child_target_id"].is_unique, "edge child targets repeat")
    require(
        int(logical_edges["target_occurrences"].sum()) == len(occurrences),
        "logical-edge multiplicities do not recover targets",
    )
    require(len(paths) == len(occurrences), "one path record per target violated")
    require(paths["target_id"].is_unique, "path targets repeat")
    require(not paths["path_status"].eq("cycle_detected").any(), "cycle detected")
    require(
        set(paths["target_id"]) == set(occurrences["target_id"]),
        "path/occurrence target sets differ",
    )
    terminal_steps = path_steps[path_steps["step_from_terminal"].eq(0)]
    require(
        terminal_steps["terminal_target_id"].nunique() == len(paths),
        "each path must have a terminal step",
    )
    require(
        int(invariance["targets_with_conflict"].sum()) == 0,
        "structural fields vary within target_id",
    )
    require(
        len(preferred)
        == int(denominators.loc["preferred_target_year_rows", "count"]),
        "preferred panel count mismatch",
    )
    key = preferred[["target_id", "fiscal_year"]].fillna("<MISSING>")
    require(not key.duplicated().any(), "preferred target-year key repeats")
    require(
        preferred.loc[preferred["balance_ready"].astype(bool), "accounting_identity_ok"]
        .eq(1)
        .all(),
        "ready rows fail upstream accounting identity flag",
    )
    require(
        int(paths["path_status"].eq("complete_to_ultimate_parent").sum())
        == expected["complete_paths"],
        "complete path count mismatch",
    )

    figure_count = 0
    for figure in sorted((output / "figures").glob("*.png")):
        with Image.open(figure) as image:
            require(image.width >= 1000 and image.height >= 700, f"small figure: {figure}")
            image.verify()
        figure_count += 1
    require(figure_count >= 6, "expected at least six figures")

    return {
        "targets": len(occurrences),
        "group_entities": len(group_entities),
        "global_entities": len(global_entities),
        "paths": len(paths),
        "preferred_rows": len(preferred),
        "figures": figure_count,
    }


def compare_rebuild(output: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="codex-research-rebuild-") as temp:
        rebuilt = Path(temp) / "outputs"
        subprocess.run(
            [sys.executable, str(PIPELINE), "--output", str(rebuilt)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        original_files = {
            path.relative_to(output)
            for path in output.rglob("*.csv")
        } | {Path("key_metrics.json")}
        rebuilt_files = {
            path.relative_to(rebuilt)
            for path in rebuilt.rglob("*.csv")
        } | {Path("key_metrics.json")}
        require(original_files == rebuilt_files, "rebuild produced a different output-file set")
        mismatches = [
            relative
            for relative in sorted(original_files)
            if (output / relative).read_bytes() != (rebuilt / relative).read_bytes()
        ]
        require(not mismatches, f"non-deterministic rebuilt outputs: {mismatches}")
        validate(rebuilt)
        return len(original_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--rebuild", action="store_true", help="re-run pipeline in a temporary directory"
    )
    args = parser.parse_args()
    summary = validate(args.output)
    if args.rebuild:
        summary["byte_identical_rebuilt_csv_json_files"] = compare_rebuild(args.output)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
