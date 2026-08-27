# Final cross-review and adjudication

## Scope, provenance, and decision rule

This document is Codex's final cross-review before joint synthesis. I reviewed
the tip of `origin/agent/claude` as Git objects, without switching branches or
modifying its worktree.

- **Exact Claude commit reviewed:**
  `79b342b1ae3a473fef40a5c8dc91fa937597185e`
- **Subject:** `research(review): reproduce eight Codex findings and add
  chokepoint, naming and ownership-dilution analyses`
- **Claude history inspected:** the tip above and its parent
  `5ab6cb5944ad6fe8193f03b71f7a918ac4d24076` —
  `research(structure): reconstruct ODI subsidiary hierarchy and document 17
  candidate findings`
- **Common branch fork:**
  `29109a3384ba0f3471a2b677f04295a51d8aadaa`
- **Input SHA-256:**
  `65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea`

The new replications use only the immutable Stata input and Codex's
independently constructed entity, edge, and path tables. They do not read or
execute Claude files. The reproducible code is
`src/codex/final_adjudication.py`; diagnostic tables are under
`outputs/codex/final/`.

A result enters the final shortlist only if its unit, numerator, denominator,
missingness rule, duplicate treatment, parent weighting, and hierarchy
definition are explicit. “Observed in these 28 parent buckets” must not be
rewritten as “typical of all Indian multinationals.” Nothing here establishes
tax motivation, legal treatment, regulatory effect, or misconduct.

### Denominator map used in the adjudication

| Unit | Count | Defensible use |
|---|---:|---|
| Raw source row | 3,742 | Candidate statement/source panel; never a firm count |
| Preferred target-year | 3,567 | One upstream-selected source per target-year |
| Structural target occurrence | 1,834 | One reported ownership-path target |
| Parent-scoped normalized entity candidate | 1,830 | Primary within-group entity denominator |
| Global normalized entity candidate | 1,818 | Cross-parent de-duplicated legal-entity candidate denominator |
| Nonroot target edge | 1,650 | One reported immediate-parent relation below level 0 |
| Complete observed path | 1,687 | Path reaches the Indian parent through observed entities |
| UIN | 186 | Mapping/registration channel, not a legal-entity identifier |
| Observed level-0 target | 184 | Two UINs lack an observed first-hop target |
| Ultimate-parent bucket | 28 | Equal-parent and leave-one-parent-out unit |

The 1,830 and 1,818 totals are conservative name-country candidates, not a
substitute for official company identifiers. Parent exposure and global unique
company counts remain distinct estimands.

## Recommended study design

**Central research question.** How do the sampled major Indian parent groups
organize their reported foreign ownership networks across registration
channels, hierarchy, and jurisdictions, and which apparent regularities survive
entity de-duplication, parent balance, missing-node corrections, and alternative
graph definitions?

**Main empirical narrative.** The useful contribution is not a league table of
“suspicious” jurisdictions. It is a measurement-corrected account of foreign
ownership topology. The 28 groups exhibit different combinations of size,
depth, branching, geography, minority exposure, and dominant gateways. A few
jurisdictions repeatedly occupy intermediary roles, but descendant-weighted
path exposure must be separated from unique-node prevalence. Several tempting
pooled results—deep manufacturing, ownership increasing with depth, and
financial-depth patterns—are primarily parent composition or data-selection
effects.

**Recommended eight-result sequence.** The paper should present, in order:

1. raw-row weighting severely distorts the parent and jurisdiction composition;
2. network architecture is multidimensional rather than a single “complexity”
   scale;
3. many groups are concentrated behind one UIN channel or one large observed
   subtree;
4. the Netherlands and Mauritius are overrepresented as intermediary nodes and
   have unusually large downstream reach;
5. 951/1,650 nonroot edges cross a jurisdiction boundary, robust to parent
   weighting;
6. reported depth differs from observed graph distance, while pooled deep and
   sector patterns are dominated by a few groups;
7. the apparent ownership-depth gradient is largely group composition, and
   recorded zero stakes cannot be treated literally; and
