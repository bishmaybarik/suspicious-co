"""Write reproducible tables, number macros, and narrative handoff files."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .config import ROOT
from .data_model import sha256_file
from .statistics import FinalResults


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "≥": r"$\geq$",
        "≤": r"$\leq$",
        "×": r"$\times$",
        "→": r"$\rightarrow$",
    }
    return "".join(replacements.get(character, character) for character in text)


def human_number(value: Any, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "--"
    if isinstance(value, (np.integer, int)):
        return f"{int(value):,}"
    if isinstance(value, (np.floating, float)):
        if float(value).is_integer() and abs(value) >= 100:
            return f"{int(value):,}"
        return f"{float(value):,.{decimals}f}"
    return str(value)


def write_frame(frame: pd.DataFrame, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(stem.with_suffix(".csv"), index=False, float_format="%.10g")
    stem.with_suffix(".md").write_text(
        frame.to_markdown(index=False, floatfmt=".3f") + "\n",
        encoding="utf-8",
    )
    latex = frame.copy()
    for column in latex.select_dtypes(include="object").columns:
        latex[column] = latex[column].map(
            lambda value: "" if pd.isna(value) else str(value)
        )
    stem.with_suffix(".tex").write_text(
        latex.to_latex(
            index=False,
            escape=True,
            na_rep="--",
            float_format=lambda value: f"{value:.3f}",
        ),
        encoding="utf-8",
    )


def tabular(
    headers: Iterable[str],
    rows: Iterable[Iterable[Any]],
    align: str,
    decimals: int = 1,
) -> str:
    lines = [f"\\begin{{tabular}}{{{align}}}", "\\toprule"]
    lines.append(" & ".join(latex_escape(header) for header in headers) + r" \\")
    lines.append("\\midrule")
    for row in rows:
        cells = []
        for value in row:
            if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
                cells.append(human_number(value, decimals))
            else:
                cells.append(latex_escape("--" if pd.isna(value) else value))
        lines.append(" & ".join(cells) + r" \\")
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def paper_tables(results: FinalResults, table_dir: Path) -> None:
    sample = results.tables["01_sample_construction"]
    sample_stages = [
        "Raw source rows",
        "Preferred target-year rows",
        "Structural target occurrences",
        "Parent-scoped normalized entity candidates",
        "Global normalized entity candidates",
        "UINs",
        "Observed level-0 targets",
        "Ultimate-parent buckets",
        "Complete observed paths",
    ]
    sample_view = sample.set_index("stage").loc[sample_stages].reset_index()
    (table_dir / "paper_01_denominators.tex").write_text(
        tabular(
            ["Analytical unit", "Count", "Definition"],
            sample_view[["stage", "count", "unit"]].itertuples(index=False, name=None),
            "lrl",
            0,
        ),
        encoding="utf-8",
    )

    parents = results.tables["02_parent_architecture"].set_index("parent_short")
    selected = parents.loc[
        [
            "Motherson",
            "Wipro",
            "Reliance Industries",
            "Hindalco",
            "Tata Communications",
            "ONGC Videsh",
        ]
    ].reset_index()
    parent_rows = []
    for row in selected.itertuples(index=False):
        parent_rows.append(
            (
                row.parent_short,
                row.raw_source_rows,
                row.normalized_entities,
                row.jurisdictions,
                row.maximum_reported_level,
                row.maximum_reconstructed_level_complete,
                row.modal_uin_target_pct,
                row.complete_path_pct,
            )
        )
    (table_dir / "paper_02_parent_examples.tex").write_text(
        tabular(
            ["Parent bucket", "Raw rows", "Entities", "Countries", "Reported max", "Graph max", "Modal UIN (%)", "Complete paths (%)"],
            parent_rows,
            "lrrrrrrr",
        ),
        encoding="utf-8",
    )

    gateways = results.tables["04_gateway_amplification"].set_index("gateway_country")
    gateway_focus = [
        "NETHERLANDS",
        "MAURITIUS",
        "UNITED STATES OF AMERICA",
        "SINGAPORE",
        "UNITED ARAB EMIRATES",
    ]
    gateway_rows = []
    for country in gateway_focus:
        row = gateways.loc[country]
        gateway_rows.append(
            (
                country.title().replace(" Of America", ""),
                row["gateways"],
                row["parents"],
                row["mean_descendants"],
                row["median_descendants"],
                row["parent_equal_mean_descendants"],
                f"{row['loo_min_mean_descendants']:.1f} to {row['loo_max_mean_descendants']:.1f}",
            )
        )
    (table_dir / "paper_03_gateway_amplification.tex").write_text(
        tabular(
            ["Gateway jurisdiction", "Gateways", "Parents", "Mean", "Median", "Parent-equal mean", "LOO mean range"],
            gateway_rows,
            "lrrrrrr",
        ),
        encoding="utf-8",
    )

    roles = results.tables["05_jurisdiction_roles"].set_index("jurisdiction")
    role_focus = [
        "UNITED STATES OF AMERICA",
        "NETHERLANDS",
        "MAURITIUS",
        "UNITED KINGDOM",
        "SINGAPORE",
    ]
    role_rows = []
    for country in role_focus:
        row = roles.loc[country]
        role_rows.append(
            (
                country.title().replace(" Of America", ""),
                row["resident_entities"],
                row["unique_observed_intermediaries"],
                row["target_paths_below"],
                row["pooled_target_path_pct"],
                row["equal_parent_target_path_pct"],
                row["parents_affected"],
            )
        )
    (table_dir / "paper_04_jurisdiction_roles.tex").write_text(
        tabular(
            ["Jurisdiction", "Residents", "Intermediaries", "Paths below", "Pooled (%)", "Parent-equal (%)", "Parents"],
            role_rows,
            "lrrrrrr",
        ),
        encoding="utf-8",
    )

    robustness = results.tables["11_robustness_matrix"]
    robust_focus = [
        "Cross-border nonroot edges",
        "Modal UIN channel",
        "Largest observed subtree",
        "Dutch gateway amplification",
        "Netherlands strictly upstream",
        "Netherlands + US + Mauritius upstream",
        "Reported depth 5+",
        "Full-ownership depth gap",
        "Financial-ready deep gap",
    ]
    robust_view = robustness.set_index("estimand").loc[robust_focus].reset_index()
    robust_rows = []
    for row in robust_view.itertuples(index=False):
        robust_rows.append(
            (
                row.estimand,
                row.unit,
                row.pooled_or_primary,
                row.equal_parent_or_fe,
                (
                    "--"
                    if pd.isna(row.loo_min)
                    else f"{row.loo_min:.1f} to {row.loo_max:.1f}"
                ),
                row.alternative,
                row.alternative_definition,
            )
        )
    (table_dir / "paper_05_robustness.tex").write_text(
        tabular(
            ["Estimand", "Unit", "Primary", "Parent-equal/FE", "LOO range", "Alternative", "Definition"],
            robust_rows,
            "llrrrrl",
        ),
        encoding="utf-8",
    )

    financial = results.tables["10_financial_data_audit"].set_index("statistic")
    financial_focus = [
        "Targets with any source",
        "Targets with parsed balance sheet",
        "Targets ready at least once",
        "Ready rows",
        "Sign-plausible ready rows",
        "P&L-valid rows",
        "Ready rows with blank units",
        "Demonstrated same-URL/different-name reuse clusters",
        "Ready rows unflagged by broad duplicate/sign screen",
    ]
    financial_rows = []
    for statistic in financial_focus:
        row = financial.loc[statistic]
        financial_rows.append(
            (statistic, row["numerator"], row["denominator"], row["value"], row["unit"])
        )
    (table_dir / "paper_06_financial_audit.tex").write_text(
        tabular(
            ["Gate or diagnostic", "Numerator", "Denominator", "Value", "Unit"],
            financial_rows,
            "lrrrl",
        ),
        encoding="utf-8",
    )

    depth = results.tables["08_depth_audit"].set_index("statistic")
    depth_focus = [
        "Reported level 2+",
        "Reported level 5+",
        "Reported level 5+, equal-parent",
        "Reconstructed distance 5+",
        "Reported/reconstructed mismatch",
        "Motherson share of mismatches",
        "Manufacturing targets at reported level 5+",
        "Motherson + Hindalco share of deep manufacturing",
    ]
    depth_rows = []
    for statistic in depth_focus:
        row = depth.loc[statistic]
        depth_rows.append(
            (statistic, row["numerator"], row["denominator"], row["value_pct"], row["unit"])
        )
    (table_dir / "paper_A1_depth_audit.tex").write_text(
        tabular(
            ["Depth diagnostic", "Numerator", "Denominator", "Value (%)", "Unit"],
            depth_rows,
            "lrrrl",
        ),
        encoding="utf-8",
    )

    ownership = results.tables["09_ownership_data_audit"]
    (table_dir / "paper_A2_ownership_audit.tex").write_text(
        tabular(
            ["Ownership diagnostic", "Numerator", "Denominator", "Value", "Unit"],
            ownership.itertuples(index=False, name=None),
            "lrrrl",
        ),
        encoding="utf-8",
    )

    evidence = results.tables["14_evidence_classification"]
    (table_dir / "paper_A3_evidence_classification.tex").write_text(
        tabular(
            ["Class", "Result", "Disposition"],
            evidence.itertuples(index=False, name=None),
            r"lp{0.28\textwidth}p{0.52\textwidth}",
        ),
        encoding="utf-8",
    )


def latex_macros(metrics: dict[str, Any]) -> str:
    mappings: list[tuple[str, str, int | None]] = [
        ("RawRows", "source_rows", 0),
        ("PreferredRows", "preferred_target_year_rows", 0),
        ("Targets", "target_occurrences", 0),
        ("ParentEntities", "parent_scoped_normalized_entities", 0),
        ("GlobalEntities", "global_normalized_entities", 0),
        ("UINs", "uins", 0),
        ("ObservedRoots", "observed_level0_targets", 0),
        ("Parents", "ultimate_parent_buckets", 0),
        ("Jurisdictions", "jurisdiction_labels", 0),
        ("NonrootEdges", "nonroot_edges", 0),
        ("ExpectedLinks", "expected_prior_level_links", 0),
        ("OtherLevelLinks", "observed_other_level_links", 0),
        ("CompletePaths", "complete_paths", 0),
        ("CompletePathPct", "complete_path_pct", 1),
        ("MissingParentEdges", "missing_parent_edges", 0),
        ("MissingParentNodes", "normalized_missing_parent_nodes", 0),
        ("CrossBorderEdges", "cross_border_edges", 0),
        ("CrossBorderPct", "cross_border_pooled_pct", 1),
        ("CrossBorderEqualPct", "cross_border_equal_parent_pct", 1),
        ("CrossBorderLooLow", "cross_border_loo_min_pct", 1),
        ("CrossBorderLooHigh", "cross_border_loo_max_pct", 1),
        ("ModalUinPct", "modal_uin_pooled_pct", 1),
        ("ModalUinCount", "modal_uin_target_count", 0),
        ("ModalUinEqualPct", "modal_uin_equal_parent_pct", 1),
        ("ModalUinMedianPct", "modal_uin_median_parent_pct", 1),
        ("ObservedSubtreeMedian", "largest_observed_subtree_median_pct", 1),
        ("NamedNodeSubtreeMedian", "named_node_inclusive_subtree_median_pct", 1),
        ("DagDominatorMedian", "strict_dag_dominator_median_pct", 1),
        ("ConcentrationParents", "concentration_parent_count", 0),
        ("ObservedIntermediaries", "observed_intermediary_nodes", 0),
        ("DutchGatewayMean", "netherlands_gateway_mean", 1),
        ("DutchGatewayMedian", "netherlands_gateway_median", 1),
        ("DutchGatewayEqualMean", "netherlands_gateway_equal_parent_mean", 1),
        ("DutchGatewayLooLow", "netherlands_gateway_loo_min", 1),
        ("DutchGatewayLooHigh", "netherlands_gateway_loo_max", 1),
        ("DutchGatewayRobustMean", "netherlands_gateway_robust_subset_mean", 1),
        ("DutchUpstreamPct", "netherlands_upstream_pooled_pct", 1),
        ("DutchUpstreamEqualPct", "netherlands_upstream_equal_parent_pct", 1),
        ("TopThreeCount", "top_three_upstream_count", 0),
        ("TopThreePct", "top_three_upstream_pooled_pct", 1),
        ("TopThreeEqualPct", "top_three_upstream_equal_parent_pct", 1),
        ("TopThreeNoFundsPct", "top_three_excluding_funds_pct", 1),
        ("DeclaredCentrePct", "declared_centre_upstream_pooled_pct", 1),
        ("DeclaredCentreEqualPct", "declared_centre_upstream_equal_parent_pct", 1),
        ("DeclaredCentreNodePct", "declared_centre_unique_observed_node_pct", 1),
        ("SourceTargets", "targets_with_source", 0),
        ("ParsedTargets", "targets_balance_parsed", 0),
        ("ReadyRows", "ready_target_year_rows", 0),
        ("SignPlausibleRows", "sign_plausible_ready_rows", 0),
        ("PlValidRows", "pl_valid_rows", 0),
        ("ReadyTargets", "valuation_ready_targets", 0),
        ("ParentsNoReady", "financial_parents_with_zero_ready", 0),
        ("RepeatedClusters", "repeated_signatures", 0),
        ("RepeatedRows", "repeated_rows", 0),
        ("ReadyRepeatedRows", "ready_repeated_rows", 0),
        ("EvidenceReuseClusters", "proven_reuse_clusters", 0),
        ("BroadUnflaggedRows", "broad_unflagged_ready_rows", 0),
        ("MissingUnitsReady", "missing_units_ready_rows", 0),
        ("DepthTwoPlusCount", "reported_level2plus_count", 0),
        ("DepthTwoPlusPct", "reported_level2plus_pct", 1),
        ("DepthFivePlusCount", "reported_level5plus_count", 0),
        ("DepthFivePlusPct", "reported_level5plus_pct", 1),
        ("DepthFiveEqualPct", "reported_level5plus_equal_parent_pct", 1),
        ("GraphDepthFivePct", "reconstructed_level5plus_pct", 1),
        ("DepthMismatchCount", "depth_mismatch_count", 0),
        ("DepthMismatchPct", "depth_mismatch_pct", 1),
        ("MothersonMismatchShare", "motherson_mismatch_share_pct", 1),
        ("DeepManufacturing", "deep_manufacturing_count", 0),
        ("ManufacturingTargets", "manufacturing_target_count", 0),
        ("DeepManufacturingTopTwo", "deep_manufacturing_top_two_count", 0),
        ("DeepManufacturingTopTwoPct", "deep_manufacturing_top_two_pct", 1),
        ("ZeroStakeCount", "zero_nonroot_stakes", 0),
        ("ZeroStakePct", "zero_nonroot_stake_pct", 1),
        ("OwnershipPooledGap", "ownership_pooled_gap_pp", 1),
        ("OwnershipEqualGap", "ownership_equal_parent_gap_pp", 1),
        ("OwnershipNoRelianceGap", "ownership_exclude_reliance_gap_pp", 1),
        ("OwnershipLevelOne", "ownership_level1_full_pct", 1),
        ("OwnershipLevelTwoPlus", "ownership_level2plus_full_pct", 1),
        ("FinancialRawDepthGap", "financial_raw_depth_gap_pp", 1),
        ("FinancialFeDepthGap", "financial_parent_fe_depth_gap_pp", 1),
        ("FinancialLooLow", "financial_parent_fe_loo_min_pp", 1),
        ("FinancialLooHigh", "financial_parent_fe_loo_max_pp", 1),
        ("HoldingNameCount", "name_holding_name_entities", 0),
        ("HoldingNameHolderPct", "name_holding_name_holder_pct", 1),
        ("OtherNameHolderPct", "name_other_name_holder_pct", 1),
        ("HoldingNameFeGap", "name_parent_country_fe_gap_pp", 1),
        ("TataCommRawRows", "tata_communications_raw_rows", 0),
        ("TataCommEntities", "tata_communications_entities", 0),
        ("MothersonRawRows", "motherson_raw_rows", 0),
        ("MothersonEntities", "motherson_entities", 0),
    ]
    lines = ["% Generated by src/analysis/run_pipeline.py; do not edit."]
    for macro, key, decimals in mappings:
        if key not in metrics:
            raise KeyError(f"missing LaTeX metric: {key}")
        value = metrics[key]
        if decimals == 0:
            rendered = f"{int(round(value)):,}"
        else:
            rendered = f"{float(value):.{decimals}f}"
        lines.append(f"\\newcommand{{\\{macro}}}{{{rendered}\\xspace}}")
    return "\n".join(lines) + "\n"


def results_markdown(metrics: dict[str, Any]) -> str:
    return f"""# Canonical results

