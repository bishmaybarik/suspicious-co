# Research findings

These are candidate empirical findings and research directions, not allegations
of wrongdoing. Scores run from 1 (low) to 5 (high); total is the sum of surprise,
robustness, economic relevance, and potential paper value. Ranking prioritizes
patterns that survive denominator and parent-group checks.

## Ranked shortlist

| Rank | ID | Short description | Surprise | Robustness | Relevance | Paper value | Total |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | X-F007 | Netherlands and Mauritius are disproportionately present as ownership-path intermediaries | 5.0 | 4.5 | 5.0 | 5.0 | 19.5 |
| 2 | X-F005 | Similar-sized groups have sharply different structural architectures | 5.0 | 5.0 | 5.0 | 4.5 | 19.5 |
| 3 | X-F001 | Raw rows radically misweight parent and jurisdiction exposure | 5.0 | 5.0 | 5.0 | 4.0 | 19.0 |
| 4 | X-F018 | Geographically broad groups can depend on one dominant UIN channel | 4.5 | 4.5 | 5.0 | 4.5 | 18.5 |
| 5 | X-F004 | Reported depth and reconstructable graph distance diverge materially | 5.0 | 5.0 | 4.5 | 4.0 | 18.5 |
| 6 | X-F009 | A small set of high-outdegree hubs organizes much of the network | 5.0 | 4.5 | 4.5 | 4.5 | 18.5 |
| 7 | X-F019 | The pooled depth–ownership gradient is mostly parent composition | 4.5 | 5.0 | 5.0 | 3.5 | 18.0 |
| 8 | X-F008 | A majority of nonroot edges are cross-border under robust weighting | 3.5 | 5.0 | 5.0 | 4.0 | 17.5 |
| 9 | X-F006 | Deep hierarchy and “deep manufacturing” are parent-driven, not general | 4.5 | 5.0 | 4.0 | 4.0 | 17.5 |
| 10 | X-F003 | Normalized entities recur across parent buckets and within multiple paths | 4.0 | 5.0 | 5.0 | 3.5 | 17.5 |
| 11 | X-F010 | Zero mapping stakes cannot safely be interpreted as zero ownership | 4.5 | 4.5 | 5.0 | 3.0 | 17.0 |
| 12 | X-F011 | Financial readiness is sparse and strongly selected by parent/panel length | 4.0 | 5.0 | 5.0 | 3.0 | 17.0 |
| 13 | X-F012 | “Ready” balance sheets still require sign, unit, and P&L gates | 4.5 | 5.0 | 4.0 | 3.0 | 16.5 |
| 14 | X-F013 | No robust financial-depth association survives basic controls | 3.5 | 4.5 | 4.5 | 4.0 | 16.5 |
| 15 | X-F014 | US concentration is real but denominator- and parent-sensitive | 3.5 | 4.0 | 4.5 | 4.0 | 16.0 |
| 16 | X-F015 | The nominal foreign-entity sample contains domestic and non-country labels | 4.0 | 5.0 | 3.5 | 2.5 | 15.0 |
| 17 | X-F016 | Temporal coverage cannot support an unqualified time-series narrative | 3.0 | 5.0 | 4.0 | 3.0 | 15.0 |
| 18 | X-F002 | UIN is a project/exposure identifier here, not an entity identifier | 4.0 | 5.0 | 4.0 | 2.0 | 15.0 |
| 19 | X-F017 | Repeated parsed balance-sheet signatures require source-level review | 4.0 | 3.5 | 4.0 | 3.0 | 14.5 |

## X-F001 — Raw rows radically misweight parent and jurisdiction exposure

**Result.** The 3,742 source rows collapse to 3,567 preferred target-years,
1,834 structural targets, 1,830 parent-scoped normalized entities, and 1,818
global normalized entity candidates. Tata Communications contributes 550 raw
rows (14.70%) but only 49 parent-scoped normalized entities (2.68%), a 5.49-fold
row-share/entity-share ratio. Motherson moves in the opposite direction: 332
raw rows (8.87%) versus 309 normalized entities (16.89%), ratio 0.53. The four
largest parent groups hold 46.50% of parent-scoped entities.

**Unit / numerator / denominator.** Raw-row shares use rows per parent / 3,742.
Entity shares use normalized group entities per parent / 1,830. Tata
Communications has 11 preferred target-year rows per target; Motherson has 1.07.

**Why interesting.** A naive row-count result is principally a statement about
source availability and panel length. It can reverse parent rankings and distort
jurisdiction shares.

