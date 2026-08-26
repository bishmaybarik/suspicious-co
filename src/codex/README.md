# Codex blind-discovery pipeline

Run from the repository root:

```bash
python src/codex/research_pipeline.py
python src/codex/validate_outputs.py --rebuild
```

The pipeline reads, but never modifies, the two immutable inputs under
`~/.agent-inputs/suspicious-co/`. It writes only to `outputs/codex/` unless an
alternative `--output` is supplied.

## Counting definitions

- **Source row:** one candidate financial-statement source.
- **Preferred target-year:** the upstream-selected row within
  `target_id × fiscal_year`; blank fiscal year remains an explicit key.
- **Target occurrence:** one unique `target_id`, retaining the reported parent,
  level, immediate parent, country, stake, UIN, and sector.
- **Parent-scoped normalized entity:** ultimate parent + standardized country +
  punctuation/spacing-insensitive entity name. Legal suffixes are deliberately
  retained.
- **Global normalized entity:** standardized country + the same conservative
  normalized name, ignoring ultimate-parent bucket. This collapses apparent
  joint exposures and therefore is not interchangeable with parent exposure.
- **Logical edge:** a distinct parent-node to parent-scoped-entity relation.
- **Ownership path:** recursive immediate-parent linkage for one target. Paths
  that encounter an absent parent are retained and flagged as truncated.

Name normalization is intentionally conservative. Fuzzy matches are output for
manual review and never automatically merged. Raw and standardized country
labels are both retained.

## Financial gates

- `balance_ready`: upstream `ready_for_valuation == 1`.
- `balance_basic_plausible`: ready, positive assets, nonnegative liabilities,
  and finite liabilities/assets.
- `balance_ratio_sensitivity`: basic-plausible plus leverage in `[0, 10]`.
- `pl_valid`: basic-plausible, upstream `pl_identity_ok == 1`, nonmissing PAT,
  and finite PAT/assets.
- `pl_ratio_sensitivity`: P&L-valid plus PAT/assets in `[-2, 2]`.

Absolute financial amounts are not pooled across rows because currencies differ
and reporting units are usually missing. Ratio and sign analyses retain exact
sample definitions in the output tables.

## Output layout

- `outputs/codex/data/`: reusable entity, edge, path, parent-jurisdiction,
  parent-level, and preferred financial tables.
- `outputs/codex/tables/`: audits, empirical summaries, denominator checks,
  leave-one-parent-out results, and anomaly review lists.
- `outputs/codex/figures/`: generated visualizations.
- `outputs/codex/manifest.json`: input hashes, package versions, variable labels,
  and headline metrics.

`validate_outputs.py --rebuild` reconstructs all outputs in a temporary
directory, checks hierarchy invariants, and requires every CSV plus
`key_metrics.json` to be byte-identical to the checked outputs.