This document summarizes the first canonical, jointly adjudicated result set.
It describes the 28 parent buckets in the supplied dataset; it does not claim
population representativeness, causal effects, tax motives, illegality, or
current legal control.

## Analytical units

The {metrics['source_rows']:,} raw rows are source candidates, not firms. They
collapse to {metrics['preferred_target_year_rows']:,} preferred target-years,
{metrics['target_occurrences']:,} structural target occurrences,
{metrics['parent_scoped_normalized_entities']:,} parent-scoped normalized
entity candidates, and {metrics['global_normalized_entities']:,} global
normalized candidates. The structural mapping contains {metrics['uins']:,}
UINs, {metrics['observed_level0_targets']:,} observed level-0 targets, and
{metrics['ultimate_parent_buckets']:,} parent buckets.

## Defensible core results

1. **Denominators are first order.** Source-panel length reverses parent
   rankings; firm and jurisdiction results use target/entity and parent-balanced
   denominators, never raw rows.
2. **Parent architectures are multidimensional.** Size, geographic breadth,
   reported depth, observed graph distance, branching, stake structure, and
   channel concentration do not collapse to one defensible complexity score.
3. **Dominant channels and large subtrees are common.** The modal UIN contains
   {metrics['modal_uin_pooled_pct']:.1f}% of targets pooled and
   {metrics['modal_uin_equal_parent_pct']:.1f}% under equal-parent weighting.
   Among 24 groups with at least 15 targets, the median largest observed
   subtree contains {metrics['largest_observed_subtree_median_pct']:.1f}% of
   normalized entities below its top node. The median is
   {metrics['strict_dag_dominator_median_pct']:.1f}% under a strict DAG
   dominator sensitivity and {metrics['named_node_inclusive_subtree_median_pct']:.1f}%
   when named-but-unscraped parents are admitted as nodes. These are mapping and
   observed-topology estimands, not verified legal chokepoints.