**Robustness.** Exact parent-scoped names give 1,834 and conservative normalized
names 1,830; the imbalance is virtually unchanged. Global normalization reduces
the total to 1,818 and likewise does not repair panel weighting.

**Mundane explanation.** Some parent groups publish long annual subsidiary
series or combined PDFs; others contribute a mostly cross-sectional mapping.

**Data-quality explanation.** None is required—the imbalance is a property of
the collection design—but missed filings can amplify it.

**Falsification test.** Re-estimate every headline result under raw-row,
preferred target-year, unique-target, normalized group-entity, global-entity,
and equal-parent denominators. Results that exist only in raw rows fail.

**Relevant outputs.** `row_denominators.csv`,
`ultimate_parent_analytical.csv`, `parent_size_concentration.csv`.

## X-F002 — UIN is not an entity identifier in this file

**Result.** Only 186 UINs label 1,834 structural targets. The median UIN maps to
two normalized group entities; `NDWAZ20010286` maps to 138 target occurrences.

**Unit / numerator / denominator.** Entity multiplicity is target occurrences
or normalized group entities per UIN across the 1,834-target structural table.

**Why interesting.** UIN-level counting would collapse long subsidiary chains
and could turn 138 distinct reported entities into one observation.

**Robustness.** Structural fields are invariant within target; the mismatch is
not created by repeated source rows. It persists under conservative entity
normalization.

**Mundane explanation.** RBI UINs can organize ODI projects/exposures whose
reported downstream structures contain many legal entities.

**Data-quality explanation.** Reuse or inheritance of UIN through mapping files
could enlarge multiplicity; the dictionary itself does not promise one UIN per
legal entity.

**Falsification test.** Obtain an authoritative legal-entity identifier or the
upstream UIN mapping and test whether each named entity is intended to inherit
the direct ODI UIN.

**Relevant output.** `uin_multiplicity.csv`.

## X-F003 — Entities recur across parent buckets and multiple paths

**Result.** Punctuation/spacing normalization finds 16 repeated global
name-country clusters covering 32 target occurrences. Twelve span multiple
ultimate-parent buckets; four repeat within one parent and have two parent nodes
each. Global normalization therefore yields 1,818 entities versus 1,830
parent-scoped entities. Sixty-one additional fuzzy pairs are review candidates
but are not automatically merged.

**Unit / numerator / denominator.** Duplicate cluster / 1,818 global normalized
entity candidates; repeated occurrences / 1,834 structural targets.

**Why interesting.** Parent exposure and global unique-company counts answer
different questions. Shared ventures should appear in each parent's exposure
network but only once in a global legal-entity count.

**Robustness.** The 16 clusters require only punctuation/spacing normalization
and matching country; no aggressive suffix stripping or fuzzy merge is used.

**Mundane explanation.** Cross-parent repeats can be joint ventures; within-
parent repeats can be name versions, restructuring, or genuine multi-parent
ownership paths.

**Data-quality explanation.** Aliases, punctuation changes, different UINs, and
historical/current mappings can create duplicates. Fuzzy candidates include
many legitimate numbered siblings, illustrating why automatic deduplication is
risky.

**Falsification test.** Match company-registration numbers and effective dates;
for joint ventures, verify contemporaneous ownership shares.

**Relevant outputs.** `entity_duplicate_clusters.csv`,
`entities_with_multiple_parent_nodes.csv`,
`fuzzy_entity_duplicate_candidates.csv`.

## X-F004 — Reported depth and graph distance diverge materially

**Result.** Of 1,650 nonroot edges, 1,500 (90.91%) find an observed parent at the
expected preceding level, 72 find the named parent at another level, and 78 have
an absent parent. Recursion reaches the ultimate parent for 1,687/1,834 targets
(91.98%), but 236/1,687 complete paths (13.99%) have reported depth exceeding
reconstructed graph distance by one to four levels. Reported level 5+ contains
342/1,834 targets (18.65%); only 125/1,687 complete paths (7.41%) have
reconstructed distance 5+.

**Unit / numerator / denominator.** Edge linkage uses 1,650 nonroot target
occurrences. Path completion uses all 1,834 targets. Depth disagreement uses
only 1,687 complete paths.

**Why interesting.** Deep-hierarchy results depend on whether “depth” means an
upstream reported label or the number of observed graph edges.

