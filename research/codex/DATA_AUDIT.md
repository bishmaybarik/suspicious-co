# Data audit

## Scope and provenance

This blind-discovery audit uses only:

- `~/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta`
- `~/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined_data_dictionary.txt`

The files were read-only. SHA-256 hashes are recorded in
`outputs/codex/manifest.json`:

- Stata file: `65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea`
- dictionary: `4f3285c0bb55e3578a73686d0fb27f9110b0d1c6e0a4000b2ff357aa8e35ac05`

The Stata file has 3,742 rows and 77 variables. It is not a census of all legal
entities and it is not a transaction dataset. It is a source-candidate panel
built around foreign-entity targets from an upstream subsidiary mapping. Most
rows are candidate or selected subsidiary financial-statement PDFs; three
parent groups instead use parent annual-report AOC-1 fallback rows.

## What one row represents

One raw row is one observed financial-statement source candidate for a
`target_id × fiscal_year`. It is not necessarily a unique company, a unique
company-year, or a unique ownership relationship.

There are 3,567 `target_id × fiscal_year` keys when blank fiscal years are
retained as an explicit key. Exactly one row per key has
`preferred_for_target_year == 1`; 175 alternative candidates are nonpreferred.
Ninety-four keys have multiple candidates: 14 have two rows, 79 have three, and
one has four.

The hierarchy fields are invariant within each `target_id` across its source
rows. This makes a unique `target_id` the defensible structural *target
occurrence* unit. There are 1,834 such targets. Financial variables remain a
target-year panel; hierarchy variables are static target attributes repeated
over source rows/years and cannot reveal changes in ownership structure over
time.

## Identifier and denominator hierarchy

| Object | Count | Definition and caution |
|---|---:|---|
| Raw source rows | 3,742 | Candidate filing/source observations; strongly panel-weighted |
| Preferred target-years | 3,567 | One selected row per `target_id × fiscal_year`; 993 have blank year |
| Structural target occurrences | 1,834 | Unique `target_id`; preserves reported parent/path exposure |
| Parent-scoped exact names | 1,834 | Parent + raw country + exact name |
| Parent-scoped normalized entity candidates | 1,830 | Parent + standardized country + punctuation/spacing-normalized name |
| Global exact name-country candidates | 1,828 | Exact name-country with parent ignored |
| Global normalized entity candidates | 1,818 | Standardized country + conservative name key with parent ignored |
| UINs | 186 | RBI ODI identifier; demonstrably not a legal-entity key here |
| Ultimate-parent buckets | 28 | 25 PDF-scraped and 3 AOC-1 fallback groups |

The normalized entity key removes punctuation and spacing but retains legal
suffix words. This is deliberately conservative. The data do not contain an
authoritative global legal-entity identifier, so “unique entity” always means
“normalized name-country candidate,” not verified legal identity.

UIN is unusable as an entity count: the median UIN maps to two normalized group
entities, and `NDWAZ20010286` maps to 138 target occurrences. `target_id` is
stable for a scraping target but can retain aliases or repeated paths.

## Repeated entities and multiple paths

Conservative normalization finds 16 repeated global name-country clusters
covering 32 target occurrences:

- 12 clusters occur in multiple ultimate-parent buckets. Several have ownership
  stakes consistent with joint exposure, so collapsing them is suitable for a
  global-legal-entity denominator but wrong for parent exposure.
- Four clusters repeat within one parent bucket. Each has two reported parent
  nodes and therefore represents either multiple ownership paths, different
  versions, or a duplicate mapping requiring review.

Examples include shared oil/energy ventures across parent buckets and within-
parent aliases such as punctuation variants of a Netherlands entity. The exact
clusters are in `tables/entity_duplicate_clusters.csv`; the four consolidated
nodes with multiple reported parents are in
`tables/entities_with_multiple_parent_nodes.csv`.

An additional 61 high-string-similarity pairs are review candidates only. They
are not auto-collapsed because many close names are genuinely distinct numbered
or sibling entities. See `tables/fuzzy_entity_duplicate_candidates.csv`.

## Parent-child and path reconstruction

Each target supplies one reported edge:

`immediate_parent -> entity_name`

Level 0 is intended to be a foreign entity directly under the Indian parent;
the root is represented separately at graph level -1. Parent resolution uses,
in order, exact/normalized name, country, expected level, and UIN as a weak
tie-breaker. A high-threshold fuzzy rescue is allowed only when unique. No fuzzy
rescue was needed in the final build. Unobserved or ambiguous parents are kept
as explicit synthetic nodes; they are never silently replaced.

