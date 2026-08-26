# Codex research state

## Status

Blind discovery and the first authorized cross-agent review increment are
complete as of 2026-08-26. No commit, push, merge, cherry-pick, checkout,
rebase, reset, or history rewrite was performed.

The previous state recorded no cross-agent review. The common fork was
`29109a3384ba0f3471a2b677f04295a51d8aadaa`. Git history showed one new commit
on `origin/agent/claude`, which was reviewed in this increment:

- `5ab6cb5944ad6fe8193f03b71f7a918ac4d24076`

The review is in `research/reviews/CLAUDE_5ab6cb5_REVIEW.md`. The replication
script reads no Claude-generated file and reconstructs every reviewed statistic
from the research input and the independently built Codex hierarchy.

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
- Created 17 blind-discovery findings plus two independently developed
  post-review findings and a follow-up research agenda.
- Inspected and classified seven claims/subclaims from the one new Claude
  commit; reproduced them with unique-entity, path, parent-weighted,
  leave-one-parent-out, missingness, and hierarchy-mechanics checks.
- Generated seven blind-discovery and two post-review inspected visualizations,
  plus extensive reusable CSV tables.

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

## Cross-agent review results

- **CONFIRMED:** C-F002 gateway amplification; C-F017 reported-level/graph-
  distance mismatch concentrated in Motherson.
- **PARTIALLY CONFIRMED:** C-F001 UIN multiplier as written; C-F003 fixed-list
  conduit exposure; C-F014 group-versus-depth financial coverage.
- **INTERESTING BUT NEEDS EXTERNAL VALIDATION:** C-F008 gateway vintage shift;
  C-F009 semantic decoding of UIN substrings.

Key replicated/corrected quantities:

- Dutch level-0 gateways have 34.85 descendants on average (median 12.0),
  equal-parent mean 37.08, and leave-one-parent-out minimum 21.25. The
  no-majority-child-branch restriction gives mean 37.75.
- Fixed-list upstream-centre exposure is 1,134/1,834 (61.83%), 57.17% under
  equal-parent weighting, and 57.77–67.89% leave-one-parent-out. Counting each
  upstream node once gives 37.97%, exposing the descendant-weighting mechanic.
- All 78 edges to an unscraped immediate parent retain a reported parent
  country. Preserving it moves Dr Reddy's fixed-list exposure to 37/41 (90.24%);
  treating these countries as unknown caused the other branch's 7.3% result.
- Mauritius supplies 11/55 pre-2011 observed gateways versus 4/99 from 2016
  onward (two-sided Fisher p = 0.0030; LOO change -19.37 to -13.44 pp). The UIN
  substring's interpretation as registration year still needs external proof.
- Financial readiness is 265/1,834 (14.45%). The proper parent fixed-effect
  depth coefficient is -2.42 pp, with leave-one-parent-out range -6.62 to -0.77
  pp, rather than the reviewed analysis's -0.9 pp conditional demeaned mean.
- Complete-path depth mismatch is 236/1,687 (13.99%); Motherson contributes
  208/236 (88.14%).

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
8. The largest UIN within each parent carries 59.71% of all targets (62.05%
   equal-parent; 57.18–62.75% LOO). Among 14 groups in at least 20 destination
   jurisdictions, the equal-parent share is 71.23%.
9. A 26.41 pp pooled level-1 versus level-2+ full-ownership gradient shrinks to
   2.33 pp with equal-parent weighting and 6.10 pp after excluding Reliance; it
   is principally group/portfolio composition.

See `FINDINGS.md` for full numerators, denominators, robustness, mundane/data-
quality explanations, falsification tests, and rankings.

## Code and outputs

- Main pipeline: `src/codex/research_pipeline.py`
- Cross-agent replication and independent extension:
  `src/codex/review_increment.py`
- Validation: `src/codex/validate_outputs.py`
- Usage: `src/codex/README.md`
- Data audit: `research/codex/DATA_AUDIT.md`
- Findings: `research/codex/FINDINGS.md`
- Research ideas: `research/codex/IDEAS.md`
- Cross-agent review: `research/reviews/CLAUDE_5ab6cb5_REVIEW.md`
- Generated data/tables/figures: `outputs/codex/`
- Review outputs and hash manifest: `outputs/codex/review/`
- Input/software manifest: `outputs/codex/manifest.json`
- Machine-readable headline metrics: `outputs/codex/key_metrics.json`

## Reproducibility verification

Executed from repository root:

```bash
python src/codex/research_pipeline.py
python src/codex/review_increment.py
python src/codex/validate_outputs.py --rebuild
ruff check src/codex
python -m py_compile src/codex/research_pipeline.py \
  src/codex/review_increment.py src/codex/validate_outputs.py
```

Validation result:

- 1,834 target occurrences validated;
- 1,830 parent-scoped and 1,818 global entity rows validated;
- one edge occurrence and one path record per target validated;
- no graph cycles detected;
- 3,567 preferred target-year keys are unique;
- seven main and two review PNG figures pass size/integrity checks;
- 18 review tables and their reviewed-commit provenance validate;
- all 88 generated CSV/JSON files are byte-identical after an isolated
  temporary rebuild, including the review manifest's figure hashes;
- Ruff and Python compilation pass.

## Known limitations / next boundary

- There is no authoritative legal-entity identifier; normalized name-country
  keys are candidates.
- Seventy-eight immediate-parent edges refer to 18 normalized entities absent
  from the target table, truncating 147 descendant paths. Their reported
  countries are present and must not be discarded.
- Reported levels may count omitted nodes; observed graph distance is a lower
  bound.
- Stake zero is semantically unreliable and no cumulative-control measure is
  defensible yet.
- Units are missing for 516/560 ready rows; absolute financial aggregation is
  unsafe.
- Financial selection is severe and parent-dependent.
- Static hierarchy attributes cannot measure ownership restructuring over time.
- The UIN's fixed string format is internally clear, but substring meanings and
  the gateway-vintage interpretation need an external RBI specification.

The next highest-value increment is external/source validation of the UIN
format, missing parent identities, dated acquisitions, duplicate legal entities,
and ownership stakes before stronger econometric interpretation.