**Robustness.** Motherson has maximum reported/reconstructed depth 12/8 and
208/309 mismatching paths. Hindalco is 12/6, with only 38/81 complete. Reported
level-5+ share is 18.65% pooled but 7.34% under equal-parent weighting.

**Mundane explanation.** Reported levels may count intermediates omitted from
the target table; graph distance then supplies a lower bound, not a correction.

**Data-quality explanation.** Missing parent targets, inconsistent level labels,
and name linkage can all create gaps. Exact names account for 1,532 observed
nonroot links; normalized names add 40 without changing the main issue.

**Falsification test.** Reconstruct chains from original mapping files or annual
report ownership diagrams and insert omitted parent nodes with stable IDs.

**Relevant outputs.** `hierarchy_linkage_summary.csv`,
`path_completion_summary.csv`, `reported_vs_reconstructed_depth.csv`,
`path_reconstruction_mismatches.csv`.

## X-F005 — Parent groups have distinct structural architectures

**Result.** Motherson has 309 normalized entities, 45 jurisdictions, reported
maximum depth 12, jurisdiction HHI 0.060, and 68.28% of targets at reported level
5+. Reliance Industries has 196 entities but only 22 jurisdictions, maximum depth
2, HHI 0.357, and 57.14% of entities in the US. Wipro combines 212 entities, 51
jurisdictions, and maximum depth 8. Tata Communications has only 49 normalized
entities across 32 jurisdictions (HHI 0.054).

Reliance's shallow count is also portfolio-like: 141/177 nonroot edges (79.66%)
have a positive stake at or below 50%, and two Breakthrough Energy Ventures
nodes have 67 and 42 direct children.

**Unit / numerator / denominator.** One row per parent in the 1,830 normalized
group-entity table. Shares are within-parent entity shares; HHI is the sum of
squared jurisdiction shares.

**Why interesting.** “Corporate complexity” is multidimensional. Size, depth,
branching, geographic diversity, and ownership stake distinguish chain-heavy,
hub-heavy, and portfolio-heavy structures.

**Robustness.** Conservative alias collapse changes only four group-entity
counts. The contrasts are much larger than this ambiguity. Reported depth needs
the X-F004 qualification.

**Mundane explanation.** Acquisition history, sector, holding-company design,
fund investments, and disclosure practices naturally generate different
architectures.

**Data-quality explanation.** Mapping scope and missed parents can exaggerate
shallow/deep differences; zero stakes cannot be treated literally.

**Falsification test.** Construct a preregistered multi-axis complexity index,
compare within sector and size bins, and validate against consolidated annual-
report subsidiary lists.

**Relevant output.** `ultimate_parent_analytical.csv` and
`parent_structure_landscape.png`.

## X-F006 — Deep hierarchy and deep manufacturing are parent-driven

**Result.** There are 342 reported level-5+ targets. Motherson contributes 211
(61.70%); adding Hindalco (54) and Wipro (47) raises the top-three contribution
to 312/342 (91.23%). The pooled deep share is 18.65%, the equal-parent mean is
7.34%, and leave-one-parent-out ranges from 8.59% (omit Motherson) to 20.88%.

Manufacturing appears especially deep: 242/508 manufacturing targets (47.64%)
are level 5+. But Motherson contributes 186 and Hindalco 54—240/242 (99.17%).
Omitting Motherson reduces the manufacturing deep share to 56/264 (21.21%).

**Unit / numerator / denominator.** Target occurrence, using reported level.
Sector-specific denominator is 508 manufacturing targets.

**Why interesting.** A highly publishable-looking sector-depth association is
mostly a composition effect from two groups.

**Robustness.** Unique target and parent-scoped normalized entity counts are
nearly identical. Parent weighting and leave-one-parent-out are decisive;
graph-reconstructed depth makes the pooled deep share smaller still.

**Mundane explanation.** Automotive/aluminium groups may have long acquisition
chains; other manufacturing parents may hold subsidiaries more directly.

**Data-quality explanation.** Reported levels count missing intermediates, and
Motherson supplies most level discrepancies.

**Falsification test.** Estimate within-parent or matched-parent sector effects;
obtain more parents per sector; repeat on reconstructed and externally verified
depth.

**Relevant outputs.** `sector_depth.csv`,
`sector_depth_leave_one_parent_out.csv`,
`structural_weighting_sensitivity.csv`.

## X-F007 — Netherlands and Mauritius are path intermediaries

