# Final adjudication — Claude

**Round:** final cross-review and adjudication before joint synthesis.
**Date:** 2026-08-27.
**Other agent's branch reviewed:** `origin/agent/codex`.
**Exact commit SHA reviewed:** `722a0c04312b13f351ea0c1faaed867c2cccc681`
(`research(codex): replicate claims and audit gateway concentration`).
The previously reviewed commit `bb67b9331f54eb7b9bfe9070c962f5664337c777` is
its parent; both are covered here. Inspection was read-only
(`git fetch`, `git log`, `git ls-tree`, `git show`). No merge, cherry-pick,
rebase, checkout, or modification of that branch was performed, and no Codex
code was executed or copied. Every number below labelled "recheck" was
recomputed from the immutable input
(`~/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta`)
through my own pipeline.

**New code this round:** `src/claude/12_adjudicate.py`,
`13_adjudicate_two.py`, `14_adjudicate_three.py`, `15_adjudicate_four.py`.
**New tables:** `outputs/claude/tables/adj_*.md` (11 tables).

**Language.** Nothing here supports an inference about legality, tax treatment
or conduct. Holding companies in financial centres are an ordinary, lawful
feature of multinational corporate finance. This document measures topology.

---

## 0. The one correction that reshapes the round

Codex's review of my commit `5ab6cb5` found that my hierarchy builder replaced
the reported `immediate_parent_country` of a named-but-unscraped intermediary
with `(UNOBSERVED)`, discarding supplied data.

**I reproduce this and confirm it.** There are **20** distinct intermediaries
named as `immediate_parent` but never scraped as entities, carrying **81**
child edges, and **all 20 have a reported non-India parent country**
(`adj_unobserved_parent_countries`). The largest are
`DR REDDY'S LABORATORIES SA` (Switzerland, 29 direct children, 37 descendants),
`NOVELIS HOLDINGS INC` (United States, 38 descendants), `HOMEFIELD PVT UK
LIMITED` (United Kingdom, 13) and `INFOSYS GERMANY GMBH` (Germany, 10).

Preserving the reported country changes:

| Statistic | discarded (my increment 1) | preserved (corrected) |
|---|---|---|
| Conduit exposure, entity-weighted | 58.8% | **61.2%** (Codex 61.8%) |
| Conduit exposure, equal-parent | 53.5% | **57.0%** (Codex 57.2%) |
| Dr Reddy's conduit exposure | 7.3% | **90.2%** (Codex 90.24%) |
| Dr Reddy's largest-subtree share | 7.5% | **92.5%** |
| Median group largest-subtree share | 43.2% | **50.8%** |
| Greedy cover at three jurisdictions | 60.6% | **62.2%** |

Codex is right, the correction is adopted, and every core number below uses the
corrected graph. This is the single most consequential finding of the whole
cross-review, and it came from the other branch.

---

## 1. Recommended core findings

Five results. Each survives entity-versus-path recounting, parent weighting,
leave-one-parent-out, and at least two denominator alternatives, and each was
either independently reproduced by both agents or re-verified here.

### CORE-1 · The funnel: the median large group routes half its foreign network through one company

**Statistic.** For the 24 groups with ≥15 entities, the share of the group's
entities sitting strictly below its single largest node has **median 50.8%,
mean 57.4%**, and **11 of 24 groups exceed 60%**. Jindal 98.1%, UPL 97.5%,
Tata Steel 96.2%, Biocon Biologics 95.5%, Dr Reddy's 92.5%, Glenmark 81.1%,
Airtel 79.7%.

**Unit / numerator / denominator.** Unit = parent group (24 obs, so the
headline is already parent-weighted, not entity-weighted). Numerator = largest
`n_descendants` within the group; denominator = group entities minus the
chokepoint. Because the reconstructed graph is a forest, every ancestor is a
dominator, so "largest subtree" is exactly "single point of detachment".

**Robustness** (`adj_chokepoint_robustness`):

| Sample | groups | median | mean | >60% |
|---|---:|---:|---:|---:|
| all entities, unscraped intermediaries included | 24 | 50.8 | 57.4 | 11 |
| excluding the two venture-fund portfolios | 24 | 50.8 | 57.2 | 11 |
| excluding strictly positive stakes below 10% | 24 | 48.2 | 56.7 | 11 |
| excluding entities above level 8 | 24 | 54.1 | 57.6 | 11 |

**Not mechanical.** The rival explanation is that a group with one registered
investment is concentrated by construction. Correlation with the number of
level-0 gateways is **−0.497**, and among the 16 groups with five or more
gateways the median is still **41.8%**. Airtel has six gateways and 79.7%;
Motherson has nine and 64.3%; Glenmark has eight and 81.1%.