8. the financial layer is too selected and extraction-contaminated to support
   population financial conclusions.

### Evidence boundary

**A. Facts established by this dataset and replication**

- The sample, entity, path, edge, UIN, and parent counts above.
- Reported parent-child topology and supplied country labels, subject to the
  documented missing-node and name-resolution limitations.
- Entity-, edge-, path-, parent-equal, and leave-one-parent-out statistics
  stated below.
- Internal contradictions between recorded mapping stakes and AOC-1 shares.
- Reuse of identical financial evidence across different named targets.

**B. Interpretations requiring external evidence**

- Whether a named entity is legally identical to an alias or shared venture.
- Whether UIN characters encode office, ownership type, or registration year.
- Whether a Dutch, Mauritian, Singaporean, Swiss, or other entity is a tax,
  treaty, financing, acquisition, governance, or operating vehicle.
- Whether a route reflects current legal ownership, historical acquisition
  structure, or inherited mapping attribution.
- Whether a legal or policy change would disrupt, reroute, or tax the network.
- Whether the 28 groups represent Indian outward investment generally.

## 1. Recommended core findings

### Core 1 — Denominator correction is empirically first order

The 3,742 source rows collapse to 3,567 preferred target-years, 1,834
structural targets, 1,830 parent-scoped normalized entities, and 1,818 global
normalized candidates. Tata Communications supplies 550/3,742 raw rows
(14.70%) but 49/1,830 normalized group entities (2.68%); Motherson supplies
332/3,742 rows (8.87%) but 309/1,830 entities (16.89%). Tata Communications is
first by raw rows and about eleventh by entities, whereas Motherson is first by
entities. Claude independently reproduced the ranking reversal.

This is a core measurement result because every downstream pooled statistic is
wrongly weighted if rows are called firms. Exact-name targets (1,834),
parent-scoped normalization (1,830), and global normalization (1,818) yield
similar aggregate structural results, but they answer different exposure
questions.

### Core 2 — Parent groups have different structural architectures

Size, country breadth, depth, branching, UIN concentration, and stake structure
do not reduce to a single ordering. Illustrative contrasts are large relative
to the four parent-scoped alias collapses:

- Motherson: 309 normalized entities, 45 jurisdictions, reported maximum depth
  12, and 68.28% of targets reported at level 5+.
- Reliance Industries: 196 entities, 22 jurisdictions, reported maximum depth
  2, 57.14% resident in the US, and a large shallow venture-fund portfolio.
- Wipro: 212 normalized entities across 51 jurisdictions and reported maximum
  depth 8.
- Tata Communications: 49 normalized entities across 32 jurisdictions, with a
  much longer financial panel per target than the other groups.

Depth is a measured axis, not a verified legal truth: missing parents and
reported/graph disagreement require the Core 5 qualification. The defensible
claim is architectural heterogeneity in this sample, not an externally ranked
index of “complexity.”

### Core 3 — Networks are concentrated behind dominant channels and subtrees

Two independent definitions agree that country breadth need not imply channel
diversification.

- The largest UIN within each parent contains 1,095/1,834 targets (59.71%).
  The equal-parent mean is 62.05%, the median-parent share is 61.16%, and the
  pooled leave-one-parent-out range is 57.18–62.75%. Parent-scoped and global
  normalized variants are 59.62% and 59.85%.
- Among the 24 groups with at least 15 targets, the median largest **observed
  subtree** contains 43.20% of normalized group entities below its top node;
  ten groups exceed 60%. Among groups with at least five observed level-0
  gateways, the median remains 41.75%.
- Treating the normalized entity graph as a DAG, so alternate reported parents
  can bypass a node, reduces the median strict root-dominator share only to
  41.72%; eight groups still exceed 60% of all group entities. This is the
  appropriate sensitivity to Claude's target-level forest assumption.

The UIN result is concentration in a registration/mapping channel, not proof
that a current legal company or cash flow is concentrated there. The subtree
result should not be called a legal “chokepoint” until missing parents and
alternate paths are resolved. Dr Reddy's is the clearest warning: its largest
observed subtree is only 7.5%, while the named but unscraped Swiss parent sits
above 37/41 targets.