**Result.** The Netherlands is 110/1,830 normalized group entities (6.01%) but
19.69% of observed-entity appearances in complete ownership paths. With equal
parent weights, its entity share is 7.97% and ancestry share is still 14.61%.
Dutch parent nodes generate 299 nonroot child occurrences, 226 cross-border
(75.59%), spanning 75 child jurisdictions and 16 parent groups; the largest
parent supplies only 30.10%.

Mauritius is 57/1,830 entities (3.11%) but 8.11% of complete-path ancestry
appearances. Equal-parent shares are 3.65% versus 8.26%. Mauritian parent nodes
generate 191 children, 163 cross-border (85.34%), across 52 destinations and ten
groups; Jindal supplies 45.03%.

**Unit / numerator / denominator.** Entity share: normalized group entities in
country / 1,830. Ancestry share: observed nodes of that country / all observed
nodes in complete target paths. Intermediary edges exclude level-0 root edges.

**Why interesting.** These jurisdictions appear repeatedly upstream of many
downstream entities, beyond what resident entity counts alone imply.

**Robustness.** The ancestry/entity ratio survives equal-parent weighting. The
Netherlands result spans 16 groups and leave-one-parent-out entity share stays
4.30-6.64%; Mauritius is more parent-sensitive but spans ten groups. Incomplete
paths are excluded, which may understate or overstate particular groups.

**Mundane explanation.** Regional holding companies, historical acquisitions,
financing coordination, treaty networks, and administrative convenience can all
produce gateway structures. No tax or legal conclusion follows from topology.

**Data-quality explanation.** Shared prefixes are repeated once for every
descendant path, mechanically making branching intermediaries prominent. That is
the phenomenon being measured, not a unique-entity count.

**Falsification test.** Repeat on leaf-only paths, unique intermediary nodes,
equal-parent paths, and externally verified complete chains; then relate gateway
use to sector, destination region, acquisition history, and time.

**Relevant outputs.** `jurisdiction_counts.csv`,
`intermediary_jurisdictions.csv`, `leaf_path_motifs.csv`.

## X-F008 — Most nonroot ownership edges cross jurisdictions

**Result.** Excluding the mechanically India-to-foreign level-0 edges, 951 of
1,650 nonroot edges (57.64%) cross jurisdiction labels. The equal-parent mean is
58.67%; leave-one-parent-out estimates range only from 56.06% to 61.78%.

**Unit / numerator / denominator.** Reported target edge; numerator is child
country different from immediate-parent country. Denominator is 1,650 nonroot
edge occurrences.

**Why interesting.** Cross-border layering is a majority feature across this
sample, not solely a consequence of one huge group.

**Robustness.** Pooled, equal-parent, and leave-one-parent-out estimates agree.
Rates are not monotonic with reported depth: level 3 is 55.0% pooled but 29.0%
equal-parent, while level 5 is 75.0% pooled but 49.3% equal-parent. Parent
composition matters for level-specific claims.

**Mundane explanation.** Multinationals use regional parents to own operating
entities in destination markets; acquisition structures also preserve
cross-country parents.

**Data-quality explanation.** Country labels contain a few regional/special-zone
values, and missing parent nodes make some paths incomplete, but each edge still
has reported parent/child country labels.

**Falsification test.** Standardize jurisdictions against authoritative codes,
remove special-zone/ambiguous labels, collapse alias edges, and estimate within-
parent/sector transition rates.

**Relevant outputs.** `edge_geography_by_level.csv`,
`structural_leave_one_parent_out.csv`, `country_transitions.csv`.

## X-F009 — High-outdegree hubs organize much of the network

**Result.** Of 1,830 normalized group entities, 1,427 are leaves and 403 are
observed parents of at least one child. Thirty-four observed entities with at
least ten direct children account for 742/1,834 logical edge relations (40.46%).
The three largest hubs alone have 190 edges (10.36%).

The largest is Jindal Steel and Power Mauritius Ltd: 81 children across 24 child
jurisdictions, 73 cross-border. Two Reliance-attributed Breakthrough Energy
Ventures nodes have 67 and 42 children. An unobserved Dr Reddy's Laboratories SA
node is named as parent of 29 children, explaining much of that group's path
truncation.

**Unit / numerator / denominator.** Parent-scoped normalized graph node and
distinct logical parent-child edge. Root and synthetic nodes are separately
typed.

**Why interesting.** Complexity is generated disproportionately by star-like
hubs, which can dominate motifs and country transitions even without long
chains.

