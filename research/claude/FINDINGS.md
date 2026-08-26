# Candidate findings — Claude, blind discovery increment 1

**Unit of observation throughout:** the scraped foreign entity (`target_id`),
1,834 entities, 186 RBI ODI registrations (`uin`), 28 Indian parent buckets,
122 jurisdictions. Depth is `level` unless stated; `depth_graph` is the
robustness counterpart. Read `DATA_AUDIT.md` before using any number here.

**Language.** "Unusual", "concentrated", "intermediary-heavy" and
"worthy of further investigation" are descriptive. Nothing in this file
supports any inference about legality, tax treatment or conduct. Holding
companies in financial centres are a standard and lawful feature of
multinational corporate finance; this document only measures where they sit.

Ranking below is by (surprise × robustness × economic relevance × paper value).
Codes are stable identifiers for later increments.

---

## Tier 1 — strongest

### C-F001 · The ODI register sees one entity in ten
**Result.** 186 registered outward investments expand into 1,834 foreign
entities. Every UIN has exactly one directly held (level-0) foreign entity;
those 184 entities carry **1,500 further entities beneath them**, a mean of
8.15 downstream entities per registered first hop. **47.5%** of all entities
sit at level 2 or deeper; 18.6% at level 5 or deeper; the deepest chains reach
level 12.
**Denominator.** Numerator = entities with `level >= 2` (871); denominator =
all 1,834 entities. Alternative denominator: entities per UIN, mean 9.86,
**median 2**, because 89 of 186 UINs (47.8%) resolve to a single entity.
**Why it matters.** ODI statistics, and any OFBV valuation anchored on the
registered entity, measure the top of a structure whose mass sits below it.
The gap is not uniform: it is a property of the first-hop jurisdiction (C-F002)
and of the group (C-F004).
**Robustness.** Ten UINs account for 49.2% of all entities, so the *mean*
multiplier is a concentrated statistic; the median (2) is the conservative
number and still implies the register misses at least half the structure for
half of all investments. Excluding the 92 entities under participation-type
(P) UINs leaves 1,742 entities over 167 UINs (10.4 each).
**Mundane explanation.** The mapping traces subsidiaries from parent
disclosures, so a UIN accumulates every entity the parent later lists under
that chain. Older registrations mechanically accumulate more (see C-F010).
**Falsification.** If entity counts per UIN were flat in registration age
after conditioning on parent, the "register sees the top only" reading would
weaken. Vintage evidence in C-F010 shows they are not flat.
**Figure.** `fig01_depth_and_uin_concentration.png`. **Table.** `uin_summary`,
`hierarchy_shape_summary`.
**Research value: 5/5.**

### C-F002 · Where the first foreign hop lands determines how much structure follows
**Result.** Downstream entities per directly held foreign entity, by that
entity's jurisdiction (gateways with n ≥ 3):

| First-hop jurisdiction | gateways | parents | mean descendants | median |
|---|---|---|---|---|
| Netherlands | 13 | 12 | **33.5** | 11.0 |
| Cyprus | 3 | 3 | 29.0 | 11.0 |
| Mauritius | 17 | 11 | **17.8** | 5.0 |
| Switzerland | 3 | 3 | 13.3 | 9.0 |
| United States | 28 | 12 | 9.9 | 1.5 |
| United Kingdom | 13 | 10 | 8.9 | 2.0 |
| Singapore | 18 | 12 | 7.4 | 3.5 |
| United Arab Emirates | 9 | 6 | 2.3 | 1.0 |
| Russia, Italy, Australia, Colombia, Myanmar | 3–6 each | 2 each | **0.0** | 0.0 |

A Dutch first hop carries seven times the median structure of an American one,
and thirty-three times an Emirati one, even though the US supplies twice as
many gateways as the Netherlands.
**Denominator.** Numerator = `n_descendants` summed over level-0 entities in
the jurisdiction; denominator = count of those level-0 entities. Median
descendants is the single-parent-robust alternative.
**Robustness — leave-one-parent-out.** Dropping any one parent:
Netherlands falls only to 19.8 (median 10.0), Mauritius to 12.4 (median 4.5),
Singapore to 6.0, US to 7.2 (median 1.0). Cyprus is fragile (29.0 → 5.5 when
Wipro is dropped; only 3 gateways) and should be quoted with the caveat.
The Netherlands result is supported by 13 gateways across **12 different
parents**, so it is not one group's architecture.
**Mundane explanation.** Dutch and Mauritian holding companies are the
conventional vehicle for consolidating an *acquired* foreign group, so the
descendants may simply be the acquired target's pre-existing structure
inherited wholesale (Novelis under A V Minerals, SMRP BV under Motherson).
That is a genuine explanation of *why*, not a reason the fact is not real.
**Falsification.** If the amplification is purely acquisition-driven, then
restricting to gateways with no single subtree larger than half the total
should collapse the Netherlands–US gap. Not yet run.
**Figure.** `fig02_gateway_amplification.png`. **Tables.**
`gateway_amplification`, `gateway_amplification_leave_one_out`.
**Research value: 5/5.**