### Core 4 — Gateway jurisdictions occupy distinct network roles

The Netherlands and Mauritius are not merely frequent resident locations; they
are disproportionately observed as parents/intermediaries under several
non-equivalent denominators.

| Statistic | Netherlands | Mauritius | United States comparator |
|---|---:|---:|---:|
| Parent-scoped resident entities | 110/1,830 (6.01%) | 57/1,830 (3.11%) | 363/1,830 (19.84%) |
| Unique observed intermediary nodes | 59/403 (14.64%) | 25/403 (6.20%) | 69/403 (17.12%) |
| Mean descendants per observed level-0 gateway | 34.85 | 17.88 | 9.89 |
| Median descendants per gateway | 12.0 | 5.0 | 1.5 |
| Parent groups represented among gateways | 12 | 11 | 12 |

For Dutch gateways the equal-parent mean is 37.08 descendants and the minimum
mean after omitting one parent is 21.25. Eight of thirteen Dutch gateways also
pass the restriction that no direct-child branch contains a majority of the
descendants; their mean is 37.75. Dutch nodes generate 299 nonroot child
occurrences, 226 cross-border, spanning 75 destination labels and 16 groups.
Mauritian nodes generate 191 children, 163 cross-border, across 52 destinations
and ten groups, although Jindal supplies 45.03%.

Path-appearance shares are useful measures of descendant exposure but repeat a
shared ancestor once for every target below it. The unique-intermediary-node
result above is therefore the decisive non-path-repeated robustness check.
These facts establish topology, not the institutional purpose of a company in
either jurisdiction.

### Core 5 — Reported depth is not graph distance, and pooled depth patterns are parent-driven

Of 1,650 nonroot edges, 1,500 link to an observed parent at the expected prior
level, 72 link to a named parent at another reported level, and 78 name a parent
absent from the target table. Recursion reaches the ultimate parent for
1,687/1,834 targets. Among those complete paths, 236/1,687 (13.99%) have
reported depth exceeding reconstructed distance by one to four levels;
Motherson supplies 208/236 (88.14%).

The dataset contains 342/1,834 reported level-5+ targets (18.65%), but the
equal-parent mean is 7.34%; omitting Motherson reduces the pooled share to
8.59%. The apparent manufacturing result is not general: Motherson and
Hindalco supply 240/242 reported deep-manufacturing targets. Only 125/1,687
complete paths have reconstructed distance 5+.

The negative result is paper-worthy: a striking pooled sector-depth pattern
fails parent weighting, and the depth variable itself has two defensible but
different meanings. Reported level may count omitted nodes; observed graph
distance is a lower bound. Neither should be relabeled “true depth.”

## 2. Supporting findings

### Supporting 1 — A majority of nonroot edges cross jurisdictions

Using supplied child and immediate-parent country labels and excluding the
mechanical India-to-foreign level-0 edges, 951/1,650 relations (57.64%) cross
jurisdictions. The equal-parent mean is 58.67%, and the pooled
leave-one-parent-out range is 56.06–61.78%. Claude independently obtains
948/1,650 (57.45%) under a slightly different normalization. This is the most
stable simple structural statistic in the study.

### Supporting 2 — Zero stakes are unusable, and the ownership-depth gradient is composition

All 184 level-0 targets lack a mapping stake. Of 1,650 nonroot edges, 406
(24.61%) record exactly zero. In the 45 preferred rows carrying both mapping
stake and AOC-1 shareholding, all seven zero-stake cases have positive AOC-1
shares—six at 100% and one at 73.94%. Zero therefore cannot safely mean no
ownership.

Among 1,244 positive-stake nonroot edges, the pooled full-ownership rate rises
from 56.37% at reported level 1 to 82.78% at level 2+, a 26.41-point gap. The
equal-parent gap is only 2.33 points; excluding Reliance reduces the pooled gap
to 6.10 points and the equal-parent gap to 0.03 points. With Claude's mean-stake
split (levels 1–2 versus 3+), the raw gap is 15.74 points, the proper parent
fixed-effect coefficient is 4.07 points, and the equal-parent paired difference
is 0.66 points (median 0.20).

