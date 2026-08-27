# Replication

## Inputs

The pipeline reads the immutable files below and never writes to them:

- `/Users/bishmaybarik/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta`
  - SHA-256: `65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea`
- `/Users/bishmaybarik/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined_data_dictionary.txt`
  - SHA-256: `4f3285c0bb55e3578a73686d0fb27f9110b0d1c6e0a4000b2ff357aa8e35ac05`

The dataset contains 3,742 rows and 77 variables. See the
supplied dictionary and `RESEARCH_PROTOCOL.md` for source semantics.

## One-command build

From the repository root:

```bash
python -m src.analysis.run_pipeline --clean
python -m src.analysis.validate
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=paper paper/main.tex
done
```

The first command reconstructs all units, entities, edges, paths, tables,
figures, `RESULTS.md`, `REPLICATION.md`, and the generated LaTeX number macros.
The second command rebuilds into a temporary directory and checks hashes and
central invariants. Three LaTeX passes are required: the third resolves the
table and figure numbers cited in the text, and the build is warning-free.

## Canonical definitions

- **Raw source row:** one candidate filing/source observation; never a firm.
- **Preferred target-year:** the row with `preferred_for_target_year == 1`
  within `target_id × fiscal_year`, retaining blank year as a key.
- **Structural target occurrence:** one `target_id`; the primary path/exposure
  unit (1,834).
- **Parent-scoped normalized entity candidate:** parent plus standardized
  country plus punctuation/spacing-normalized name
  (1,830).
- **Global normalized entity candidate:** the same name-country key with parent
  ignored (1,818). This is not a verified
  legal-entity identifier.
- **Nonroot edge:** one reported immediate-parent relation for a target below
  level 0 (1,650).
- **Complete observed path:** recursion reaches the Indian parent through
  observed entity nodes (1,687). Named missing parents
  retain their supplied countries but do not make paths complete.
- **Equal-parent estimate:** compute the within-parent statistic first, then
  average across the 28 parent buckets. Leave-one-parent-out estimates repeat
  the pooled or fixed-effect estimand after dropping each parent.

## Hierarchy rules

Parent linkage forms candidates within a parent bucket using conservative
punctuation/spacing name aliases, then ranks them lexicographically by expected
preceding level, supplied country, exact name, and UIN. No fuzzy match is
accepted in the canonical build. Named-but-unscraped parents
remain explicit unresolved nodes: 18
normalized names on 78 child edges. Their
reported countries are preserved. Reported `level` and reconstructed graph
distance are stored and reported separately.

## Missingness and exclusions

Recorded `stake == 0` is treated as unknown, not zero economic ownership.
Absolute financial amounts are not pooled because currencies differ and units
are blank for 516 of
560 ready rows. Financial tables report
source/parse/readiness attrition, sign checks, P&L validity, and duplicate
evidence; they do not estimate population performance.

## Output map

- `outputs/final/tables/`: every final table in CSV, Markdown, and LaTeX, plus
  paper-specific LaTeX views and generated number macros.
- `outputs/final/figures/`: every final figure in PNG and PDF.
- `outputs/final/metrics.json`: machine-readable central estimates.
- `outputs/final/manifest.json`: input and output hashes plus software versions.
- `paper/main.pdf`: compiled paper.

Every generated analysis output is byte-reproducible, including figure PDFs,
which are written without a creation timestamp. Validation hashes those outputs;
it does not hash LaTeX build auxiliaries or `paper/main.pdf`, whose bytes carry
TeX-engine metadata.
