# Research ideas and next tests

## Highest-priority extensions

### X-I001 — Validate and complete the ownership graph

Return to the upstream mapping/annual-report ownership diagrams for the 78
unobserved immediate parents and 72 other-level links. Assign stable legal-
entity identifiers and effective dates, then compare reported depth, observed
graph distance, and completed graph distance. This is the prerequisite for any
causal or comparative result involving depth.

### X-I002 — Build a legal-entity resolution layer

For the 16 conservative duplicate clusters and 61 fuzzy candidates, collect
company-registration numbers, incorporation dates, and former names. Store
`entity_id`, `alias_id`, valid-from/to dates, and confidence. Preserve separate
parent-exposure rows for joint ventures while permitting global unique-company
counts.

### X-I003 — Distinguish subsidiaries, joint ventures, associates, and funds

Repair zero stakes and align mapping stake to fiscal year. Classify each edge as
controlled subsidiary, joint control, associate/minority investment, fund
portfolio exposure, or unknown. Re-estimate size, depth, branching, and country
patterns on controlled subsidiaries only. Reliance's shallow venture-fund hubs
make this especially important.

### X-I004 — Gateway-jurisdiction topology paper

Develop three complementary measures for each jurisdiction:

1. unique resident intermediary nodes;
2. cross-border outgoing edges and destination breadth; and
3. descendant-weighted appearances in complete leaf paths.

Estimate parent-balanced and sector-balanced models, remove one parent at a
time, and compare the Netherlands, Mauritius, Singapore, UK, Cyprus, and
Switzerland. Test whether gateway use predicts destination region, chain length,
branching, acquisition origin, or entity role. Institutional interpretation
requires separate legal/tax sources.

### X-I005 — Structural archetype clustering

Cluster parent groups using log entity count, direct-root count, reported and
verified depth, leaf share, outdegree quantiles, country entropy, cross-border
edge share, minority-investment share, and gateway-jurisdiction exposure. With
only 28 parents, use transparent hierarchical clustering and leave-one-feature-
out stability rather than black-box prediction. Interpret candidate archetypes
as chain-heavy, star-holding, geographically dispersed, or portfolio-heavy.

### X-I006 — Explain high-outdegree hubs

Manually classify the 34 observed nodes with at least ten children. Test whether
they are regional holdings, operating parents, acquisition vehicles, or
investment funds. Recompute motif and transition counts after weighting each hub
equally rather than each child equally.

## Financial and selection work

### X-I007 — Source-level financial replication

Audit all 39 ready rows failing sign plausibility, all 19 ready leverage values
above ten, the one P&L-valid absolute ROA above two, and the 51 repeated balance-
sheet signatures. Record PDF page, statement heading, sign convention, unit,
period, and whether liabilities were computed. Create corrected values only with
auditable provenance.

### X-I008 — Unit and currency normalization

Recover reporting units for the 516/560 ready rows where units are blank. Confirm
that assets, liabilities, equity, and P&L fields share the same within-row scale.
Then convert amounts using period-specific FX rates and distinguish stock-date
from flow-period conversion. Until this is done, restrict inference to signs and
ratios.

### X-I009 — Financial missingness bounds

Model `source_found`, `variables_parsed`, `ready`, and `pl_valid` separately at
entity level using parent, country, depth, source type, sector, and panel length.
Report worst-case/Manski-style bounds for negative-equity and loss rates rather
than relying only on observed ready rows. Do not use inverse-probability weights
without positivity and model diagnostics.

### X-I010 — Operating versus holding entities

Use names, sector, turnover, employees if recoverable, and P&L/cash-flow
presence to classify operating and pure-holding entities. Re-test negative
equity, loss, and cash-flow patterns within role. A direct comparison without
role adjustment may conflate financing vehicles with businesses.

## Geography, sector, and time

### X-I011 — Transition models with parent-balanced nulls

For frequent transitions such as Netherlands-to-Germany/Brazil/US and
Mauritius-to-South Africa/Australia/UK, compare observed counts to null networks
that preserve each parent's number of entities, country margins, depth profile,
and outdegree sequence. This distinguishes nontrivial routing motifs from
mechanical country abundance and hubs.

### X-I012 — Sector-depth matched design

The raw deep-manufacturing result is group-driven. Match parents on sector,
entity count, country breadth, and acquisition intensity; then estimate within-
parent differences between manufacturing and other entity roles. More parent
groups per sector are needed for credible generalization.

### X-I013 — Balanced temporal panel

Define a panel of entities with verified statements for at least three
consecutive years and consistent fiscal-year definitions. Analyze within-entity
changes in leverage, equity sign, profitability, and operating cash flow. The
current static hierarchy cannot measure restructuring over time; annual
ownership snapshots would need to be collected separately.

### X-I014 — Clarify foreign/domestic scope

Create an authoritative country-code crosswalk, decide explicitly how IFSC GIFT
City entities enter foreign-structure analysis, and verify the ten India-labeled
downstream entities. Run all geography results with and without the 20 domestic,
special-zone, or regional-label targets.

## Negative controls and falsification

- Reproduce every jurisdiction ranking with raw rows, unique targets,
  parent-scoped entities, global entities, leaves only, path appearances, and
  equal-parent weights.
- For each headline statistic, report the dominant parent's share and the full
  leave-one-parent-out range.
- Randomize country labels within parent-depth cells while preserving graph
  topology to test whether path motifs exceed mechanical expectations.
- Randomize edges within parent while preserving in/outdegree and country
  margins to test gateway measures.
- Compare name-normalized and exact-name results; treat fuzzy resolution as a
  sensitivity bound, not truth.
- Repeat depth analyses using reported level, observed graph distance, and
  externally completed distance.
- Treat blank/zero stake under alternative assumptions: unknown, literal zero,
  and externally recovered values.
- Use source type and parent as negative-control predictors of financial
  outcomes; large coefficients would indicate collection-selection artifacts.
