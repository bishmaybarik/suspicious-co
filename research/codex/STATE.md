# Codex research state

## Status

Blind discovery is complete for the supplied subsidiary financial dataset as of
2026-08-26. No Claude branch, output, note, or finding was inspected. No commit,
push, merge, rebase, reset, or history rewrite was performed.

## Inputs

- `subsidiary_financial_variables_refined.dta`
  - SHA-256: `65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea`
- `subsidiary_financial_variables_refined_data_dictionary.txt`
  - SHA-256: `4f3285c0bb55e3578a73686d0fb27f9110b0d1c6e0a4000b2ff357aa8e35ac05`

Both inputs were treated as immutable and read-only.

## Completed work

- Read `AGENTS.md` and `RESEARCH_PROTOCOL.md` completely before substantive
  analysis.
- Established row semantics and every principal denominator.
- Audited all 77 variables, identifiers, missingness, duplicate structures,
  ownership fields, dates, sectors, country labels, and financial gates.
- Built conservative parent-scoped and global entity tables.
- Built target-level and logical parent-child edge tables.
- Recursively reconstructed complete/truncated ownership paths and long path
  steps without silently imputing absent parents.
- Built parent-jurisdiction and ultimate-parent analytical tables.
- Measured depth, branching, leaves, hubs, country composition, cross-border
  transitions, recurring motifs, intermediary use, and parent heterogeneity.
- Ran raw-row versus entity, parent-balanced, leave-one-parent-out, reported-
  versus-reconstructed depth, financial-sample, and sector-composition checks.
- Created 17 ranked candidate findings/directions and a follow-up research
  agenda.
- Generated seven inspected visualizations and extensive reusable CSV tables.

## Stable headline counts

- raw source rows: 3,742
- preferred target-year rows: 3,567
- structural target occurrences: 1,834
- parent-scoped normalized entity candidates: 1,830
- global normalized entity candidates: 1,818
- UINs: 186
- ultimate-parent buckets: 28
- complete paths to ultimate parent: 1,687 (91.98%)
- nonroot edges linked at expected level: 1,500/1,650 (90.91%)
- complete paths with reported/reconstructed depth mismatch: 236/1,687
  (13.99%)
- ready target-year balance sheets: 560/3,567 (15.70%)
- basic sign-plausible ready rows: 521
- P&L-valid rows: 105

## Strongest research conclusions

1. Raw source rows are invalid firm counts and substantially misweight parent
   exposure; Tata Communications is the clearest example.
2. Parent groups have distinct architectures—chain-heavy, hub-heavy,
   geographically diversified, or portfolio-heavy—so a single complexity
   measure is inadequate.
3. Netherlands and Mauritius appear far more often as ancestors/intermediaries
   than as unique resident entities; the result survives equal-parent weighting,
   although path branching is part of the estimand.
4. A majority of nonroot ownership edges are cross-border (57.64% pooled,
   58.67% equal-parent; leave-one-parent-out 56.06-61.78%).
5. Reported ownership depth is not graph distance. Deep-hierarchy and deep-
   manufacturing patterns are heavily driven by Motherson and Hindalco.
6. Zero mapping stakes are unsafe: seven rows with mapping stake zero have
   positive AOC-1 shareholding where both measures exist.
7. Financial coverage and quality are too selected for broad population claims;
   no robust financial-depth association was found.

See `FINDINGS.md` for full numerators, denominators, robustness, mundane/data-
quality explanations, falsification tests, and rankings.

## Code and outputs

- Main pipeline: `src/codex/research_pipeline.py`
- Validation: `src/codex/validate_outputs.py`
- Usage: `src/codex/README.md`
- Data audit: `research/codex/DATA_AUDIT.md`
- Findings: `research/codex/FINDINGS.md`
- Research ideas: `research/codex/IDEAS.md`
- Generated data/tables/figures: `outputs/codex/`
- Input/software manifest: `outputs/codex/manifest.json`
- Machine-readable headline metrics: `outputs/codex/key_metrics.json`

## Reproducibility verification

Executed from repository root:

```bash
python src/codex/research_pipeline.py
python src/codex/validate_outputs.py --rebuild
ruff check src/codex
python -m py_compile src/codex/research_pipeline.py src/codex/validate_outputs.py
```

Validation result:

- 1,834 target occurrences validated;
- 1,830 parent-scoped and 1,818 global entity rows validated;
- one edge occurrence and one path record per target validated;
- no graph cycles detected;
- 3,567 preferred target-year keys are unique;
- seven PNG figures pass size/integrity checks;
- all 68 generated CSV/`key_metrics.json` files are byte-identical after an
  isolated temporary rebuild;
- Ruff and Python compilation pass.

## Known limitations / next boundary

- There is no authoritative legal-entity identifier; normalized name-country
  keys are candidates.
- Seventy-eight immediate parents are absent, truncating 147 descendant paths.
- Reported levels may count omitted nodes; observed graph distance is a lower
  bound.
- Stake zero is semantically unreliable and no cumulative-control measure is
  defensible yet.
- Units are missing for 516/560 ready rows; absolute financial aggregation is
  unsafe.
- Financial selection is severe and parent-dependent.
- Static hierarchy attributes cannot measure ownership restructuring over time.

The next highest-value increment is external/source validation of missing
parents, duplicate legal entities, and ownership stakes before stronger
econometric interpretation.