The defensible result is a parent/portfolio composition effect. It is not that
ownership mechanically strengthens with depth.

### Supporting 3 — Financial coverage is selected and partly contaminated

Only 560/3,567 preferred target-years are marked ready (15.70%), covering
265/1,834 targets at least once (14.45%). Five parents have no ready target;
Tata Communications supplies 190/560 ready rows. Of the 560 ready rows, 39 fail
the added positive-assets/nonnegative-liabilities gate, only 105 have a
testable valid P&L identity, and 516 lack units.

Claude's stronger duplicate-evidence diagnosis is independently confirmed:

- 51 repeated fiscal-year/currency/units/assets/liabilities/equity signatures
  cover 104/863 parsed preferred rows;
- 33 clusters combine one source URL with different entity names, and all 33
  reuse byte-identical core evidence text;
- 70/560 ready rows are in some repeated numeric signature;
- within the ready-only repeats, 24 different-name clusters cover 49 ready
  rows; and
- the broad union of a repeated-signature flag and the sign gate flags 100/560
  rows, leaving 460 unflagged; the narrower proven-artifact/sign union flags 79
  and leaves 481.

The artifact result applies directly to the 33 established clusters, not
automatically to all 51. No population claim about leverage, profitability,
negative equity, or depth can be supported before re-parsing, unit recovery,
and a selection analysis.

### Supporting 4 — Holding-type names predict observed network role

Claude's new name result reproduces on the independent graph. Of 1,834 target
occurrences, 177 contain `Holding(s)`, `Holdco`, or `Investment(s)`; 64.41%
hold at least one observed child, versus 17.56% of other names, a raw gap of
46.84 points. Parent-scoped entity normalization gives essentially the same
46.67-point gap.

Claude's reported 23.3-point “within parent × country” estimate demeaned only
the outcome and is not a fixed-effect coefficient. Residualizing both outcome
and name flag gives **36.34 points**, with leave-one-parent-out range
34.76–38.33 points across 68 informative parent-country cells and 23 parents.
The flag remains high-precision/low-recall: 64.4% precision and 28.2% recall.
This is a useful methodological proxy, but it needs held-out-parent and
externally verified legal-role validation before general use.

### Supporting 5 — UIN and legal entity are different units

The 186 UINs label 1,834 targets; the median UIN labels two, while the largest
labels 138. Only 184 UINs have an observed level-0 target. These are exact
internal facts. The defensible language is that the file's mapping expands a
UIN into multiple reported entities. “The ODI register sees one entity in ten”
overstates a skewed mean and assumes an external interpretation of UIN scope.

### Supporting 6 — Parent exposure and global company counts differ

Conservative normalization finds 16 repeated global name-country clusters
covering 32 targets. Twelve span parent buckets; four repeat within a parent
and carry two reported parent nodes. These may be joint exposures, aliases,
versions, or genuine multiple paths. Count them once for a global-company
estimand and once per parent for a parent-exposure estimand; do not force a
single denominator.

## 3. Interesting descriptive facts

- **US prominence has a different topology.** The US contains 363/1,830
  parent-scoped entities (19.84%) and remains the largest resident jurisdiction
  under every denominator, yet it supplies only 69/403 unique intermediary
  nodes (17.12%). Its intermediary/entity ratio is below one, unlike the
  Netherlands and Mauritius. Specific US-to-US motif shares remain definition-
  sensitive.
- **Three-country descendant cover.** Preserving the supplied countries of
  unscraped parents, the Netherlands, US, and Mauritius appear strictly
  upstream of 1,140/1,834 target paths (62.16%). The equal-parent union is
  46.65%, the complete-path version is 1,075/1,687 (63.72%), and excluding the
  109 Breakthrough children gives 1,031/1,725 (59.77%). This is an informative
  exposure description, not an independent core result: it repeats ancestors
  by descendant and includes the US, the largest resident market.