Among 1,650 nonroot edges:

- 1,500 (90.91%) link to an observed parent at the expected preceding level;
- 72 link to an observed named parent at another reported level;
- 78 name an immediate parent absent from the target table.

The last category is **identity-missing, not jurisdiction-missing**. All 78
edges retain a nonblank `immediate_parent_country`, spanning 18 normalized
parent names and nine reported countries. A synthetic or unresolved node should
therefore preserve that country while flagging the absent legal-entity record.
Replacing it with a generic unknown jurisdiction materially understates
ancestor exposure for Dr Reddy's and smaller groups.

Recursive traversal reaches the Indian parent for 1,687 of 1,834 targets
(91.98%). The other 147 paths are truncated because they or an ancestor hit one
of the 78 absent parent nodes. No cycles are produced.

Reported levels are not equivalent to graph distance. Among 1,687 complete
paths, 236 (13.99%) have a reported level different from the distance
reconstructable through observed links. All differences are negative
(`reconstructed - reported` ranges from -1 to -4), consistent with omitted or
level-skipping intermediates rather than extra graph nodes. This is concentrated:
208 of 309 Motherson paths differ. Motherson's maximum is 12 reported versus 8
reconstructable; Hindalco's is 12 versus 6, and only 38 of its 81 paths are
complete. Neither measure should be relabeled “correct depth”: reported level
may encode omitted nodes, while graph distance is a lower bound when nodes are
absent.

The reusable hierarchy products are:

- `data/entity_occurrences.csv`
- `data/unique_entities_parent_scoped.csv`
- `data/unique_entities_global.csv`
- `data/parent_child_edge_occurrences.csv`
- `data/parent_child_edges.csv`
- `data/ownership_paths.csv`
- `data/ownership_path_steps.csv`
- `data/parent_jurisdiction.csv`
- `data/ultimate_parent_analytical.csv`

## Jurisdiction variables

`entity_country` and `immediate_parent_country` are uppercase text labels. The
target table has 122 distinct child labels and 63 immediate-parent labels.
Raw labels are retained; a parallel standardized field corrects only obvious
spelling/format variants (for example, `VENEZULA` to `VENEZUELA`). Conceptually
ambiguous labels are not forced into countries:

- `IFSC GIFT CITY` is a special-zone label;
- `EUROPIAN UNION` is a misspelled supranational region;
- `CONGO` is jurisdictionally ambiguous;
- `CHANNEL ISLAND` is a broad regional label.

Although the dictionary describes foreign subsidiaries/entities, 10 targets
are labeled `INDIA`, nine `IFSC GIFT CITY`, and one `EUROPIAN UNION`. They are
retained and separately flagged. The 1,814 conventional foreign-jurisdiction
labels are 98.91% of targets.

Country shares are produced under four noninterchangeable denominators:

1. pooled parent-scoped entities;
2. global normalized entities;
3. equal-parent mean shares; and
4. appearances as ancestors in complete leaf/target paths.

## Ownership variables

`stake` is populated on all 1,650 nonroot edges and missing on all 184 level-0
targets. However, 406 nonroot stakes are exactly zero (24.61%). A zero stake is
not credible as a literal ownership relation without upstream clarification.
Among the 45 preferred rows where both mapping `stake` and AOC-1
`shareholding_percent` are present, seven have mapping stake zero but positive
shareholding (six at 100% and one at 73.94%). Eight of 45 differ by more than one
percentage point.

Consequently, cumulative ownership/control weights are not calculated. Positive
minority, majority, full, zero, and missing stakes are reported separately.

`shared_uin` equals one for 89 targets, but all retained rows have exactly one
top-30 claimant and use either `not_shared_uin` or
`sole_top30_claimant_shared_uin`. This does not prevent the same normalized
legal-entity candidate from appearing under different UINs/parents.

## Sector variables

There are 17 sector codes with matching labels. The largest are manufacturing
(508 targets), IT/software (283), professional/business services (261), finance
(166), pharmaceuticals/healthcare (145), and mining/extraction (140).

Sector is not invariant within UIN: many UINs contain several sectors. Sector
analyses therefore use entity targets, not UIN counts. Depth-sector associations
are audited with leave-one-parent-out checks because a sector can be repeated
through one parent's deep hierarchy.

Every UIN has a 13-character fixed format, positions 6–9 parse as a plausible
year, and the final four positions are digits. Those are internal string facts.
The supplied dictionary does not define the substrings, so labels such as
regional office, investment type, registration year, and serial remain inferred
until verified against an external RBI specification. Only 184 of 186 UINs have
an observed level-0 target in this file.