### C-F003 · Three in five foreign entities are held *through* a financial-centre jurisdiction, and groups differ from 0% to 97%
**Result.** Using a fixed list of 19 holding/financial-centre jurisdictions
(Netherlands, Mauritius, Singapore, Cyprus, Luxembourg, Jersey, Guernsey,
Isle of Man, Cayman, BVI, Bermuda, Barbados, Panama, Marshall Islands,
GIFT City IFSC, Switzerland, Ireland, Hong Kong, UAE), **59.3%** of the 1,834
entities have at least one such jurisdiction strictly *above* them in the
ownership path. Across parents the share runs from **0%** (Biocon Biologics,
Reliance Energy Generation & Distribution) and **11.2%** (Reliance Industries)
to **97.2%** (Jindal Steel & Power), 96.3% (UPL), 94.6% (Suzlon) and 93.3%
(Bharti Airtel).
**Denominator.** Numerator = entities with an upstream centre; denominator =
all entities. The entity's *own* location is excluded so that an operating
company in Singapore does not count itself.
**Robustness.** Excluding participation-type UINs: 62.2%. Excluding stakes
below 10%: 59.9% (n = 1,353). Excluding the largest parent (Motherson):
54.8%. **Parent-weighted** (mean of the 28 parent shares, so every group
counts once): **53.7%**. The result is stable across all four.
**Why it matters.** The 86-percentage-point spread across groups of broadly
similar size is the interesting object: it is a firm-level choice variable,
not an industry constant. Airtel (93%) and Wipro (39%) are both large
services multinationals; Jindal (97%) and JSW Steel (33%) are both steel.
**Mundane explanation.** Treaty networks, investor-protection agreements,
financing and joint-venture governance all rationally push holding companies
into these jurisdictions; sector and the location of acquisitions matter.
**Falsification.** Regress the parent share on sector, number of
acquisitions, and destination mix; if little variance survives, the
"firm-level choice" reading weakens.
**Figure.** `fig05_conduit_exposure_by_parent.png`. **Tables.**
`conduit_exposure_by_parent`, `conduit_exposure_robustness`.
**Research value: 5/5.**