**Robustness.** Direct-child counts use unique logical edges, not source rows or
path appearances. The top hubs remain large under entity normalization.

**Mundane explanation.** Regional holding companies and investment funds are
designed to own many operating companies or portfolio investments.

**Data-quality explanation.** AOC/mapping tables can flatten intermediate
levels; missing parent targets can turn a named but unobserved node into an
artificial hub.

**Falsification test.** Compare audited ownership charts; classify hubs as funds,
holdings, or operators; recompute downstream reach after inserting missing
nodes.

**Relevant output.** `branch_hubs.csv`.

## X-F010 — Zero mapping stakes are not literal zero ownership

**Result.** All 184 level-0 targets have missing mapping stake, while all 1,650
nonroot targets have a numeric stake; 406/1,650 are exactly zero (24.61%). The
zero share ranges from 0.78% for Airtel to 100% for the Reliance Energy bucket.
Among 45 preferred rows with both mapping stake and AOC-1 shareholding, seven
have stake zero but positive AOC shareholding, and eight differ by more than one
percentage point.

**Unit / numerator / denominator.** Nonroot edge occurrence for mapping stake;
preferred target-year with both measures for cross-validation.

**Why interesting.** Treating zero as economic ownership would erase chains,
misclassify control, and make cumulative stake products zero.

**Robustness.** The AOC comparison directly falsifies literal zero in seven
observations (six AOC shares are 100%, one is 73.94%). The broader 406 zeros
remain unresolved.

**Mundane explanation.** Zero may be an upstream placeholder for unavailable or
indirect stake, or reflect a historical mapping rather than current ownership.

**Data-quality explanation.** Numeric zero was likely used where missing would
be semantically preferable; effective dates may also differ between mapping and
financial statement.

**Falsification test.** Return to mapping source fields, distinguish unknown from
true zero, and align stake to financial-statement period. Do not estimate control
until then.

**Relevant outputs.** `stake_quality.csv`, `stake_by_parent.csv`,
`ownership_measure_comparison.csv`.

## X-F011 — Financial readiness is sparse and selected

**Result.** Only 560/3,567 preferred target-years are ready (15.70%), covering
265/1,834 targets at least once (14.45%). The average within-entity ready-year
fraction is 8.97%, while the equal-parent mean target-year rate is 12.95%.
Tata Communications supplies 190/560 ready rows (33.93%) and 46/50 of its
targets are ever ready (92%). Five parent groups have no ready target at all.
Removing one parent moves the pooled readiness rate from 12.26% to 16.63%.

**Unit / numerator / denominator.** Preferred target-year, unique target ever
ready, entity mean across observed years, and equal-parent mean are all reported
separately.

**Why interesting.** Financial analyses describe a selected subset of entities,
years, parents, and source regimes, not the 1,834-target hierarchy.

**Robustness.** Selection remains severe under all denominators. The direction
of parent imbalance changes with target-year versus entity-ever-ready counting,
which is itself diagnostic.

**Mundane explanation.** Availability of standalone statements and combined
subsidiary accounts differs by parent, year, language, and filing practice.

**Data-quality explanation.** Search/parser failures, missing periods/currencies,
and section-location failures drive readiness.

**Falsification test.** Model selection using structural observables, apply
inverse-probability bounds only with credible assumptions, and prioritize manual
collection for low-coverage parents.

**Relevant outputs.** `parent_financial_coverage.csv`,
`financial_weighting_sensitivity.csv`,
`financial_leave_one_parent_out.csv`.

## X-F012 — Ready rows still need additional plausibility gates

**Result.** Of 560 ready balance sheets, 39 (6.96%) fail the added basic gate:
assets must be positive and liabilities nonnegative. There are three negative-
asset rows, one zero-asset row, and 38 negative-liability rows, with overlap.
Only 105/560 ready rows (18.75%; 2.94% of all preferred rows) have a valid,
testable P&L identity. Units are blank for 516/560 ready rows (92.14%).

Within the 521 basic-plausible rows, 127 have negative equity (24.38%); the
equal-parent rate is 18.98% and pooled leave-one-parent-out is 21.70-26.36%.
Within the 105 P&L-valid rows, 36 are loss-making (34.29%); equal-parent is
38.42% and leave-one-parent-out 31.58-39.13%.

**Unit / numerator / denominator.** Preferred target-year. Negative equity uses
the 521-row basic sample; loss uses the 105-row P&L-valid sample.