4. **Gateway jurisdictions occupy different network roles.** Dutch observed
   level-0 gateways have a mean of {metrics['netherlands_gateway_mean']:.1f}
   and median of {metrics['netherlands_gateway_median']:.1f} downstream
   normalized entities, compared with a parent-equal mean of
   {metrics['netherlands_gateway_equal_parent_mean']:.1f}. The Netherlands is
   strictly upstream of {metrics['netherlands_upstream_pooled_pct']:.1f}% of
   target paths, but {metrics['netherlands_upstream_equal_parent_pct']:.1f}%
   under equal-parent weighting.
5. **A majority of nonroot edges cross jurisdictions.** The standardized-label
   estimate is {metrics['cross_border_pooled_pct']:.1f}%, the equal-parent
   estimate is {metrics['cross_border_equal_parent_pct']:.1f}%, and the
   leave-one-parent-out range is {metrics['cross_border_loo_min_pct']:.1f}–
   {metrics['cross_border_loo_max_pct']:.1f}%.
6. **Depth is definition- and parent-sensitive.** Reported level 5+ contains
   {metrics['reported_level5plus_count']:,} targets
   ({metrics['reported_level5plus_pct']:.1f}%), but the equal-parent mean is
   {metrics['reported_level5plus_equal_parent_pct']:.1f}% and reconstructed
   distance 5+ is {metrics['reconstructed_level5plus_pct']:.1f}% of complete
   paths. Reported and reconstructed depth disagree for
   {metrics['depth_mismatch_count']:,} complete paths
   ({metrics['depth_mismatch_pct']:.1f}%); Motherson supplies
   {metrics['motherson_mismatch_share_pct']:.1f}% of those mismatches.