## Financial variables and comparability

The preferred panel contains 3,361 PDF rows and 206 AOC-1 rows. Quality tiers are
2,845 `full_pdf_review`, 516 `full_pdf_ready`, 162 `aoc1_review`, and 44
`aoc1_ready`.

Only 560 preferred target-years (15.70%) are `ready_for_valuation`; they cover
265 of 1,834 targets at least once (14.45%). Readiness is a balance-sheet gate,
not a general financial-quality guarantee.

Among the 560 ready rows:

- four have nonpositive assets (three negative);
- 38 have negative liabilities;
- 39 unique rows therefore fail the added basic sign-plausibility gate;
- 19 have liabilities/assets above 10;
- 129 have negative equity, which can be economically real but needs context;
- only 105 have a valid, testable P&L identity; 83 fail it and 372 are untestable.

The main analytical samples are explicitly gated:

- **balance ready:** upstream `ready_for_valuation == 1`, N = 560;
- **basic plausible:** ready, assets > 0, liabilities >= 0, finite leverage,
  N = 521;
- **balance-ratio sensitivity:** basic plausible and leverage in [0, 10],
  N = 503;
- **P&L valid:** basic plausible, `pl_identity_ok == 1`, PAT present, finite ROA,
  N = 105;
- **P&L-ratio sensitivity:** P&L valid and PAT/assets in [-2, 2], N = 104.

Currencies among ready rows are USD 298, INR 171, EUR 64, GBP 16, MXN 7, and
four single observations in other currencies. Units are blank for 516 of 560
ready rows (92.14%). Absolute amounts are therefore not pooled across currencies
or entities. Ratio analyses assume within-row fields use consistent units and
remain subject to evidence-line review.

Fifty-one repeated balance-sheet signatures involve 104 of 863 preferred parsed
rows. Final cross-review establishes an extraction-reuse mechanism for a
specific majority subset: 33 clusters combine one source URL with different
entity names, and all 33 reuse byte-identical assets, liabilities, and equity
evidence. Twenty-four different-name clusters that repeat within the ready
sample cover 49 ready rows. The remaining clusters can still include shared
ventures, aliases, or legitimate equal balances and are not automatically
errors. A broad repeated-signature/sign union flags 100/560 ready rows (460
remain unflagged); a narrower demonstrated-artifact/sign union flags 79 (481
remain). Neither count is a validated final financial sample. Evidence-bearing
anomalies are in `tables/financial_anomalies_for_review.csv`; the final audit is
in `final/duplicate_evidence_audit.csv`.

## Dates and temporal interpretation

Among 3,567 preferred rows:

- 993 (27.84%) have no fiscal year;
- 2,252 (63.13%) have no period-end date;
- 1,302 have both a parseable date and fiscal-year window;
- 70 of those 1,302 (5.38%) fall outside the April-to-March fiscal window.

December period ends inside the corresponding Indian fiscal-year window are
treated as valid; a naive equality between calendar year and fiscal-year end is
not used. Early-year coverage is parent-specific (2010-13 is entirely Vedanta;
2015-17 is dominated by Tata Communications), so temporal trends cannot be
generalized without parent-balanced designs.

## Missingness and duplicates

There are no fully identical 77-field rows. Nevertheless, duplication exists at
several meaningful levels:

- 94 target-year keys have multiple candidate sources;
- 518 targets appear in multiple source rows/years;
- one target has 16 raw rows;
- 16 normalized entity clusters repeat;
- 51 parsed balance-sheet signatures repeat across targets.

Structural name, parent, country, UIN, sector, and level fields are nonblank for
all target occurrences; apparent completeness does not establish correctness.
Financial missingness is extensive: among preferred rows, assets are present for
28.0%, equity for 28.4%, PAT for 21.1%, operating cash flow for 9.1%, and most
capital-flow items for 1-3%. The complete variable-by-sample matrix is in
`tables/variable_missingness.csv`.

## Analytical rules adopted

- Never count raw rows as firms.
- Report parent exposure and global unique-entity counts separately.
- Do not use UIN as a legal-entity identifier.
- Retain unresolved paths and report path-completion rates.
- Treat reported depth and reconstructable graph distance as distinct measures.
- Do not treat zero stake as zero economic ownership.
- Do not aggregate absolute financial amounts across missing units/currencies.
- Use parent weighting and leave-one-parent-out checks for pooled patterns.
- Use unique entities or entity means to remove panel-length weighting.
- Describe anomalies as unusual or data-quality-sensitive, never as evidence of
  wrongdoing.