### C-F004 · Comparable footprints, opposite architectures
**Result.** Breadth and depth are close to independent design choices.
Reliance Industries records **196 entities but a maximum depth of 2** and a
mean depth of 0.93. Hindalco records **81 entities and a maximum depth of 12**,
mean 6.27 — the deepest structure in the file by a wide margin. Wipro (213
entities, depth 8) and Motherson (309, depth 8) are both wide and deep;
ONGC Videsh (41 entities, depth 2, 24 UINs) is wide *across registrations*
rather than within them.
**Denominator.** Parent-level table, 28 observations, one row per parent
bucket.
**Robustness.** Correlation of `log(n_entities)` with `max_depth` is 0.63 and
with `mean_depth` 0.50 — positive but far from determinative; the residual
spread at any given size is 6–10 levels. Correlation with `n_countries` is
0.79, so *breadth of geography* tracks size much more closely than depth does.
**Mundane explanation — important, and only partly supported.** `level` is
only as deep as the parent's own disclosures trace the chain, so measured
depth could be a disclosure artefact. The two headline cases are consistent
with that story — Reliance has the lowest source-location rate in the file
(15.3%) and the flattest structure; Hindalco has 100% and the deepest. But
**across all 28 parents the correlation between `max_depth` and
`pct_source_found` is only 0.065**, i.e. essentially zero: Mahindra, Tata
Communications, Piramal, ICICI and Biocon all have 100% source location and
maximum depths of 1–4. The disclosure channel therefore does not explain the
cross-sectional spread, though it may still explain the two extremes. Read
this as "measured architecture" and verify the extremes against an external
structural source before treating depth as a firm characteristic.
**Falsification.** Compare measured depth against an independent structural
source (Orbis, or the parents' own AOC-1 nesting) for a handful of groups.
**Figure.** `fig04_breadth_vs_depth.png`. **Table.** `parent_summary`,
`parent_complexity_correlations`.
**Research value: 4/5 (5/5 if the disclosure channel can be closed).**

---

## Tier 2 — strong, with clear caveats

### C-F005 · The network is layering, not branching, and a handful of nodes carry it
**Result.** 78.0% of entities (1,430) hold nothing at all. Of the 404 that
hold something, **exactly half (201) hold precisely one entity** — vertical
holding strings rather than operational fan-out. At the same time the **20
largest holding nodes carry 37.1% of the 1,569 ownership links that originate
from an observed foreign entity** (the remaining 285 of the 1,854 edges
originate from an Indian parent root or from an unobserved intermediary). The single
largest is `JINDAL STEEL AND POWER MAURITIUS LTD`, which directly holds **81**
entities — 75% of its group's entire foreign network hangs off one Mauritian
node.
**Denominator.** Out-degree computed on the reconstructed forest; leaves and
hubs are shares of all 1,834 entities.
**Robustness / caution.** Two of the top three hubs are **not subsidiaries**:
`BREAKTHROUGH ENERGY VENTURES LLC` (67) and `BREAKTHROUGH ENERGY VENTURES II
L.P` (42) are venture funds whose "children" are portfolio companies held at
stakes of 0.0001% or recorded as zero. Excluding entities held at under 10%
removes 481 entities and *raises* the top-20 edge share to 41.3% of the
remaining entity-origin links, because the two fund vehicles drop out while
the genuine holding hubs do not. The Jindal, Wipro, Sun Pharma, Airtel and Motherson hubs
are unaffected.
**Mundane explanation.** A single acquisition holding company naturally
acquires a whole target group at once.
**Figure.** `fig07_branching_concentration.png`. **Table.**
`top_holding_nodes`, `branching_distribution`.
**Research value: 4/5.**

### C-F006 · Jurisdictions sort cleanly into entry points and terminals
**Result.** Ranking the 25 jurisdictions with ≥15 entities by the mean level
of entities located there produces an almost perfect separation:

- **Entry points** — Singapore 0.87, Cyprus 1.00, Mauritius 1.21, Israel 1.22,
  UAE 1.68, Netherlands 1.86. High pass-through: 54% of Dutch entities,
  44% of Mauritian and 40% of Cypriot entities hold at least one subsidiary.
- **Terminals** — France 5.53, China 4.97, Poland 4.19, Spain 3.93,
  Mexico 3.82. Pass-through near zero: 3.0% in Mexico, 4.7% in South Africa,
  8.2% in China; Thailand, Russia, Malaysia and the Philippines are 100% leaf.

Descendants per entity spans three orders of magnitude: Jersey 32.0 (n=2),
Estonia 25.0 (n=2), Luxembourg 9.2, Netherlands 7.8, Cyprus 7.7, Mauritius
5.8, versus United States 1.5, Israel 0.7, Mexico 0.03.
**Denominator.** All entities located in the jurisdiction; jurisdictions with
fewer than 8–15 entities are reported but flagged.
**Robustness.** The Dutch, Mauritian, Singaporean and US cells rest on 13–23
different parents each. Jersey (2 entities), Estonia (2) and Cyprus (15,
5 parents) are thin and should be quoted with n.
**Mundane explanation.** This is close to the definition of a holding company
location, so the pattern is expected; the contribution is that it is
*measured* on Indian outward FDI rather than assumed, and that the ordering
(Singapore ahead of Mauritius ahead of the Netherlands on entry, Netherlands
far ahead on amplification) is not obvious ex ante.
**Figure.** `fig03_jurisdiction_roles.png`. **Table.** `jurisdiction_roles`.
**Research value: 4/5.**

### C-F007 · A small number of jurisdiction sequences is used over and over
**Result.** The 1,834 entities travel only **610 distinct collapsed
jurisdiction sequences**, and the top 25 cover roughly 40% of entities. The
recurring multi-hop motifs are specific and repeated:

| Motif | entities | group |
|---|---|---|
| India → Netherlands → Jersey (66) → Cyprus (25) → Hungary (22) → Australia (14) | 66 at the Jersey hop | Motherson (SMR mirrors) |
| India → United Kingdom → Estonia → Finland → Luxembourg → Mexico | 11 | Motherson (PKC) |
| India → Cyprus → Luxembourg → … → Belgium | 20 | Wipro (Capco) |
| India → Mauritius → South Africa / Australia / Namibia / Botswana | 21 / 18 / 13 / 7 | Jindal, Vedanta |
| India → Netherlands → Germany | 54 | Motherson, Hindalco |
| India → Singapore → Marshall Islands | 9 | Reliance |

**67.0%** of entities sit on a path spanning three or more jurisdictions
(including India) and **22.5%** span four or more.
**Denominator.** Collapsed paths (consecutive same-country hops merged) over
all 1,834 entities.
**Robustness.** Motifs are by construction group-specific; the finding is
about *repetition within a group*, i.e. that one template is replicated across
many operating subsidiaries, not that different groups converge on the same
chain. The Mauritius → Southern Africa motif is the one that spans parents.
**Mundane explanation.** Acquiring a group with an existing multi-country
holding stack reproduces that stack across all its operating units.
**Table.** `jurisdiction_path_motifs`, `jurisdiction_trigrams`.
**Research value: 4/5.**

### C-F008 · The gateway mix has shifted: Mauritius out, Singapore and GIFT City in
**Result.** Using the registration year decoded from the UIN (C-F009), the
jurisdiction of newly registered first-hop entities:

| Vintage | UINs | Mauritius | Netherlands | Singapore | GIFT City IFSC |
|---|---|---|---|---|---|
| ≤2004 | 16 | 18.8% | 12.5% | 6.2% | 0% |
| 2005–10 | 39 | 20.5% | 10.3% | 5.1% | 0% |
| 2011–15 | 30 | 6.7% | 13.3% | 6.7% | 0% |
| 2016–20 | 54 | **1.9%** | 3.7% | **14.8%** | 3.7% |
| 2021–25 | 45 | 6.7% | 2.2% | 11.1% | **11.1%** |

Mauritius supplied roughly one in five new gateways before 2011 and one in
fifty in 2016–20. GIFT City appears for the first time in 2016–20 and is
5 of 45 new gateways in 2021–25.
**Denominator.** 184 level-0 entities, split by decoded UIN year; cell counts
are small (1–8 entities) and are reported in `gateway_vintage_counts`.
**Robustness — weak.** With 16–54 UINs per bin, no single cell is precisely
estimated; the Mauritius decline (3, 8, 2, 1, 3 gateways) and the GIFT City
arrival (0, 0, 0, 2, 5) are the two movements large enough to read. Both
survive dropping any single parent because no parent has more than 3 Mauritian
level-0 entities.
**Interpretation.** The timing coincides with the 2016 India–Mauritius treaty
protocol and the establishment of the GIFT City IFSC, but this file contains
no policy variable and cannot identify the mechanism. Stated as a described
coincidence only.
**Figure.** `fig06_gateway_vintage_shift.png`. **Tables.**
`gateway_vintage_shares`, `gateway_vintage_counts`.
**Research value: 4/5 (5/5 if merged with the full ODI register).**

### C-F009 · The RBI ODI UIN is a structured string, and the structure is recoverable
**Result.** All 186 UINs parse as
`[2-char RBI regional office][1-char investment type][2-char series][4-digit year][4-digit serial]`.
The investment-type character orders exactly as wholly owned > joint venture >
participating interest on observed stakes:

| Character | UINs | mean stake of level-1 entities | % at exactly 100 | entities per UIN |
|---|---|---|---|---|
| W | 117 | 82.8 | 65.8 | 11.6 |
| J | 50 | 60.1 | 50.0 | 7.8 |
| P | 19 | **13.6** | **1.6** | 4.8 |

The office code matches the parent's home region (PJ → Vedanta/Goa only,
HY → Dr Reddy's only, AH → Adani only). The year field is never later than
the first observed statement for 92% of dated UINs.
**Why it matters.** This is a methodological result: it lets any ODI dataset
be split by investment type, registering office and vintage without a
separate crosswalk, and it is what makes C-F008 possible.
**Caveat.** This is an inference from three consistency checks, not
documentation. It should be confirmed against RBI's ODI form definitions
before being relied on in a paper.
**Table.** `uin_format_checks`, `uin_investment_type_evidence`,
`uin_participation_type_level0_names`, `uin_office_by_parent`, `uin_year_checks`.
**Research value: 4/5.**

---

## Tier 3 — interesting, smaller or more fragile

### C-F010 · Ownership chains that return to India
**Result.** 19 entities in the file are located in India (10) or GIFT City
IFSC (9). **12 of them sit at level ≥ 1**, i.e. they are Indian-registered
companies owned by their Indian parent *through* a foreign chain. Paths
include `INDIA > NETHERLANDS > JERSEY > CYPRUS > INDIA` (level 5,
`SMR AUTOMOTIVE SYSTEMS INDIA LIMITED`, stake 51%),
`INDIA > NETHERLANDS > NETHERLANDS > NETHERLANDS > INDIA` (level 5),
`INDIA > IFSC GIFT CITY > SINGAPORE > INDIA` and
`INDIA > UNITED STATES > INDIA` (Trifacta, Sensehawk — the Indian arms of
acquired US startups).
**Denominator.** 12 of 1,834 entities (0.65%).
**Mundane explanation.** Two clean and distinct mechanisms are visible in the
data and account for most cases: (i) acquiring a foreign company that already
owned an Indian subsidiary (Trifacta, Sensehawk, VAKT, Yachiyo); (ii) GIFT City
IFSC exchange infrastructure held in a domestic stack (ICICI's India
International Exchange group). Only the Motherson and Airtel cases are
holding structures that route Indian operations through Europe.
**Table.** `round_trip_entities`.
**Research value: 3/5 on its own; 4/5 as a component of a round-tripping paper.**

### C-F011 · Single-asset SPV jurisdictions: the Marshall Islands pattern
**Result.** All 13 Marshall Islands entities sit at **level 1**, all are
**leaves**, all have zero descendants, and all belong to two groups: four
Jindal vessels (`CORE AMBITION`, `CORE FORTE`, `CORE INTEGRITY`, `CORE VISION`)
held through `JINDAL STEEL AND POWER MAURITIUS LTD`, and nine Reliance ethane
carriers (`ETHANE CORAL`, `ETHANE CRYSTAL`, …) held through
`RELIANCE ETHANE HOLDING PTE LTD` in Singapore. The Reliance vessels split
cleanly into wholly owned (100%) and 50/50 joint ventures, and the two groups
carry different sector labels accordingly.
**Why it is interesting.** A jurisdiction used *exclusively* for
single-asset isolation one hop below a holding company, never as a holding
node itself — the mirror image of the Netherlands. It is a clean, visible
instance of the "one ship, one company" convention appearing inside Indian
ODI data.
**Denominator.** 13 of 1,834 entities; 2 of 28 parents.
**Table.** in `jurisdiction_roles`; entity list reproducible from
`entity.parquet`.
**Research value: 3/5.**

### C-F012 · Two state-owned parents built mirror-image conduit chains into the same joint ventures
**Result.** `INDOIL NETHERLANDS B.V.` is reached by Indian Oil through
`IOC SWEEDEN AB` and by Oil India through `OIL INDIA SWEDEN AB` — two
separately incorporated Swedish intermediaries doing the same job for two
different Indian state-owned parents into the same Dutch vehicle. Likewise
`TAAS INDIA PTE LTD`, `URJA BHARAT PTE LTD` and `VANKOR INDIA PTE LTD`
(Singapore) each sit under both Bharat Petroresources (via
`BPRL INTERNATIONAL SINGAPORE PTE LTD.`) and Indian Oil (via
`IOCL SINGAPORE PTE LTD`), with a separate UIN registered by each parent.
**Why it is interesting.** Consortium investment by Indian public-sector oil
companies is implemented as *parallel private chains*, not a shared vehicle.
Each parent registers its own UIN and builds its own intermediary, so the
same underlying asset is counted twice in any UIN-level or entity-level
aggregate that pools parents.
**Denominator.** 4 shared entities, 8 targets, 4 parents.
**Robustness.** This is a documented feature of the data (`shared_uin`,
`attribution_rule`), not an artefact of my reconstruction.
**Research value: 3/5 (4/5 as a caution for any aggregate ODI statistic).**

### C-F013 · Intermediary entities look financially like holding companies
**Result.** Among entities with both turnover and total assets parsed, the
median turnover-to-assets ratio is **0.096 for entities that hold at least one
subsidiary (n = 47)** versus **0.486 for entities that hold none (n = 187)**.
Exactly-zero turnover is reported for 10.2% of leaves and 2.1% of holders.
**Robustness — this is the weak point.** Restricting to a single currency
(USD, the largest subsample) the gap narrows sharply: 0.119 (holders, n = 24)
versus 0.230 (leaves, n = 65). The five-fold gap in the pooled sample is
therefore partly a currency- and unit-mixing artefact; the two-fold gap in the
USD sample is the defensible number, on 89 entities.
**Mundane explanation.** Holding companies have no operations by construction;
this is a validation of the graph, not a discovery.
**Table.** `holding_vs_operating_financial_signature`,
`holding_vs_operating_signature_usd`.
**Research value: 2/5 as a finding, 4/5 as a *validation* that the
reconstructed graph identifies real holding companies.**

### C-F014 · Only one foreign entity in seven will ever support a book-value valuation, and the shortfall is a group-level, not a depth-level, phenomenon
**Result.** Of 1,834 entities, 847 (46.2%) have any located source, 444
(24.2%) have a parsed balance sheet, and **265 (14.4%) are valuation-ready in
at least one year**. Raw coverage falls with depth (16.5% at levels 0–2 versus
9.9% at level 3+) and varies enormously by jurisdiction (South Africa 39.5%,
Netherlands 23.0%, United States 7.4%, Israel 2.4%) and by parent (Tata
Communications 92.0%, Dr Reddy's 48.8%, JSW Steel, Biocon, ICICI and Oil India
all 0.0%).
**The falsification result — reported because it matters.** Within parent, the
depth gradient nearly vanishes: demeaning by parent, deep entities are only
**0.9 percentage points** below their group average, against a raw gap of
6.6 points. Entities that hold subsidiaries are +5.0 points within parent.
**The apparent "deep subsidiaries are harder to see" story is a between-group
composition effect, not a depth effect.**
**Why it matters anyway.** Any OFBV or IRR exercise built on this panel will
be estimated on a 14.4% subsample selected almost entirely on *which group
you are looking at*. That is a first-order selection problem for the parent
project and should be handled with parent fixed effects or explicit
reweighting.
**Figure.** `fig08_coverage_by_level.png`. **Tables.** `coverage_summary`,
`coverage_by_level`, `coverage_by_country`, `coverage_by_parent`,
`coverage_selection_check`.
**Research value: 4/5 for the parent project; 2/5 as a standalone fact.**

### C-F015 · Reliance's apparent breadth is a venture portfolio, not a subsidiary network
**Result.** 109 of Reliance Industries' 196 entities (55.6%) are children of
two vehicles, `BREAKTHROUGH ENERGY VENTURES LLC` (67) and
`BREAKTHROUGH ENERGY VENTURES II L.P` (42). Their recorded stakes are 0.0001%
(14 entities), 0 (7) or small double digits. The first is registered under a
participation-type (P) UIN, the second under a joint-venture (J) UIN.
Removing the 109 fund-portfolio companies takes Reliance from 196 entities
(third-largest in the file) to **87** (fifth, behind Motherson 309, Wipro 213,
Airtel 134 and Jindal 108). Its conduit-exposure share also moves, from 11.2%
to 25.3%, because the US portfolio companies were held directly and diluted
the denominator. Its maximum depth is unchanged at 2.
**Why it matters.** Any entity-count-based measure of corporate complexity
must be control-weighted. Applying a 10% stake floor removes 481 entities
(26.2%) file-wide.
**Related data problem.** `stake == 0` is a missing code, not a zero share
(406 entities, 33.5% of all level-1 entities), so a naive stake filter also
deletes real subsidiaries. Both filters are reported side by side in
`parent_denominator_check`.
**Research value: 3/5 as a finding, 5/5 as a denominator rule for everything
else in this project.**

### C-F016 · Twenty intermediaries in these chains are named but never observed
**Result.** 20 companies appear as the `immediate_parent` of a scraped entity
but never as a scraped entity themselves; they are the top of subtrees
containing **150 entities (8.2% of the file)**. The largest is
`DR REDDY'S LABORATORIES SA` with 29 direct children; others include
`RIZING LLC`, `INFOSYS GERMANY GMBH`, `NOVELIS HOLDINGS INC.`,
`TATA CHEMICALS (SODA ASH) PARTNERS`, `MOZ LNG 1 HOLDING COMPANY LTD`.
**Why it matters.** These are structural holes: for 150 entities the
jurisdiction of one node on the ownership path is unknown, so every
path-composition statistic (C-F003, C-F007) treats one hop as `(UNOBSERVED)`.
The affected entities are flagged (`path_has_unobserved == 1`), and the
headline conduit share is computed both ways.
**Table.** `unobserved_intermediaries`.
**Research value: 2/5 as a finding, 4/5 as a data-quality constraint.**

### C-F017 · Reported level and the immediate-parent chain disagree, and almost entirely in one group
**Result.** `level` and reconstructed `depth_graph` agree for 87.1% of
entities. All 237 disagreements have `depth_graph < level`, and 208 (88%) are
Samvardhana Motherson. The mechanism is cross-UIN linking: within a group, an
entity's recorded `immediate_parent` may be registered under a different UIN
at a much shallower level, short-circuiting the chain that `level` was
measured along.
**Why it matters.** Any depth-based result must state which measure it uses.
Motherson's maximum depth is 8 on the graph measure and 12 on the reported
measure; Hindalco's is 12 on both, which is why C-F004's headline uses
Hindalco rather than Motherson.
**Research value: 1/5 as a finding, 5/5 as a methodological requirement.**

---

## Ranked shortlist

| Rank | Code | Surprise | Robustness | Economic relevance | Paper value |
|---|---|---|---|---|---|
| 1 | C-F002 gateway amplification | high | high (LOO-checked) | high | high |
| 2 | C-F003 conduit exposure spread | high | high (4 robustness cuts) | high | high |
| 3 | C-F001 ODI register multiplier | high | medium (skewed) | high | high |
| 4 | C-F004 breadth vs depth | high | medium (disclosure channel) | high | medium-high |
| 5 | C-F008 vintage shift in gateways | high | low-medium (small n) | high | high if merged |
| 6 | C-F005 layering and hub concentration | medium-high | high | medium | medium-high |
| 7 | C-F009 UIN decoding | medium | high | medium | medium (methods) |
| 8 | C-F006 jurisdiction roles | medium | high | medium | medium |
| 9 | C-F007 recurring motifs | medium-high | medium | medium | medium |
| 10 | C-F015 control-weighted denominators | medium | high | medium | medium (methods) |
| 11 | C-F014 coverage selection | medium | high | high for this project | medium |
| 12 | C-F010 round-trip chains | high | low (n = 12) | high | medium |
| 13 | C-F012 mirrored PSU consortium chains | high | medium | medium | medium |
| 14 | C-F011 Marshall Islands SPVs | medium-high | medium (n = 13) | low-medium | low-medium |
| 15 | C-F013 holding-company financials | low | low-medium | low | low (validation) |

---

# Increment 2 additions (C-F018 to C-F022)

Added after reviewing Codex commit `bb67b93`. These are new lines of enquiry
that neither branch had investigated. All adopt the corrected zero-stake rule
from `research/reviews/X-F010.md`: `stake == 0` is a missing code, so a
minority filter applies only to entities with a strictly positive recorded
stake.

Code: `src/claude/09_analyse_chokepoints.py`,
`src/claude/10_analyse_names_and_stakes.py`,
`src/claude/11_make_figures_increment2.py`.

## C-F018 · Half of all large Indian groups route more than 43% of their entire foreign network through a single company

**Result.** The reconstructed ownership graph is a forest, so every ancestor
of an entity is a dominator of it: removing any node on the path detaches
everything below. For the 24 groups with at least 15 entities, the share of the
group's foreign network sitting below its single largest node has a **median of
43.2%**, and ten groups exceed 60% (the table lists those ten plus Sun
Pharmaceutical, the next largest):

| Group | entities | % below one node | that node | jurisdiction |
|---|---|---|---|---|
| Jindal Steel & Power | 108 | **98.1** | Jindal Steel and Power Mauritius Ltd | Mauritius |
| UPL | 81 | **97.5** | UPL Corporation Ltd | Mauritius |
| Tata Steel | 27 | **96.2** | T Steel Holdings Pte. Ltd. | Singapore |
| Biocon Biologics | 23 | **95.5** | Biocon Biologics UK Limited | United Kingdom |
| Glenmark Pharmaceuticals | 38 | 81.1 | Glenmark Holdings SA | Switzerland |
| Bharti Airtel | 134 | 79.7 | Bharti Airtel International Netherlands B.V | Netherlands |
| Tata Communications | 50 | 67.3 | Tata Communications International Pte Ltd | Singapore |
| Samvardhana Motherson | 309 | 64.3 | Samvardhana Motherson Automotive Systems Group B.V. | Netherlands |
| Suzlon Energy | 37 | 63.9 | Suzlon Energy Limited | Mauritius |
| Bharat Petroresources | 20 | 63.2 | BPRL International BV | Netherlands |
| Sun Pharmaceutical | 75 | 54.1 | Sun Pharma (Netherlands) B.V | Netherlands |

At the other end, Dr Reddy's routes only 7.5% through its largest node.
**18 of the 24 chokepoint companies sit in a holding jurisdiction** (Mauritius
5, Netherlands 5, Singapore 5, Switzerland, Cyprus, Channel Islands).

**Denominator.** Numerator = the largest `n_descendants` in the group;
denominator = the group's entities minus the chokepoint itself.

**Is it mechanical?** This is the obvious objection: a group with one
registered outward investment has one gateway and is concentrated by
construction (Jindal has exactly one UIN). It does not survive as an
explanation. The correlation between the number of level-0 gateways and the
share below one node is **−0.351**, and among the 16 groups with five or more
gateways the median is still **41.8%**. Bharti Airtel has six gateways and
still routes 79.7% through one Dutch company; Motherson has nine and routes
64.3% through one; Glenmark has eight and routes 81.1%.

**Robustness.** Uses only the graph and is immune to the stake and financial
data problems. Unaffected by the venture-fund denominator issue except for
Reliance itself, whose chokepoint *is* a fund vehicle (34.4%).

**Mundane explanation.** A single acquisition or regional holding vehicle is
the natural way to consolidate a foreign business, and a group that made one
big foreign acquisition will look like this by construction. The finding is
that this is the *typical* architecture rather than the exception, and that the
chokepoint is overwhelmingly located in a holding jurisdiction rather than in
the operating market.

**Falsification.** If the chokepoint were simply "the biggest acquisition",
its jurisdiction should match the acquisition's operating country. It does not:
18 of 24 sit in a jurisdiction with almost no operating activity in the data.

**Figure.** `fig09_single_node_chokepoints.png`. **Tables.**
`chokepoint_single_node`, `chokepoint_summary`.
**Research value: 5/5.**

## C-F019 · Three jurisdictions sit above 61% of all Indian foreign subsidiaries

**Result.** Because the graph is a forest, "how many entities would be detached
if jurisdiction *j* were removed" is exactly "how many entities have *j*
strictly upstream". A greedy cover over jurisdictions:

| Step | Jurisdiction | newly detached | cumulative % of 1,834 |
|---|---|---|---|
| 1 | Netherlands | 538 | 29.3 |
| 2 | United States | 316 | 46.6 |
| 3 | Mauritius | 258 | **60.6** |
| 4 | United Kingdom | 129 | 67.7 |
| 5 | Singapore | 102 | 73.2 |
| 6 | Cyprus | 75 | 77.3 |

Per resident entity, the leverage differs by more than an order of magnitude:
Jersey 32.0 entities held below per resident entity, Estonia 23.5, Cyprus 7.6,
Mauritius 5.4, Netherlands 4.8 — against **0.98 for the United States**, which
has the most entities of any jurisdiction and almost no leverage.

**Robustness.** Netherlands: pooled 29.3%, equal-parent 20.8%, leave-one-parent-out
22.3%–32.8%, affecting 16 of 28 groups. Mauritius: 16.7% pooled, 14.6%
equal-parent, LOO 11.7%–19.1%, 10 groups. United States: 19.4% / 14.1% /
14.4%–22.1%, 16 groups. Removing the two venture-fund portfolios reorders the
first three (Netherlands, Mauritius, United States) and gives 58.1% at step 3
on 1,725 entities — the substance is unchanged.

**Fragile cells, stated as such.** Jersey (pooled 3.5% but equal-parent 0.8%,
2 parents), Estonia (1 parent) and Cyprus (5 parents) have high leverage on
very few groups. Quote them with n.

**Why it matters.** It converts an impressionistic claim about conduit
jurisdictions into a covering number: a shock to Dutch holding-company law
would sit above 29% of these networks; three jurisdictions span 61%. This is a
concentration-of-exposure statement about Indian outward FDI that does not
require any assumption about intent.

**Mundane explanation.** Regional holding structures cluster where corporate
law, treaty networks and financing infrastructure are convenient; the same
three jurisdictions would appear for most multinationals.

**Figure.** `fig10_jurisdiction_criticality.png`. **Tables.**
`jurisdiction_criticality`, `jurisdiction_greedy_cover`.
**Research value: 5/5.**

## C-F020 · A company's name predicts its position in the ownership chain, even within parent and country

**Result.** Entities whose name contains *Holding(s)*, *Holdco*, *Investment(s)*
hold at least one subsidiary **64.4% of the time**, against **17.5%** for all
other entities — a raw gap of **46.9 percentage points** on 177 entities across
24 of the 28 groups. The signal survives the two obvious confounds: demeaning
within **parent × country cells**, the gap is still **23.3 percentage points**.
Leave-one-parent-out moves the raw gap only between 45.4 and 48.8 points.

Legal form carries an independent signal:

| Legal form | n | % holding at least one subsidiary |
|---|---|---|
| B.V. (Netherlands) | 114 | **50.0** |
| Pte Ltd (Singapore) | 53 | 37.7 |
| S.A.R.L. (Lux/France) | 18 | 33.3 |
| GmbH (Germany) | 79 | 32.9 |
| Inc (United States) | 168 | 27.4 |
| Pty (Australia/South Africa) | 101 | 15.8 |
| **LLC (United States)** | 137 | **13.9** |

All-entity baseline: 22.0%.

**Precision and recall, stated honestly.** The holding-name flag is a
**high-precision, low-recall** classifier: 64.4% precision, **28.2% recall**.
Most holding companies are not named as such (Novelis Inc, Aleris Corporation,
Wipro LLC), so the flag identifies a clean subset rather than the whole class.

**Why it matters — methodological.** Corporate-structure datasets very often
have names and jurisdictions but no ownership graph. This shows the name alone
carries substantial information about function, and it does so *conditional on
country*, so it is not simply a proxy for "Dutch companies are called Holding
B.V.". For any dataset with names but no edges, the flag gives a usable
holding-company proxy with a measurable error rate.

**Mundane explanation.** Naming conventions are chosen by the group to signal
function, and some jurisdictions require a form (B.V., GmbH) that is
conventionally used for holding purposes. That is precisely why it works.

**Falsification.** If the effect were purely a jurisdiction artefact it would
disappear within country. It does not — 23.3pp survives parent × country
demeaning.

**Figure.** `fig11_name_predicts_role.png`. **Tables.**
`name_tokens_vs_role`, `legal_form_vs_role`, `name_signal_robustness`.
**Research value: 4/5.**

## C-F021 · Layering does not dilute ownership — and the tempting reading of that is wrong

**Result.** For the 1,083 non-level-0 entities whose entire chain has recorded
positive stakes (65.6% of 1,650), cumulative ownership below the first foreign
entity has a **median of 100%** and **53.6% of chains are exactly 100% at every
step**. Depth does not erode it: mean cumulative ownership is 87.3% at level 2,
91.9% at level 3, 93.9% at level 5 and 93.9% at level 8. Layers are wholly
owned conduits, not partial-ownership steps.

**The falsification, which is the more useful half.** The raw data suggest
"partners at the top, wholly owned below": single-edge stakes average 76.7% at
levels 1–2 and 92.4% at level 3+, a 15.7-point gap. **Within parent the gap is
2.0 points**, and excluding Reliance the cumulative-ownership gap vanishes
entirely (87.4% shallow versus 86.4% deep). The apparent depth gradient is a
between-group composition effect driven by Reliance's minority venture holdings,
which sit almost entirely at level 1. My own increment-1 idea A4 predicted the
opposite and is refuted.

**Selection caveat, on the figure.** Chain completion falls with depth in a
non-monotonic way (66.5% at level 1, 72.6% at level 2, 50.0% at level 4, 45.6%
at level 6) because a longer chain needs more edges to have a positive recorded
stake. The completed-chain sample is therefore selected toward well-documented
chains. The direction of that bias is unknown, so the level-by-level means
should be read as descriptive.

**Why it matters.** If depth diluted economic ownership, deep entities would
matter less for consolidated valuation and the depth statistics would be
economically minor. They do not: a level-8 entity is, on this evidence, as
wholly owned as a level-1 entity. Depth is about structure, not about
diminishing economic claims — which is exactly what makes it worth measuring.

**Figure.** `fig12_no_ownership_dilution.png`. **Tables.**
`cumulative_ownership_by_level`, `cumulative_ownership_completion`,
`ownership_dilution_by_depth`.
**Research value: 4/5 (the falsification is the more valuable part).**

## C-F022 · The Netherlands and Mauritius divide the world between them

**Result.** Assigning each entity the first foreign jurisdiction on its path,
and asking which gateway each destination is reached through:

- **The Netherlands is the modal gateway for 11 of the 31 destinations** with
  at least 12 entities: France (62.8%), Spain (57.1%), China (50.8%),
  Portugal (50.0%), Brazil (48.1%), Germany (45.7%), Thailand (43.8%),
  Canada (38.5%), Russia (35.7%), South Korea (35.7%), Poland (31.2%).
- **Mauritius is the modal gateway for 9**: Namibia (100%), Botswana (100%),
  Turkey (76.9%), Indonesia (61.5%), South Africa (51.2%), Australia (35.2%),
  UAE (28.6%), Hong Kong (21.4%), Italy (20.0%).

The split is regional: the Netherlands routes continental Europe, Latin America
and East Asia; Mauritius routes Africa, Australia and the Middle East. The
median destination is reached through its top gateway 50.8% of the time.

**Robustness.** The routing-concentration table reports how many parents use
each modal route, and this is where the finding needs care. The strong cells
are Netherlands → Germany (5 parents), Netherlands → Brazil (5),
Netherlands → Canada (5), Mauritius → South Africa (6), Mauritius → Australia
(4), Mauritius → Mauritius (8). The 100% cells (Namibia, Botswana) rest on 2
and 1 parent respectively and are single-group facts.

**Hierarchy mechanics.** A single gateway with a large subtree mechanically
dominates the destinations inside that subtree, so this measure is not
independent of C-F018. The parent counts are the guard: a route used by five
or six different groups is not one group's subtree.

**Mundane explanation.** Bilateral investment treaties and historical ties —
the India–Mauritius relationship for Africa, Dutch holding structures for the
EU single market — are the obvious drivers, and both predate any of these
investments.

**Table.** `destination_routing_concentration`.
**Research value: 3/5 pooled, 4/5 restricted to the multi-parent routes.**

## Updated ranked shortlist (increments 1 and 2)

| Rank | Code | Claim | Robustness |
|---|---|---|---|
| 1 | C-F018 | median large group routes 43% of its foreign network through one company | high; not mechanical (r = −0.35 with gateway count) |
| 2 | C-F019 | three jurisdictions sit above 61% of all entities | high; equal-parent and LOO reported |
| 3 | C-F002 | gateway amplification by first-hop jurisdiction | high; LOO-checked, 12 parents |
| 4 | C-F003 | 59% of entities held through a financial centre; 0–97% across groups | high; four robustness cuts |
| 5 | C-F020 | names predict network position within parent × country | high; 23pp within-cell, LOO 45–49pp raw |
| 6 | C-F001 | ODI register sees roughly one entity in ten | medium; skewed, median 2 per UIN |
| 7 | C-F021 | layering does not dilute ownership | medium; completion-rate selection |
| 8 | C-F004 | breadth and depth are different choices | medium; see X-F006 review |
| 9 | C-F008 | vintage shift in gateway jurisdictions | low-medium; 16–54 UINs per bin |
| 10 | C-F022 | Netherlands and Mauritius divide the world regionally | medium on multi-parent routes only |