- **Small, interpretable motifs.** Twelve downstream India/GIFT targets sit
  below a foreign layer; 13 Marshall Islands entities are leaf vessel SPVs in
  two groups; and four shared consortium vehicles appear through parallel
  parent-specific chains. These are useful case illustrations and denominator
  cautions, not population regularities.
- **Nominally foreign scope is imperfect.** Ten targets are labeled India,
  nine IFSC GIFT City, and one European Union. Geography tables should show the
  sensitivity to excluding these 20 labels.
- **High-degree hubs matter.** Thirty-four observed entities with at least ten
  direct children account for 742/1,834 logical edge relations. Fund vehicles,
  regional holdings, and missing parent nodes must be separated before calling
  all of them subsidiary hubs.

## 4. Rejected or fragile findings

| Candidate claim | Classification | Adjudication |
|---|---|---|
| A fixed list of 19 “financial centres” is upstream of three in five targets | **FRAGILE** | Country-preserving reconstruction gives 1,134/1,834 (61.83%), 57.17% equal-parent, but only 153/403 (37.97%) unique upstream nodes. The maintained list and descendant weighting define the magnitude. |
| Layering does not dilute ownership | **FRAGILE** | Claude counts orphan-terminated chains as complete. Requiring a path to reach the Indian parent leaves 962/1,650 complete all-positive chains (58.30%), not 1,083. Their median is 100% and 51.04% are exactly 100%, but selection on positive stakes is severe and depth-dependent. |
| Netherlands and Mauritius “divide the world” regionally | **FRAGILE** | Several modal destination routes reproduce, but many entity-weighted shares have zero median parent share and fall sharply under equal-parent destination weighting. Acquisition subtrees mechanically repeat routes. |
| Mauritius out, Singapore/GIFT in over time | **UNRESOLVED** | Root counts reproduce and the Mauritius contrast is internally strong, but positions 6–9 of UIN are not documented as registration year in the supplied metadata; the full ODI-register denominator is absent. |
| UIN characters reveal official office and participation type | **UNRESOLVED** | String regularities and correlations reproduce, but official semantics require an RBI form specification. |
| Manufacturing subsidiaries are generally deeper | **REJECTED** | Motherson and Hindalco supply 240/242 deep-manufacturing targets. |
| Deep or gateway entities have different financial health | **REJECTED** | Coverage selection, missing units, invalid signs, repeated extraction, small P&L N, and depth measurement prevent the inference. |
| A fivefold pooled turnover/assets gap identifies holding companies | **FRAGILE** | The gap narrows to about twofold in the USD-only sample on 89 entities and is largely graph validation rather than a paper result. |
| Jersey, Estonia, or Cyprus has extreme general “leverage” | **FRAGILE** | High descendant-per-resident ratios rest on one to five parents and tiny resident counts. |
| Static hierarchy fields reveal restructuring over time | **REJECTED** | Hierarchy fields are fixed within target, dates are incomplete, and early years are parent-specific. |
| A jurisdictional legal shock would detach the measured descendants | **REJECTED as stated** | The dataset establishes upstream topology, not a behavioral or legal counterfactual; alternate paths and corporate adaptation are not observed. |
| Any tax, treaty, regulatory, illegality, or intent narrative | **UNRESOLVED** | It requires external institutional and causal evidence. Frequency or unusual topology is insufficient. |

## 5. Disagreements resolved