## Supporting and negative results

- The Netherlands, United States, and Mauritius are strictly upstream of
  {int(metrics['top_three_upstream_count']):,}/{metrics['target_occurrences']:,}
  target paths ({metrics['top_three_upstream_pooled_pct']:.1f}%), but the
  equal-parent union is only {metrics['top_three_upstream_equal_parent_pct']:.1f}%.
  This is a descendant-weighted descriptive exposure, not a counterfactual
  detachment estimate.
- {metrics['zero_nonroot_stakes']:,} nonroot stakes are recorded as zero
  ({metrics['zero_nonroot_stake_pct']:.1f}%). Direct AOC comparisons contradict
  literal zero in every comparable zero case, so control-weighted claims are
  not defensible. The pooled full-ownership depth gap of
  {metrics['ownership_pooled_gap_pp']:.1f} points shrinks to
  {metrics['ownership_equal_parent_gap_pp']:.1f} points with equal-parent
  weighting and {metrics['ownership_exclude_reliance_gap_pp']:.1f} points when
  Reliance is excluded.
- Only {metrics['valuation_ready_targets']:,}/{metrics['target_occurrences']:,}
  targets are valuation-ready at least once. There are
  {metrics['proven_reuse_clusters']:,} demonstrated same-URL/different-name
  evidence-reuse clusters, and units are blank for
  {metrics['missing_units_ready_rows']:,}/{metrics['ready_target_year_rows']:,}
  ready rows. The financial layer supports a data-quality result, not financial
  performance inference.