**Falsification passed.** If the chokepoint were simply "the largest
acquisition", its jurisdiction should look like the group's own footprint.
**17 of 24 chokepoints (70.8%) sit in a financial-centre jurisdiction, against
a 26.5% benchmark** — the mean share of those same groups' own entities that
are located in a centre (`adj_chokepoint_jurisdiction`). A 44-point excess.

**Convergent validation from the other branch.** Codex's X-F018 measures a
different object — the share of a group's targets carrying its modal UIN —
and gets 59.7% pooled, 62.1% equal-parent, which I reproduce **exactly**.
Correlation between the graph chokepoint and the modal-UIN share across the 24
groups is **0.87** (`adj_chokepoint_vs_uin_channel`). Two independently built
measures, one topological and one administrative, agree on the ranking.

### CORE-2 · Three jurisdictions sit above 62% of all Indian foreign subsidiaries

**Statistic.** Greedy cover on the corrected graph
(`adj_greedy_cover_corrected`): Netherlands detaches 540 entities (29.4%),
adding the United States reaches 48.0%, adding Mauritius reaches **62.2%**;
United Kingdom 69.4%, Singapore 75.2%, Cyprus 79.3%, Switzerland 83.3%.

**Leverage per resident entity** differs by an order of magnitude:
Cyprus 7.6, Mauritius 5.4, Netherlands 4.8, Singapore 2.5, United Kingdom 2.2,
against **1.0 for the United States**, which has the most resident entities
(363) and almost no leverage.

**Robustness** (`adj_jurisdiction_criticality_corrected`). Netherlands: 29.4%
pooled, 20.9% equal-parent, LOO 22.4–33.0%, 16 of 28 groups affected.
Mauritius: 16.8% / 14.7% / 11.8–19.1%, 10 groups. United States: 20.8% /
14.9% / 15.9–23.7%, 16 groups.

**Estimand discipline — Codex's X-F007 caution, adopted.** This is a
descendant-weighted exposure statistic: an ancestor is counted once per entity
below it. Counting each internal node once instead gives **36.6% of the 424
internal nodes located in a centre** (Codex: 38.0%). Both belong in the paper.
The descendant-weighted number answers "how much of the network sits below a
jurisdiction"; the node-weighted number answers "how many vehicles are there".
Neither is wrong; conflating them is.

**Fragile cells, quoted with n.** Jersey (64 entities below, but 2 resident
entities and 2 parents; equal-parent 0.8%), Estonia (1 parent) and Cyprus (5
parents) are single- or few-group facts.

### CORE-3 · Where the first foreign hop lands determines how much structure follows

**Statistic** (`adj_gateway_amplification_recheck`), descendants per level-0
gateway by that gateway's jurisdiction:

| Gateway | gateways | parents | mean | median | Codex mean | Codex median |
|---|---:|---:|---:|---:|---:|---:|
| Netherlands | 13 | 12 | 33.5 | 11.0 | 34.9 | 12.0 |
| Mauritius | 17 | 11 | 17.8 | 5.0 | 17.9 | 5.0 |
| United States | 28 | 12 | 9.9 | 1.5 | 9.9 | 1.5 |
| Singapore | 18 | 12 | 7.4 | 3.5 | 7.5 | 3.5 |
| United Arab Emirates | 9 | 6 | 2.3 | 1.0 | 2.6 | 1.0 |

Two independently built graphs, two linkers, the same ordering and essentially
the same magnitudes. The 13 Dutch gateways span **12 different parents**, so
this is not one group's architecture.

**Robustness.** My LOO minimum for the Netherlands is 19.8 (median 10.0);
Codex's is 21.25 and its equal-parent mean is 37.1 — the Dutch result is if
anything *stronger* under parent weighting. Codex additionally ran the
largest-subtree falsification I proposed but had not executed: restricting to
the eight Dutch gateways where no single child branch holds more than half the
descendants gives **mean 37.75, median 12.5**. The gap does not collapse.

**Reporting rule.** State the ratio in one estimand at a time. Dutch/US is
3.4–3.5 on means and 7.3–8.0 on medians. My increment-1 prose ("seven times",
"thirty-three times") mixed estimands and must not be reused.

**Caveat that stays.** Cyprus (29.0 on 3 gateways, collapsing to 5.5 when Wipro
is dropped) is fragile and belongs in a footnote, not the table headline.

### CORE-4 · Comparable footprints, opposite architectures

**Statistic.** Breadth and depth are close to independent design choices.
Reliance: 196 entities, maximum depth 2. Hindalco: 81 entities, maximum depth
12. Wipro 213/8, Motherson 309/8 (graph) or 12 (reported), ONGC Videsh 41/2
across 24 UINs. Correlation of `log(n_entities)` with `max_depth` is 0.63 and
with `n_countries` 0.79 — geography tracks size, depth does not.