**Why interesting.** Accounting-identity success is necessary but insufficient
for economically interpretable ratios, and “ready for valuation” does not imply
P&L readiness.

**Robustness.** Sign anomalies are exact data values. Negative-equity/loss rates
are reasonably stable to leave-one-parent-out but not representative because
selection into the samples is severe.

**Mundane explanation.** Negative equity and operating losses can be legitimate.
Negative assets/liabilities more likely reflect sign/extraction conventions.

**Data-quality explanation.** Evidence lines can mix signs, periods, consolidated
sections, or scales. Missing units prevent safe absolute-value pooling.

**Falsification test.** Manually audit evidence lines for all sign/extreme rows,
normalize units, and reproduce statement totals from source PDFs.

**Relevant outputs.** `financial_plausibility.csv`,
`financial_anomalies_for_review.csv`, `financial_sample_definitions.csv`.

## X-F013 — No robust financial-depth relationship is established

**Result.** At entity level, reported depth 2+ is associated with -1.72
percentage points in ever-ready coverage (clustered p = 0.654), -1.63 pp with
parent fixed effects (p = 0.579), and -0.36 pp under equal-parent weighting
(p = 0.916). In the 521-row basic sample, the deep coefficient for negative
equity is +1.22 pp pooled (p = 0.910) and -0.44 pp with parent/year fixed effects
(p = 0.975). In the 105-row P&L sample, the loss coefficient is +4.01 pp pooled
(p = 0.674) and -1.64 pp with parent fixed effects (p = 0.887).

**Unit / numerator / denominator.** Unique target for coverage; preferred
target-year for negative equity and loss. Standard errors cluster by 28, 23, or
15 represented parents. Models are descriptive linear-probability regressions.

**Why interesting.** Binned raw rates look irregularly different by level, but
no monotonic or within-parent pattern survives simple robustness checks.

**Robustness.** Pooled, fixed-effect, and parent-weighted estimates are all near
zero relative to uncertainty. Reconstructed-depth bins also remain nonmonotonic.

**Mundane explanation.** Financial health need not vary with legal ownership
depth after sector, role, and group strategy are considered.

**Data-quality explanation.** Severe outcome selection, depth mismeasurement,
small P&L N, and repeated years make null estimates imprecise.

**Falsification test.** Improve financial coverage, use verified depth, separate
holding/operating entities, and estimate within-sector, within-parent, matched-
year models.

**Relevant outputs.** `financial_models.csv`, `financial_by_depth.csv`,
`financial_by_reconstructed_depth.csv`.

## X-F014 — US concentration is real but sensitive to denominator and parent

**Result.** The US contains 363/1,830 parent-scoped normalized entities (19.84%)
and 356/1,818 global entities (19.58%). Its raw-row share is 17.00% and equal-
parent entity share 16.02%; leave-one-parent-out group-entity share ranges from
15.36% to 22.09%. It occurs in 19 parent groups.

US-to-US is the most common logical country transition: 287 edges across 15
parents; Reliance supplies 35.54%. The complete leaf motif
India -> US -> US occurs for 158 leaf paths across ten parents, but Reliance
supplies 61.39%. At reported level 1, 188/779 targets (24.13%) are US entities
and Reliance supplies 52.66% of them.

**Unit / numerator / denominator.** Normalized entity, logical edge, and complete
leaf path are separate denominators.

**Why interesting.** US prominence is broad but its magnitude and apparent path
motif depend on joint-entity collapse, parent weighting, and portfolio-heavy
groups.

**Robustness.** The US remains the largest entity jurisdiction under every
denominator. Group dominance is moderate for US-to-US edges but high for the
specific full leaf motif and level-1 composition.

**Mundane explanation.** The US is a large operating and investment market;
same-country US layering can reflect domestic subholding/fund structures.

**Data-quality explanation.** Complete-path motifs repeat common ancestors for
descendant leaves and exclude truncated groups.

**Falsification test.** Separate funds/minority investments from controlled
subsidiaries, use unique root-to-leaf chains, and compare to parent industry and
acquisition history.

**Relevant outputs.** `jurisdiction_counts.csv`, `country_transitions.csv`,
`full_leaf_jurisdiction_paths.csv`, `jurisdiction_by_depth.csv`.

## X-F015 — Nominally foreign targets include domestic/special-zone labels