## Excluded from the core narrative

The canonical study excludes sector-depth generalizations, financial-health
rankings, cumulative no-dilution claims, gateway-vintage or policy claims,
regional routing narratives, tiny-jurisdiction leverage rankings, and any tax,
legal, regulatory, misconduct, or intent interpretation. The full disposition
is generated in `outputs/final/tables/14_evidence_classification.*`.
"""


def replication_markdown(
    input_path: Path,
    dictionary_path: Path,
    metrics: dict[str, Any],
) -> str:
    return f"""# Replication

## Inputs

The pipeline reads the immutable files below and never writes to them:

- `{input_path}`
  - SHA-256: `{sha256_file(input_path)}`
- `{dictionary_path}`
  - SHA-256: `{sha256_file(dictionary_path)}`

The dataset contains {metrics['source_rows']:,} rows and 77 variables. See the
supplied dictionary and `RESEARCH_PROTOCOL.md` for source semantics.

## One-command build

From the repository root:

```bash
python -m src.analysis.run_pipeline --clean
python -m src.analysis.validate
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=paper paper/main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=paper paper/main.tex
```

The first command reconstructs all units, entities, edges, paths, tables,
figures, `RESULTS.md`, `REPLICATION.md`, and the generated LaTeX number macros.
The second command rebuilds into a temporary directory and checks hashes and
central invariants. The two LaTeX passes compile cross-references.