| Issue | Competing results or definitions | Resolution |
|---|---|---|
| What is an “entity”? | Claude generally calls all 1,834 targets entities; Codex distinguishes 1,834 occurrences, 1,830 parent-scoped candidates, and 1,818 global candidates. | Use the three labels explicitly. Parent-scoped entities are primary for group architecture; target paths are primary for exposure; global candidates are primary for cross-parent de-duplication. |
| UIN multiplier and roots | Claude: every UIN has one level-0 entity and the register “sees one in ten.” Codex: 184/186 roots, mean 9.86, median 2. | The multiplicity is confirmed; the universal-root claim is false and the rhetoric is rejected. |
| Fixed-list conduit exposure | Claude: 59.3% overall and 7.3% for Dr Reddy's. Codex: 61.83% and 37/41 (90.24%) for Dr Reddy's. | Claude replaced the reported countries of unscraped parents with `(UNOBSERVED)`. All 78 such edges have a supplied country. Preserve country while flagging identity missing; Codex's 61.83% is the defensible path statistic. |
| Missing intermediaries | Claude: 20 raw parent names and 150 affected targets. Codex: 18 normalized names, 78 incident edges, and 147 truncated target paths. | Both describe different normalization/path-link rules. Report 18 normalized missing entities and 147 truncated Codex paths, with raw-name count as sensitivity. Do not synthetically declare paths verified. |
| Depth mismatch | Claude: 237 mismatches and Hindalco graph maximum 12 after orphan re-anchoring. Codex: 236/1,687 complete-path mismatches and Hindalco observed graph maximum 6. | Use the stricter complete-path count. Re-anchoring an orphan using its child's reported level partly imposes agreement. Hindalco is reported 12 / observed graph 6, with only 38/81 complete paths; neither is true depth. |
| Financial coverage fixed effect | Claude: depth nearly vanishes at −0.9 points after outcome-only demeaning. Codex: proper parent FE −2.42 points, LOO −6.62 to −0.77. | A fixed-effect coefficient requires residualizing treatment as well as outcome. Use −2.42 points and describe it as small, selected, and parent-sensitive—not zero. |
| Cross-border edge total | Codex: 951/1,650; Claude: 948/1,650. | The three-edge normalization difference is immaterial. Use 951 after the documented spelling-only country standardization and show 948 as sensitivity. |
| US leaf motif | Exact three-node path: 158, Reliance 61.39%. Collapsing consecutive US hops: 213, Reliance 48.83%. | Both are valid definitions. The motif is descriptive; report the 49–61% Reliance range if used and do not make it a headline. |
| Repeated financial signatures | Codex initially marked 51 clusters for review; Claude called them data artifacts. | Claude's sharpening is accepted for the established subset. All 33 same-URL/different-name clusters reuse identical evidence. The other 18 require separate classification; do not label every repeat erroneous. |
| Single-node chokepoints | Claude target forest: median 43.15% below one node and ten groups above 60%. Normalized graph permits four multiple-parent nodes. | The target result reproduces (43.20% after entity normalization). A stricter normalized-DAG dominator is 41.72%, with eight groups above 60%. Use “largest observed subtree” in the main text, not an unconditional chokepoint counterfactual. |
| Three-jurisdiction cover | Claude: 60.6%; Codex country-preserving paths: 62.16%. | The difference comes largely from retaining reported countries for missing identities and alternative linkage. Use 1,140/1,834 (62.16%) with the 46.65% equal-parent union beside it; classify as descriptive. |
| Name-role within-cell effect | Claude: 23.3 points after demeaning the outcome only. Codex: proper parent-country FE 36.34 points. | Use 36.34 points, with LOO 34.76–38.33. The substantive conclusion is confirmed and stronger, but Claude's estimator label was incorrect. |
| Positive cumulative-ownership chains | Claude: 1,083/1,650 complete-positive chains. Codex: 962. | Claude's traversal stops at an orphan without marking the chain incomplete. Require recursion to the Indian root: 962 is defensible. The no-dilution claim remains fragile. |
| Ownership-depth within-parent gap | Claude: 2.0 points using outcome-only demeaning. Codex: proper parent FE 4.07 for mean edge stake; paired-parent mean 0.66. | Use the proper FE and paired-parent estimates. Both still reject the large 15.74-point pooled interpretation. |

## 6. Remaining disagreements and unresolved boundaries

These cannot be settled from the present file and should remain explicitly
unresolved rather than harmonized by assumption.

1. **Legal identity.** The 1,830/1,818 normalized candidates lack company
   registration numbers and effective dates; some aliases, shared ventures,
   and multiple paths remain ambiguous.
2. **True depth.** Reported levels may count omitted intermediaries, while
   observed graph distance omits them. External ownership diagrams are needed.
3. **Actual dominators.** Missing parent entities and four normalized nodes
   with multiple reported parents prevent a universal forest interpretation.
