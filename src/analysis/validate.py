#!/usr/bin/env python3
"""Independently rebuild and byte-check deterministic canonical outputs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .config import DICTIONARY_PATH, INPUT_PATH, OUTPUT_ROOT, ROOT
from .data_model import sha256_file
from .run_pipeline import build


def stable_outputs(root: Path) -> list[Path]:
    """Return outputs whose bytes should not contain run-time metadata.

    Figure PDFs are written without a creation timestamp, so every analytical
    output except the manifest itself is byte-comparable.
    """

    files = sorted((root / "tables").glob("*"))
    files.extend(sorted((root / "figures").glob("*")))
    files.append(root / "metrics.json")
    return [path for path in files if path.is_file()]


def relative_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in stable_outputs(root)
    }


def main() -> int:
    if not OUTPUT_ROOT.is_dir():
        raise SystemExit(
            "canonical output is missing; run python -m src.analysis.run_pipeline --clean"
        )

    with tempfile.TemporaryDirectory(prefix="suspicious-co-validation-") as temp:
        temp_root = Path(temp)
        rebuilt_output = temp_root / "outputs/final"
        rebuilt_reports = temp_root / "reports"
        build(
            INPUT_PATH,
            DICTIONARY_PATH,
            rebuilt_output,
            rebuilt_reports,
            clean=True,
        )

        expected = relative_hashes(OUTPUT_ROOT)
        observed = relative_hashes(rebuilt_output)
        if expected != observed:
            missing = sorted(set(expected) - set(observed))
            extra = sorted(set(observed) - set(expected))
            changed = sorted(
                key
                for key in set(expected) & set(observed)
                if expected[key] != observed[key]
            )
            raise AssertionError(
                f"rebuild mismatch: missing={missing}, extra={extra}, changed={changed}"
            )

        for report in ("RESULTS.md", "REPLICATION.md"):
            canonical = ROOT / report
            rebuilt = rebuilt_reports / report
            if sha256_file(canonical) != sha256_file(rebuilt):
                raise AssertionError(f"generated report drifted: {report}")

        canonical_manifest = json.loads(
            (OUTPUT_ROOT / "manifest.json").read_text(encoding="utf-8")
        )
        rebuilt_manifest = json.loads(
            (rebuilt_output / "manifest.json").read_text(encoding="utf-8")
        )
        for key in ("input", "dictionary", "software", "central_metrics"):
            if canonical_manifest[key] != rebuilt_manifest[key]:
                raise AssertionError(f"manifest section drifted: {key}")

    print(
        "Validation passed: central invariants and "
        f"{len(expected)} deterministic outputs reproduced exactly."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