## Canonical definitions

- **Raw source row:** one candidate filing/source observation; never a firm.
- **Preferred target-year:** the row with `preferred_for_target_year == 1`
  within `target_id × fiscal_year`, retaining blank year as a key.
- **Structural target occurrence:** one `target_id`; the primary path/exposure
  unit ({metrics['target_occurrences']:,}).
- **Parent-scoped normalized entity candidate:** parent plus standardized
  country plus punctuation/spacing-normalized name
  ({metrics['parent_scoped_normalized_entities']:,}).
- **Global normalized entity candidate:** the same name-country key with parent
  ignored ({metrics['global_normalized_entities']:,}). This is not a verified
  legal-entity identifier.
- **Nonroot edge:** one reported immediate-parent relation for a target below
  level 0 ({metrics['nonroot_edges']:,}).
- **Complete observed path:** recursion reaches the Indian parent through
  observed entity nodes ({metrics['complete_paths']:,}). Named missing parents
  retain their supplied countries but do not make paths complete.
- **Equal-parent estimate:** compute the within-parent statistic first, then
  average across the 28 parent buckets. Leave-one-parent-out estimates repeat
  the pooled or fixed-effect estimand after dropping each parent.

## Hierarchy rules

Parent linkage forms candidates within a parent bucket using conservative
punctuation/spacing name aliases, then ranks them lexicographically by expected
preceding level, supplied country, exact name, and UIN. No fuzzy match is
accepted in the canonical build. Named-but-unscraped parents
remain explicit unresolved nodes: {metrics['normalized_missing_parent_nodes']:,}
normalized names on {metrics['missing_parent_edges']:,} child edges. Their
reported countries are preserved. Reported `level` and reconstructed graph
distance are stored and reported separately.