Codex's X-F005 reaches the same conclusion on an independently built parent
table, adding a jurisdiction HHI (Motherson 0.060 across 45 countries;
Reliance 0.357 across 22, 57% of entities in the US) and the observation that
Reliance's shallow layer is portfolio-like (141/177 non-root edges at ≤50%).
**Both agents, independently, conclude that a single scalar complexity measure
is inadequate.** That agreement is the finding.

**Mandatory caveat, agreed by both branches.** "Depth" is two different
variables. Reported `level` and reconstructed graph distance disagree for
13.99% of complete paths (236/1,687 on Codex's stricter graph; 237 on mine),
**and 88% of the disagreements are Motherson**. Any depth statement must name
its measure. My increment-1 concern that depth is a disclosure artefact is not
supported in the cross-section — correlation between `max_depth` and
`pct_source_found` across the 28 parents is 0.065 — but remains open for the
two extremes.

### CORE-5 · The register sees the top of the structure

**Statistic.** 186 RBI ODI registrations expand into 1,834 foreign entities.
**47.5% (871/1,834) sit at level 2 or deeper**; 18.6% at level 5 or deeper.
Entities per UIN: mean 9.86, **median 2**, because 89 of 186 UINs (47.8%)
resolve to a single entity; the ten largest UINs are 49.2% of all entities.

**Corrections adopted from Codex, both verified.**
1. My increment-1 sentence "every UIN has exactly one level-0 entity" is
   **false**. **184 of 186** UINs have an observed level-0 entity; the two
   without cover 38 entities (37 Dr Reddy's, 1 Wipro). No UIN has more than one.
2. The mean multiplier is a skewed statistic and must be reported as such. The
   **median of 2** is the number to lead with; it still implies the register
   misses at least half the structure for half of all registered investments.
3. The "1,500 downstream entities" count is graph-definition dependent (Codex
   gets 1,522 nodes / 1,503 non-root targets). Report it as approximate.

**Why this is core despite the caveats.** It is the paper's motivating fact and
the reason CORE-1 to CORE-3 matter: ODI aggregates, and any OFBV valuation
anchored on the registered entity, measure the top of a structure whose mass
sits below it and whose control passes through a handful of nodes.

---

## 2. Supporting findings

**SUP-1 · Conduit exposure and its 96-point spread across groups.**
On the corrected graph, **61.2%** of the 1,834 entities have a
financial-centre jurisdiction strictly upstream (Codex 61.8%); equal-parent
**57.0%** (Codex 57.2%); LOO 57.7–67.2%; node-weighted **36.6%** (Codex 38.0%);
level 1+ only 68.1%; level 2+ only 75.4%. Across groups the corrected range
runs from **0%** (Biocon Biologics, Reliance Energy) to **96.3%** (UPL),
94.8% (Airtel), 92.6% (Tata Steel), 90.2% (Dr Reddy's).
The spread across groups of similar size is the interesting object; the pooled
level is definition-dependent and should never be quoted without its estimand.
*Both agents flag that the 19-place centre list is a maintained classification
imposed on the data, not a variable in it.*

**SUP-2 · Names predict network position, even within parent × country.**
Entities named *Holding(s)/Holdco/Investment(s)* hold at least one subsidiary
64.4% of the time versus 17.5% otherwise — a raw gap of **46.9pp** on 177
entities across 24 groups, LOO 45.4–48.8pp. **Self-correction:** my increment-2
within-cell figure of 23.3pp used the mean of demeaned outcomes, the same
estimator error Codex caught in C-F014. The proper within estimator gives
**36.5pp**, and the mean paired within-cell difference across the 68 cells with
variation in the flag is **36.7pp** (median 44.9pp). The finding is stronger
than I reported, not weaker. Precision 64.4%, recall 28.2% — a high-precision,
low-recall proxy, useful for datasets with names but no edges.

**SUP-3 · The apparent depth–ownership gradient is group composition.**
Codex's X-F019 and my C-F021 reach the same conclusion from opposite
directions and should be merged. Codex: 26.41pp pooled level-1-vs-level-2+
full-ownership gap collapses to 2.33pp equal-parent, 0.03pp excluding Reliance,
3.23pp paired on graph depth; bounded 37.5/69.0 to 71.0/85.7 under extreme
zero-stake imputations. Mine: on the 1,083 chains with complete positive
stakes, cumulative ownership has **median 100%** and 53.6% are exactly 100% at
every step; the raw 15.7pp single-edge gradient is 2.0pp within parent and
vanishes excluding Reliance. **Joint statement: layering does not dilute
economic ownership, and the pooled depth gradient is a Reliance-driven
composition effect.** Both agents independently refuted an attractive
hypothesis; that is the value.

**SUP-4 · A few hubs carry the network.** 78.0% of entities hold nothing; of
the 404 that hold something, exactly half hold precisely one entity — layering,
not branching. The **34 entities with ten or more direct children carry
741 of the 1,569 edges that originate from an observed entity (47.2%)**.
Codex's X-F009 finds the same 34 hubs and the same 741–742 edges but divides by
1,834 targets to get 40.5%. **My denominator is the correct one** — the
numerator counts edges, so the denominator must be edges. Substance identical.
Two of the top three hubs are venture vehicles, not subsidiaries, and must be
excluded from any control-weighted statement.

**SUP-5 · Jurisdictions sort into entry points and terminals.** Mean level of
resident entities: Singapore 0.87, Cyprus 1.00, Mauritius 1.21, Netherlands
1.86 at the entry end; France 5.53, China 4.97, Poland 4.19, Mexico 3.82 at the
terminal end. Pass-through rates run 54% (Netherlands) to 3.0% (Mexico), with
Thailand, Russia, Malaysia and the Philippines 100% leaf. Close to the
definition of a holding-company location, so unsurprising — but *measured* on
Indian outward FDI rather than assumed, and the ordering is not obvious ex ante.

---

## 3. Interesting descriptive facts

Real, reproducible, too small or too group-specific to carry a section.

| Fact | Statistic | Constraint |
|---|---|---|
| Recurring path motifs (C-F007) | 1,834 entities travel only 610 collapsed jurisdiction sequences; top 25 cover ~40%; 67.0% span 3+ jurisdictions | motifs are within-group template replication; only Mauritius→Southern Africa spans parents |
| Marshall Islands SPVs (C-F011) | all 13 entities are level-1 leaves, zero descendants, two groups (4 Jindal vessels, 9 Reliance ethane carriers) | n = 13, 2 parents; a clean "one ship, one company" instance |
| Mirrored PSU consortium chains (C-F012) | Indian Oil and Oil India each built a separate Swedish vehicle into the same `INDOIL NETHERLANDS B.V.`; 3 Singapore JVs held twice | 4 shared entities, 4 parents; matters as a double-counting caution |
| Chains returning to India (C-F010) | 12 of 1,834 entities are Indian- or IFSC-registered at level ≥1, owned through a foreign chain | n = 12 (0.65%); mostly acquired-target Indian arms, not designed round-trips |
| Netherlands / Mauritius regional division (C-F022) | Netherlands is modal gateway for 11 of 31 destinations (Europe, Latin America, East Asia); Mauritius for 9 (Africa, Australia, Middle East) | only the multi-parent routes (NL→Germany/Brazil/Canada, MU→South Africa/Australia) are group-robust |
| "Foreign" file contains domestic labels (X-F015) | 10 entities labelled India, 9 IFSC GIFT CITY, 1 `EUROPIAN UNION`, of 1,834 | Codex's finding; adopted as a filter rule |
| Duplicate entities are immaterial (X-F003) | my recheck: 11 global name-country clusters, 22 occurrences, 11 cross-parent, 1,823 global uniques. Codex: 16 / 32 / 12 / 1,818 | normalization-aggressiveness difference; ≤1.2% of the file either way, cannot drive any headline |

---

## 4. Rejected and fragile findings

### Rejected outright

| Claim | Source | Why rejected |
|---|---|---|
| "Every UIN has exactly one level-0 entity" | my C-F001 | false: 184 of 186; verified |
| `(UNOBSERVED)` for named-but-unscraped parents | my `02_build_hierarchy.py` | discards 20 supplied country labels on 81 edges; verified and corrected |
| Dr Reddy's conduit exposure 7.3% | my C-F003 | artefact of the above; correct value 90.2% |
| "The depth gradient in coverage nearly vanishes within parent" (−0.9pp) | my C-F014 | wrong estimator; see §5.2 |
| Name-signal within-cell gap of 23.3pp | my C-F020 | same estimator error; correct value 36.5pp |
| Cross-border edge share 64.1% | my increment 1 | included level-0 India edges, which cross by construction; correct value 57.64% |
| "Partners at the top, wholly owned below" (idea A4) | my IDEAS.md | refuted: 2.0pp within parent, vanishes excluding Reliance |
| Any sector × depth association | implied by raw data | 240 of 242 deep manufacturing entities are Motherson + Hindalco (X-F006, verified) |
| Any value-weighted structural statistic | proposed by the protocol | **not estimable**: units are blank for 516 of 560 ready rows across 9 currencies. Every structural statistic in this project is necessarily entity-weighted. This must be stated in the paper, not silently assumed |

### Fragile — real but not yet publishable as stated

| Claim | Status |
|---|---|
| Gateway vintage shift (C-F008) | The **Mauritius decline is the robust component**: 11/55 pre-2011 gateways versus 4/99 from 2016, Fisher two-sided p = 0.0030, LOO −19.4 to −13.4pp, equal-parent −17.8pp (Codex's sharper two-era test, adopted over my five-bin version). **"Singapore in" is not established** (p = 0.17, 16 gateways total); GIFT City is p = 0.051 on 7 gateways. And the whole result inherits the unvalidated UIN-year assumption below. Fragile until both are fixed |
| Holding-company financial signature (C-F013) | The pooled 5× turnover/assets gap is a currency- and unit-mixing artefact; the defensible number is the 2× gap in the USD subsample (n = 89). Keep as graph validation, not as a finding |
| Jersey / Estonia / Cyprus leverage | 1–5 parents each; quote with n or drop |
| Negative equity by jurisdiction | Mauritius 53.8% on n = 13; ordinary in loan-funded holding companies (X-F012). Downgraded |
| 1,500 downstream entities (C-F001) | graph-definition dependent (1,500 / 1,503 / 1,522). Report as approximate |

---

## 5. Disagreements resolved

### 5.1 Reported country of unscraped intermediaries — **Codex right, adopted**
Stated in §0. Verified independently: 20 nodes, 81 edges, all with a reported
non-India country. Dr Reddy's conduit exposure 7.3% → 90.2%, exactly matching
Codex's 37/41 = 90.24%; its chokepoint share 7.5% → 92.5%. Pooled effects are
small (58.8% → 61.2%) but one parent ranking reverses completely.

### 5.2 Coverage depth gradient: which estimator — **Codex right, adopted**
I reported −0.9pp as the within-parent gap; Codex objected that this is the
mean of demeaned outcomes inside the deep cell, not a fixed-effect coefficient.
My recheck (`adj_coverage_depth_estimators`) reproduces Codex **to the second
decimal**:

| Estimator | Value (pp) |
|---|---:|
| raw deep-minus-shallow gap | −6.65 |
| parent fixed-effect coefficient | **−2.42** |
| mean paired within-parent difference (16 parents with both cells) | −2.98 |
| median paired within-parent difference | −7.93 |
| leave-one-parent-out FE range | **−6.62 to −0.77** |

The −6.62 endpoint comes from dropping Wipro, the −0.77 endpoint from dropping
Motherson — also exactly as Codex reports. **Resolution:** parent selection is
first order (rates run 0% to 92%, five parents supply 60.8% of ready targets),
but the depth association is *attenuated, not eliminated*, and is
leave-one-parent-out sensitive. My "group, not depth" framing overstated it and
is withdrawn. This same estimator error, found in my C-F014, is what led me to
re-audit C-F020 and find that my name-signal number was too *low*.

### 5.3 Conduit exposure magnitude: 59.3% versus 61.8% — **not a disagreement**
Both are correct on their own graph. Corrected, mine is 61.2% and Codex's is
61.8%; equal-parent 57.0% versus 57.2%; node-weighted 36.6% versus 38.0%. The
residual is a handful of cross-UIN links Codex's linker recovers. **Report a
range, not a point.**

### 5.4 Dutch gateway amplification: 33.5 versus 34.85 — **both defensible**
Codex's linker recovers one additional cross-UIN Dutch chain, most visibly
under Tata Communications (total descendants 453 versus my 436). The difference
strengthens the result rather than creating it. **Use the median (11–12) as the
headline and report the mean with both graphs.**

### 5.5 Graph chokepoint (C-F018) versus UIN channel (X-F018) — **complementary**
Not competing claims: one is topological, one administrative. Correlation
across the 24 groups is **0.87**. Median 50.8% (graph) versus 63.2% (modal
UIN). They diverge exactly where the graph is imperfect, and Codex predicted
both cases: **Hindalco** 47.5% graph versus 95.1% UIN (graph truncation — only
38 of 81 paths are complete), **Motherson** 64.3% versus 44.7% (cross-UIN
linking short-circuits the reported chain). **Resolution: report both. The
graph measure is the conservative one and is the paper's headline; the UIN
measure is the administrative cross-check.**

### 5.6 Hub concentration denominator — **my denominator right, substance identical**
Codex divides 741–742 hub edges by 1,834 *targets* to get 40.5%. The numerator
counts edges, so the denominator must be the 1,569 edges that originate from an
observed entity: **47.2%**. Both agents identify the same 34 hubs.

### 5.7 Duplicate entity clusters: 16 versus 11 — **immaterial**
A normalization-aggressiveness difference (Codex 16 clusters / 32 occurrences /
1,818 global uniques; mine 11 / 22 / 1,823). Either way duplicates are ≤1.2% of
the file and cannot drive a headline. Neither number should be presented as
authoritative without registration numbers.

### 5.8 Cross-border edge share — **exact agreement**
57.64% pooled, 58.67% equal-parent, LOO 56.06–61.78%, all to the second
decimal, on independently built edge tables. Also X-F018 (59.71% / 62.05% /
61.16%) and X-F001 (Tata Communications 14.7% of rows versus 2.7% of entities,
ratio 5.4 versus Codex's 5.49) reproduce.

---

## 6. Remaining disagreements and unresolved questions

**U-1 · Which depth concept reflects legal structure.** Both agents agree
reported `level` and graph distance diverge for ~14% of complete paths and that
Motherson supplies 88%. Neither can decide which is right. A reported level may
count an omitted intermediary (graph distance is then a lower bound), or
cross-UIN linking may have short-circuited a chain (reported level is then
stale). **Unresolved. Requires external ownership charts.** This is the single
largest threat to CORE-4 and to every depth statistic.

**U-2 · Whether the UIN substrings mean what I inferred.** The 13-character
fixed format is verified by both agents. The semantic labels — regional office,
investment type, series, registration year, serial — are my inference from
three internal consistency checks. Codex's objection is fair: my W/J/P
validation uses *level-1 child* stakes because the India-to-level-0 stake is
missing for all 184 roots. **Unresolved. Requires the RBI ODI form
specification.** C-F008 is downstream of this and inherits the risk.

**U-3 · The 406 zero stakes.** Both agents agree `stake == 0` is a missing code
(7 of 7 cases with an AOC-1 cross-check are contradicted). Codex bounded the
consequences for the ownership gradient (37.5/69.0 to 71.0/85.7). **The
underlying semantics remain unresolved** and no cumulative-control measure is
safe until the mapping source distinguishes unknown from true zero.

**U-4 · Whether measured depth is a firm characteristic or a disclosure
artefact.** The cross-sectional correlation between `max_depth` and
`pct_source_found` is 0.065 — essentially zero — so the disclosure channel does
not explain the spread across 28 parents. It may still explain the two extremes
(Reliance 15.3% source location and flattest; Hindalco 100% and deepest).
**Unresolved for the extremes.**

**U-5 · Whether "financial centre" is the right partition.** Both agents flag
that the 19-place list is imposed. Singapore, UAE, Switzerland and Ireland host
ordinary operating companies. No test in the data can separate a holding
jurisdiction from an operating one except by measured behaviour — which is
circular if the behaviour is the outcome. **Unresolved; a design problem, not a
data problem.** SUP-2 (names predict role) is the partial substitute and should
be used that way.

---

## 7. Recommended final tables

| # | Table | Content | Source |
|---|---|---|---|
| T1 | The denominator ladder | 3,742 rows → 3,567 target-years → 1,834 targets → 1,818–1,830 entities → 186 UINs → 184 roots → 28 parents, with both agents' counts side by side and the row/entity ratio by parent | `adj_row_vs_entity_weighting`, Codex `row_denominators` |
| T2 | Parent structural table | one row per group: entities, countries, jurisdiction HHI, reported and graph max depth, largest-subtree share, modal-UIN share, conduit exposure, coverage rate | `parent_summary` + `adj_chokepoint_vs_uin_channel` + Codex `ultimate_parent_analytical` |
| T3 | Gateway amplification | by first-hop jurisdiction: gateways, parents, mean, median, equal-parent mean, LOO minimum, largest-subtree-restricted mean | `adj_gateway_amplification_recheck` + Codex `gateway_amplification_review` |
| T4 | Jurisdiction criticality and cover | entities below, % of 1,834, resident entities, leverage per resident, parents affected, equal-parent %, LOO range; greedy cover in a second panel | `adj_jurisdiction_criticality_corrected`, `adj_greedy_cover_corrected` |
| T5 | Chokepoints | all 24 groups: entities, chokepoint name and jurisdiction, % below, modal-UIN share, and the centre-versus-benchmark test | `adj_chokepoint_corrected`, `adj_chokepoint_jurisdiction` |
| T6 | **The robustness matrix** | every headline statistic (rows) × {pooled, equal-parent, LOO range, node-weighted, fund-excluded, minority-excluded, complete-paths-only} (columns), with a blank where an estimand does not apply | `adj_conduit_exposure_estimands`, `adj_chokepoint_robustness`, `adj_coverage_depth_estimators`, `adj_cross_check_ledger` |
| T7 | Data-quality gates | source located 46.2%, parsed 24.2%, ready 14.4%; 39/560 sign failures; 516/560 blank units; 70 rows sharing a balance sheet; 20 unscraped intermediaries over 81 edges; 406 zero stakes | `coverage_summary`, Codex `financial_plausibility`, `adj_unobserved_foreign_intermediaries` |

T6 is the table I would fight hardest to keep. It is what makes the paper
credible and it is the direct product of this two-agent process.

## 8. Recommended final figures

| # | Figure | Design | Status |
|---|---|---|---|
| F1 | The funnel | one panel: entities per UIN (log, median line at 2) beside the level distribution with 47.5% shaded at level 2+ | revise `fig01` |
| F2 | Gateway amplification | descendants per gateway, jurisdictions on the y-axis, one dot per gateway, median marked, LOO band behind | revise `fig02` |
| F3 | **Chokepoint dot plot** | 24 groups ranked by % below one node, dot coloured by chokepoint jurisdiction type, vertical line at the 26.5% random-entity benchmark, modal-UIN share as a hollow marker on the same row | revise `fig09` — **the paper's lead figure** |
| F4 | Jurisdiction criticality | scatter of resident entities (x) against entities held below (y), log–log, 45° line marking leverage 1, labelled points | revise `fig10` |
| F5 | Breadth versus depth | entities (log) against max depth, one point per parent, dual markers for reported and graph depth to make U-1 visible | revise `fig04` |
| F6 | **The robustness ladder** | each core statistic on its own row, one dot per weighting scheme, so the reader sees at a glance which results move and which do not | **new — build this** |
| F7 | Coverage by parent | appendix: ready-rate by group, 0% to 92%, with the pooled rate as a line | keep `fig08` |

Drop `fig03`, `fig05`, `fig06`, `fig07`, `fig11`, `fig12` from the paper; they
are exploratory and their content is better carried in T2 and T6.

## 9. Recommended paper structure

**Working title.** *The Funnel: Hierarchy, Chokepoints and Jurisdictional
Concentration in Indian Outward Direct Investment.*

**Central research question.** *How much corporate structure sits beneath a
registered Indian outward direct investment, how is control over that structure
concentrated across companies and jurisdictions, and what does the answer imply
for how outward FDI is measured?*

**Main empirical narrative.** A registered ODI is a first hop. Beneath it sits
a network roughly ten times larger on average and twice as large for the median
registration, half of it two or more levels down (CORE-5). How much sits below
is a property of where the first hop lands, not of the investment's size
(CORE-3). The resulting structure is not a branching tree but a funnel: the
median group's entire foreign network passes through a single company (CORE-1),
overwhelmingly located in a financial centre rather than in an operating market,
and three jurisdictions sit above 62% of all entities in the file (CORE-2).
Groups of similar size make radically different architectural choices
(CORE-4). Because that variation is firm-level, every pooled statistic about
"Indian subsidiaries" is really a statement about a handful of parents — which
is the paper's measurement contribution.

**Sections.**

1. **Introduction** — the register-versus-network gap, and the funnel result.
2. **Data, and the denominator problem** — T1, the six competing units of
   observation, and the rule that every statistic names its estimand.
3. **What the register sees** — CORE-5, T1, F1.
4. **Gateway amplification** — CORE-3, T3, F2.
5. **The funnel** — CORE-1 and CORE-2; T4, T5; F3, F4. The paper's core.
6. **Architectural heterogeneity** — CORE-4, SUP-1, SUP-5; T2, F5.
7. **What does not survive** — SUP-3, the estimator corrections of §5.2, the
   Motherson/Hindalco depth problem, the non-estimability of value weighting;
   T6, F6. *A genuine negative-results section, not an appendix.*
8. **Measurement implications** — for ODI aggregates, for OFBV valuation on a
   14.4% parent-selected subsample, and for anyone building a complexity index
   from entity counts.
9. **Conclusion and limitations.**

**Appendices.** A: UIN internal structure, explicitly labelled as inference
pending the RBI specification. B: data-quality gates (T7). C: the full
robustness matrix. D: reproduction instructions for both pipelines.

**Analyses to drop.** Sector × depth (composition). Value-weighted anything
(not estimable). Holding-company financial ratios as a *finding* (keep as graph
validation). Five-bin gateway vintage (replaced by the two-era test). Jersey and
Estonia leverage as standalone facts. Everything in `fig03/05/06/07/11/12`.
The pooled negative-equity-by-jurisdiction table.

### Facts established by this dataset, versus interpretations that are not

**A. Established here (topology and measurement, no external evidence needed).**
Entity, path and edge counts and every denominator in T1; the depth
distribution under both measures; descendants per gateway by jurisdiction;
largest-subtree shares and their jurisdictions; the greedy cover; cross-border
edge shares; conduit exposure under each estimand; hub out-degrees; recurring
motifs; name-to-role prediction; coverage and financial-gate failure rates; the
duplicate and unscraped-intermediary counts; the absence of ownership dilution
with depth.

**B. Requires external evidence and must be labelled as such.** That any
jurisdiction is used *for* tax, treaty access or regulatory arbitrage. That the
Mauritius gateway decline was caused by the 2016 protocol, or the GIFT City
arrival by the IFSC regime — the file contains no policy variable. That the UIN
substrings mean registration office, investment type or year. That a chokepoint
reflects current legal control rather than the mapping's exposure attribution.
That any structure is designed rather than inherited through acquisition. That
19 named jurisdictions are "financial centres" — an imposed classification.
That reported `level` reflects legal ownership distance.

The paper should carry these two lists explicitly, as a table.

## 10. Missing robustness work that genuinely matters

Ranked by how much a negative result would change the paper.

1. **External validation of the hierarchy for three groups** — Motherson,
   Hindalco, Dr Reddy's — against AOC-1 filings or annual-report ownership
   charts. This is the only thing that resolves U-1, and U-1 threatens CORE-4,
   the C-F018/X-F018 divergence, and every depth statistic. **Highest value.**
2. **Insert the 20 unscraped intermediaries as first-class nodes throughout
   both pipelines.** I have done this only inside the adjudication scripts. It
   must be pushed back into `02_build_hierarchy.py` before the joint dataset is
   frozen, or the corrected numbers will not be reproducible from the main run.
3. **Clustered / bootstrap inference on the chokepoint median.** CORE-1 is
   currently a point estimate on 24 groups. A parent bootstrap would give it a
   confidence interval, which a referee will ask for.
4. **The duplicate-evidence filter as a row-level deliverable.** 70 of 560
   ready rows carry a balance sheet whose evidence text is byte-identical to
   another target's (my X-F017 review, sharpened from Codex's 51 clusters). No
   financial statistic should be published before this flag exists and every
   financial number is re-run on the cleaned ~460-row sample.
5. **The RBI ODI form specification** — resolves U-2, and with it C-F008.
6. **The full ODI register as a denominator** — the vintage result currently
   describes 186 registrations of unknown representativeness.
7. **A single reconciled entity table across both branches** — 1,818 / 1,823 /
   1,830 / 1,834 are four different counts of the same thing. One frozen
   entity key, agreed by both agents, before any table is written.

*Not worth doing:* sector fixed effects (28 parents), time-series structure
(hierarchy variables are static within target, X-F016), and value weighting
(units missing for 92% of ready rows).

## 11. Does the evidence support a coherent empirical paper?

**Yes — one descriptive-and-measurement paper, not a causal or policy paper.**

The case for it:

- **A genuine central result.** CORE-1 is surprising, economically meaningful,
  parent-weighted by construction, robust to every cut I ran, and passes its own
  falsification test by 44 percentage points. It was reached independently by
  two agents through two different measures that correlate at 0.87.
- **A coherent narrative.** CORE-5 → CORE-3 → CORE-1/CORE-2 → CORE-4 is a
  single argument, not a list.
- **Unusually strong internal replication.** Two independently built pipelines
  agree to the second decimal on the cross-border share, the modal-UIN share,
  the coverage FE coefficient and its LOO endpoints, the hub set, and the
  gateway ordering. Where they disagreed, every disagreement is now resolved or
  explicitly marked unresolved.
- **A real negative-results section** (§7 above), which most descriptive
  corporate-structure work lacks.

The case against overclaiming:

- **Nothing here is causal, and nothing here is about tax.** Every institutional
  reading sits in list B of §9.
- **28 parents is the binding constraint.** It supports parent-weighted
  descriptive statistics and leave-one-out sensitivity. It does not support
  regressions with covariates, sector effects, or inference that treats parents
  as a sample from a population.
- **The financial layer is not publishable in its current state.** 14.4%
  coverage, parent-selected from 0% to 92%, 7% sign failures, 92% missing units,
  and 70 shared balance sheets. It belongs in the paper as a *measurement
  finding* about data availability, not as evidence about firm performance.
- **U-1 is unresolved and load-bearing.** If external charts show that reported
  `level` is right and graph distance is wrong, CORE-4's headline contrast
  changes. CORE-1, CORE-2 and CORE-3 do not depend on the depth measure and
  would survive.

**Recommendation.** Write the paper around CORE-1 and CORE-2, with CORE-5 as
motivation and CORE-3 as mechanism. Treat the financial data as a measurement
appendix. Do item 1 and item 2 of §10 before drafting; do items 3 and 4 before
submitting. Present §5.2 and the §0 correction openly in the appendix — a paper
that shows which of its own estimators were wrong is more credible, not less.