4. **Control and economic ownership.** The 406 zeros, absent level-0 stakes,
   and time mismatch between mapping and AOC-1 make cumulative control
   unresolved.
5. **UIN semantics.** Fixed string structure is internal evidence; official
   field meanings and vintage remain undocumented here.
6. **Gateway mechanism.** Acquisition inheritance, treaty use, financing,
   governance, operating location, and tax treatment cannot be separated
   without external histories and institutional sources.
7. **Financial artifact extent.** Thirty-three repeated-signature clusters
   have a demonstrated evidence-reuse mechanism; the remaining clusters and
   apparently unique parses still need source-level verification.
8. **Population validity.** The construction and selection of the 28 parent
   buckets are insufficient for inference to all Indian parents or all ODI.

## 7. Recommended final tables

1. **Sample construction and denominator map.** Raw rows, preferred
   target-years, structural targets, parent/global normalized entities, UINs,
   roots, edges, missing nodes, path completion, and financial gates. Include
   definitions in table notes.
2. **Parent architecture table.** One row per parent: normalized entities,
   UINs, jurisdictions, HHI/entropy, root count, leaf share, largest observed
   subtree, normalized-DAG dominator, maximum reported/reconstructed depth,
   path completion, cross-border edge share, and positive-minority share.
3. **Jurisdiction role table.** For frequent jurisdictions: resident entity
   count/share, unique intermediary count/share, holder rate, direct children,
   cross-border children, first-hop gateway count, mean/median descendants,
   affected parents, equal-parent estimate, and LOO range. This should replace
   a single sensational “financial centre” ranking.
4. **Channel and subtree concentration table.** Parent-by-parent modal UIN
   share, first observed foreign-node share, largest observed subtree, strict
   DAG-dominator sensitivity, gateway count, and country breadth.
5. **Depth audit table.** Reported-depth distribution, reconstructed-depth
   distribution on complete paths, mismatch count by parent, level-5+ pooled
   versus equal-parent versus LOO, and parent contributions to deep sectors.
6. **Ownership-data robustness table.** Zero/missing/positive stake counts,
   AOC-1 contradictions, full-ownership gradients under pooled/equal-parent/
   without-Reliance estimands, and positive-chain completion by level.
7. **Financial attrition and contamination table.** Target/source/parsed/ready/
   sign-plausible/P&L-valid counts, parent coverage range, unit missingness,
   repeated signatures, proven evidence-reuse subset, and cleaned-sample bounds.
8. **Cross-agent adjudication appendix.** Every disputed statistic, both
   definitions, the chosen estimand, and the reason. The machine-readable basis
   is `outputs/codex/final/classification_ledger.csv`.

## 8. Recommended final figures

1. **Parent architecture landscape.** Entity count versus country breadth,
   with color for verified/reconstructed depth and bubble outline for largest
   subtree share; label only influential parents.
2. **Jurisdiction role quadrant.** Resident entity share on one axis and unique
   intermediary share or median descendant amplification on the other; bubble
   size is number of parent groups. This makes the US-versus-Netherlands role
   contrast visible without path repetition.
3. **Parent-by-jurisdiction intermediary heatmap.** Within-parent upstream or
   intermediary shares for the major jurisdictions, with one equal-sized row
   per parent and a separate pooled margin.
4. **Channel-concentration dot plot.** For each parent, compare modal UIN share,
   largest observed subtree share, and strict normalized-DAG dominator share.
5. **Reported versus reconstructed depth.** Parent-level maximum and level-5+
   share under both definitions, annotated with path-completion rate.
6. **Data attrition flow.** 3,742 rows to structural entities and from 3,567
   preferred target-years to 560 ready, 521 sign-plausible, 460–481 unflagged
   depending duplicate rule, and 105 P&L-valid rows.

Small-country maps, company-name word clouds, and a policy-timeline overlay
would add visual drama without improving identification and should be omitted.

## 9. Recommended paper structure

1. **Introduction.** State the topology question, contribution, sample limits,
   and non-causal interpretation.