**Result.** Of 1,834 structural targets, 1,814 (98.91%) have conventional foreign
jurisdiction labels, ten (0.55%) are labeled India, nine (0.49%) are labeled
IFSC GIFT CITY, and one (0.05%) is labeled EUROPEAN UNION. The India targets span
six parents and levels 1-5; IFSC targets span five parents and levels 0-1.

**Unit / numerator / denominator.** Structural target occurrence / 1,834.

**Why interesting.** “Foreign entity” is not perfectly equivalent to the
country field, affecting domestic/foreign comparisons and direct-root logic.

**Robustness.** Counts are exact raw labels; conservative standardization does
not reclassify ambiguous conceptual categories.

**Mundane explanation.** IFSC entities may be intentionally included in ODI-
related mappings; downstream Indian subsidiaries can sit under foreign parents.

**Data-quality explanation.** `EUROPIAN UNION` is not a country, and some labels
may reflect reporting categories rather than incorporation jurisdiction.

**Falsification test.** Obtain incorporation-country codes and an explicit rule
for IFSC treatment; report results with and without these 20 targets.

**Relevant outputs.** `foreign_domestic_summary.csv`,
`domestic_special_zone_entities.csv`, `country_label_quality.csv`.

## X-F016 — Temporal coverage is too unbalanced for naive trends

**Result.** 993/3,567 preferred rows (27.84%) have blank fiscal year and
2,252/3,567 (63.13%) have blank period end. Among 1,302 rows with a parseable
period date and fiscal window, 70 (5.38%) fall outside it. Every 2010-13 row is
Vedanta; Tata Communications supplies 73.5% of 2015-16 and 75.8% of 2016-17.

**Unit / numerator / denominator.** Preferred target-year row. Date consistency
uses the 1,302 rows with both parseable date and valid fiscal-year label.

**Why interesting.** Apparent aggregate time trends can simply trace changing
parent coverage. Moreover, hierarchy variables are static within target and do
not measure time-varying restructuring.

**Robustness.** Missingness and parent dominance are exact. December period ends
inside the relevant April-March window are accepted, avoiding a false mismatch.

**Mundane explanation.** Filing availability expands over time and varies by
parent; foreign entities can have December year-ends.

**Data-quality explanation.** Missing/partial date strings and mismatched source
periods account for some inconsistencies.

**Falsification test.** Restrict to a balanced parent-entity panel, verify period
ends, and analyze ratios only within consistently observed entities. Structural
time trends require annual ownership mappings not present here.

**Relevant outputs.** `temporal_coverage.csv`, `date_quality.csv`.

## X-F017 — Repeated parsed balance-sheet signatures need source review

**Result.** Among 863 preferred rows with all three core balance variables
parsed, 51 exact fiscal-year/currency/units/assets/liabilities/equity signatures
involve 104 rows (12.05%). There are no fully identical 77-field source rows.

**Unit / numerator / denominator.** Preferred parsed target-year row. Signature
includes fiscal year, currency, units, assets, liabilities, and equity.

**Why interesting.** Equal signatures can signal aliases/shared entities,
dormant sibling shells, or one combined-PDF section reused across targets. They
can also duplicate the same economic balance sheet across parent buckets.

**Robustness.** Equality is exact; interpretation is not. Known cross-parent
entity aliases explain part, and equal zero/shell balances can be legitimate.

**Mundane explanation.** Joint ventures appear for multiple parent exposures;
shell entities may have identical capital and no liabilities; a combined report
can contain repeated values.

**Data-quality explanation.** Section matching or source reuse can assign one
statement to multiple targets. Several same-source/year signatures have
different entity names and therefore require evidence review.

**Falsification test.** Compare entity-name evidence/section boundaries and PDF
page locations for all 51 clusters; classify them as alias, shared venture,
legitimate equal balance, or extraction error before econometric use.

**Relevant outputs.** `duplicate_financial_signatures.csv` and evidence-bearing
input fields.

## X-F018 — Geographically broad groups can depend on one UIN channel

**Result.** For each ultimate parent, take the UIN carried by the largest number
of target occurrences. These 28 largest-UIN cells contain 1,095/1,834 targets
(59.71%). The equal-parent mean is 62.05%, the median-parent share is 61.16%,
and the pooled leave-one-parent-out range is 57.18–62.75%.

The contrast is stronger among geographically broad groups. For the 14 parents
with targets in at least 20 jurisdictions, the equal-parent largest-UIN share is
71.23%. Jindal has 108/108 targets in one UIN while spanning 24 jurisdictions;
UPL has 79/81 across 39; Hindalco 77/81 across 25; Biocon Biologics 22/23 across
20; and Glenmark 31/38 across 28.