## Missingness and exclusions

Recorded `stake == 0` is treated as unknown, not zero economic ownership.
Absolute financial amounts are not pooled because currencies differ and units
are blank for {metrics['missing_units_ready_rows']:,} of
{metrics['ready_target_year_rows']:,} ready rows. Financial tables report
source/parse/readiness attrition, sign checks, P&L validity, and duplicate
evidence; they do not estimate population performance.

## Output map

- `outputs/final/tables/`: every final table in CSV, Markdown, and LaTeX, plus
  paper-specific LaTeX views and generated number macros.
- `outputs/final/figures/`: every final figure in PNG and PDF.
- `outputs/final/metrics.json`: machine-readable central estimates.
- `outputs/final/manifest.json`: input and output hashes plus software versions.
- `paper/main.pdf`: compiled paper.

All generated output is deterministic apart from PDF metadata written by the
TeX engine; validation hashes the analysis outputs, not LaTeX build auxiliaries.
"""


def write_outputs(
    results: FinalResults,
    table_dir: Path,
    input_path: Path,
    dictionary_path: Path,
    report_root: Path = ROOT,
) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in results.tables.items():
        write_frame(frame, table_dir / name)
    paper_tables(results, table_dir)
    (table_dir / "numbers.tex").write_text(
        latex_macros(results.metrics), encoding="utf-8"
    )
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "RESULTS.md").write_text(
        results_markdown(results.metrics), encoding="utf-8"
    )
    (report_root / "REPLICATION.md").write_text(
        replication_markdown(input_path, dictionary_path, results.metrics),
        encoding="utf-8",
    )
    (table_dir.parent / "metrics.json").write_text(
        json.dumps(results.metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