2. **Data and units.** Explain source rows, targets, entity candidates, UINs,
   parents, and why these denominators are not interchangeable.
3. **Entity resolution and graph construction.** Document conservative name-
   country normalization, shared entities, edges, missing parents, complete and
   truncated paths, and the reported/graph depth distinction.
4. **Architectural heterogeneity and concentration.** Present parent-level
   profiles, dominant UIN channels, large subtrees, and DAG sensitivities.
5. **Jurisdiction roles in ownership topology.** Compare resident nodes,
   unique intermediaries, gateway amplification, cross-border edges, and
   descendant exposure with parent balance and LOO checks.
6. **Falsification and negative results.** Show the collapse of deep-sector and
   ownership-depth pooled claims; separate US destination prevalence from
   gateway role.
7. **Measurement limits of stakes and financials.** Treat this as a data audit
   and boundary on inference, not a financial-outcome section.
8. **External interpretation agenda.** Clearly label acquisition, tax, treaty,
   legal, and regulatory mechanisms as hypotheses for future linked-data work.
9. **Conclusion.** The contribution is a reproducible framework for measuring
   foreign ownership topology and avoiding denominator/hierarchy errors.

Appendices should contain the full parent table, duplicate clusters, missing
parent list, path-link rules, all LOO ranges, regex/name validation, financial
evidence audit, and the cross-agent replication ledger.

## 10. Missing robustness work that genuinely matters

Ordered by value to the final study:

1. **Resolve legal entities and the 18 normalized missing parents.** Collect
   registration IDs, former names, countries, and effective dates; rebuild the
   DAG without synthetic re-anchoring.
2. **Classify economic relationship.** Separate controlled subsidiaries,
   associates, joint ventures, investment funds, and portfolio look-through
   companies; repair all zero and missing stakes with dated sources.
3. **Validate UIN metadata externally.** Obtain the RBI specification before
   using year, office, or participation labels.
4. **Link acquisition histories.** Test whether Dutch/Mauritian amplification
   and dominant subtrees were inherited with large acquisitions or subsequently
   constructed.
5. **Establish the sample frame.** Document how the 28 parent buckets were
   chosen and compare them with a broader ODI/parent population.
6. **Run topology-preserving nulls.** For country transitions and destination
   routing, permute countries or edges within parent while preserving country
   margins, depth, and degree sequence.
7. **Validate the name proxy out of sample.** Train on 27 parents, test on the
   held-out parent, and compare against externally coded legal roles.
8. **Re-parse combined financial tables.** Use column-aware extraction, recover
   units/currencies, and manually validate the 33 established artifact clusters
   plus all sign failures before any valuation aggregation.
9. **Recover annual ownership snapshots.** Static hierarchy fields cannot
   support restructuring or policy-event analysis.

### Analyses to drop from the current paper

- sector-depth generalizations;
- broad financial-outcome regressions or jurisdiction financial rankings;
- cumulative-ownership claims from positive-chain selection;
- gateway-vintage/policy claims before UIN validation and a full denominator;
- exact recurring motifs as general evidence;
- tiny-jurisdiction leverage rankings;
- raw-row or unqualified path-count rankings;
- a one-dimensional “complexity score” without transparent components; and
- tax, treaty, legal-shock, or misconduct narratives unsupported by linked
  external evidence.

## 11. Does the evidence support a coherent empirical paper?

**Yes, conditionally.** The present evidence supports a coherent descriptive
and methodological paper about measurement-corrected foreign ownership
topology in 28 sampled Indian parent groups. Five core results survive
independent replication and meaningful denominator, parent-weight, LOO,
duplicate, and graph checks: denominator distortion, multidimensional parent
architecture, dominant channels/subtrees, gateway-jurisdiction roles, and the
parent-driven/mismeasured nature of pooled depth patterns.

It does **not** yet support a causal policy paper, a tax-avoidance paper, a
population estimate for all Indian outward investment, or a financial-health
paper. The strongest publishable posture is skeptical: show what the network
data establish, demonstrate how naive counting produces attractive but false
generalizations, and make the institutional mechanisms an explicit external-
validation agenda.