**Unit / numerator / denominator.** Primary numerator = targets carrying the
within-parent modal UIN, summed over parents; denominator = all 1,834 target
occurrences. One row per parent defines the equal-parent estimand.

**Why interesting.** Country diversification and registration-channel
diversification are separate dimensions. A group can appear highly global by
destination while most mapped entities inherit one outward-investment channel.

**Robustness.** Parent-scoped and global unique-entity versions are 59.62% and
59.85%. A different complete-path estimator—the first observed foreign node—
gives 61.17% pooled and 61.22% parent-equal over 1,687 paths.

**Hierarchy qualification.** Motherson's largest UIN share is 44.66%, while
cross-UIN graph linkage puts 64.40% of complete paths behind one Dutch root. Dr
Reddy's modal UIN has no observed level-0 target, so its 90.24% UIN share cannot
be interpreted as an observed legal vehicle. UIN concentration is the robust
claim; group-specific gateway identity needs a complete graph.

**Mundane explanation.** One acquisition can bring a multi-country target group
under a single UIN, and the mapping may mechanically propagate that UIN to all
descendants. This does not show that current funds or legal control traverse one
company.

**Falsification test.** Validate UIN inheritance against the original ODI
register and dated acquisition structures; separate current legal ownership
from the mapping's exposure attribution.

**Relevant outputs.** `review/tables/gateway_dependency_by_parent.csv`,
`review/tables/gateway_dependency_sensitivity.csv`, and
`review/figures/gateway_dependency_landscape.png`.

## X-F019 — The pooled depth–ownership gradient is parent composition

**Result.** Among 1,244 nonroot edges with a positive recorded stake, 56.37% of
reported-level-1 edges are at least 99.5% owned, versus 82.78% at level 2+: an
entity-weighted difference of 26.41 percentage points. Equal-parent rates are
73.60% and 75.93%, only 2.33 points apart. The paired within-parent difference
across 25 groups is 4.44 points and its median is zero.

Reliance is decisive. Excluding it reduces the pooled gap to 6.10 points and
the equal-parent gap to 0.03 points. Excluding child edges of the two
Breakthrough Energy vehicles gives 12.59 points; excluding UINs whose third
character is P gives 18.99 points. The third character is not assigned a legal
meaning without external validation.

**Unit / numerator / denominator.** Nonroot structural target/edge with
`stake > 0`. “Fully owned” means recorded mapping stake at least 99.5%. Reported
level 1 is compared with reported level 2+.

**Why interesting.** A seemingly strong structural regularity becomes a
portfolio-composition result once ultimate-parent groups receive comparable
weight.

**Robustness.** Parent-scoped/global de-duplication changes the rates by less
than one point. On complete paths, reconstructed graph depth yields a 26.14
point entity-weighted gap but only 3.23 points in the paired parent comparison.
Hierarchy correction therefore does not rescue the pooled interpretation.

**Missing-data bounds.** The other 406 nonroot stakes are recorded as zero and
treated as unknown. If every zero were non-full, level-1/level-2+ full-ownership
rates would be 37.48%/69.00%; if every zero were full, they would be
70.99%/85.65%. The pooled ordering survives extreme assumptions, while the
across-parent generalization does not.

**Mundane explanation.** Reliance's shallow US layer contains venture-fund
portfolio exposures and minority positions. Other groups' deeper layers often
contain consolidated entities inherited through acquisitions.

**Falsification test.** Recover contemporaneous legal stakes, classify control,
joint control, associates, and fund look-through holdings, then estimate
within-parent and within-acquisition differences.

**Relevant outputs.** `review/tables/stake_depth_sensitivity.csv`,
`review/tables/stake_zero_bounds.csv`, `review/tables/stake_depth_by_parent.csv`,
and `review/figures/ownership_stake_depth_sensitivity.png`.

## Cross-cutting interpretation

The strongest paper-oriented directions are topology and denominator design,
not financial anomalies. In particular:

1. treat parent networks as distinct structural archetypes rather than pooling
   them as exchangeable subsidiaries;
2. model gateway jurisdictions with unique-node, edge, and descendant-path
   measures side by side;
3. separate controlled subsidiaries, joint ventures, and minority/fund
   investments once ownership data are repaired;
4. validate the hierarchy before interpreting reported depth; and
5. treat current financial results as selection/audit findings until coverage,
   units, and P&L validation improve.
