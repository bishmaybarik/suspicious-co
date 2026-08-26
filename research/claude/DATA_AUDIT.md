# Data audit — `subsidiary_financial_variables_refined.dta`

Agent: Claude (blind discovery, increment 1)
Code: `src/claude/01_audit_rows.py`, `src/claude/02_build_hierarchy.py`,
`src/claude/06_audit_uin_structure.py`
Tables: `outputs/claude/tables/audit_*.md`, `unobserved_intermediaries.md`,
`uin_*.md`

---

## 1. Units of observation

The file has **3,742 rows and 77 variables**. There are three nested units,
and confusing them is the single largest denominator risk in this project.

| Unit | Count | Key | Notes |
|---|---|---|---|
| Source row | 3,742 | none (row number) | one located financial-statement source for one entity-year |
| Entity-year | 3,567 preferred | `target_id` × `fiscal_year` | `preferred_for_target_year == 1` selects exactly one row per entity-year |
| Scraped entity | **1,834** | `target_id` | the analytical unit for all structural work |
| Registered outward investment | **186** | `uin` | the RBI ODI registration |
| Indian parent bucket | **28** | `parent` | 25 PDF-scraped + 3 AOC-1 fallback |

`target_id` × `fiscal_year` is *not* unique in the raw file: 94 combinations
carry 2–4 rows. `preferred_for_target_year == 1` restores uniqueness exactly
(3,567 groups, all of size 1). 993 rows have a blank `fiscal_year`; these are
targets for which no dated statement was located.

All 14 structural variables (`parent`, `level`, `entity_name`,
`entity_country`, `immediate_parent`, `immediate_parent_country`, `stake`,
`sector_code`, `sector_label`, `uin`, `shared_uin`, `n_top30_claimants`,
`top30_claimants`, `attribution_rule`) are **constant within `target_id`**
(zero targets show variation). The entity-level collapse is therefore lossless
for structure. Rows per target range from 1 to 16 (median 1).

`n_top30_claimants` is 1 for every row: the multi-claimant cases were already
removed upstream, as the dictionary states. 302 rows (8.1%) still carry
`shared_uin == 1` under `attribution_rule == "sole_top30_claimant_shared_uin"`.

## 2. Identifiers and the hierarchy

- `parent` — 28 Indian parent buckets. All names are truncated to 30
  characters (`SAMVARDHANA MOTHERSON INTERNATI`), so they are labels, not
  legal names.
- `uin` — 186 RBI ODI registration numbers. Each has **exactly one** level-0
  entity (184 of 186; 2 UINs have no level-0 entity), so the UIN identifies
  the first foreign entity and everything traced below it.
- `entity_name` — 1,828 distinct strings; 1,823 distinct after normalisation.
- `immediate_parent` — 457 distinct strings.
- `level` — 0 to 12.

**Does `(parent, entity)` repeat?** No. Within a parent bucket, the
normalised entity name is unique (1,834 groups for 1,834 targets). The
per-parent structure is therefore a proper forest, not a multigraph.

**Do entities appear on more than one ownership path?** Yes, but rarely.
Eleven normalised names appear under two different parent buckets
(22 targets, 1.2%). Two economically distinct cases:

1. *Genuine consortium vehicles.* `TAAS INDIA PTE LTD`, `URJA BHARAT PTE LTD`
   and `VANKOR INDIA PTE LTD` (Singapore) each sit under both
   `BHARAT PETRORESOURCES LTD` and `INDIAN OIL CORPORATION LTD.`, reached
   through each parent's own Singapore intermediary.
   `INDOIL NETHERLANDS B.V.` sits under both `INDIAN OIL CORPORATION LTD.`
   and `OIL INDIA LIMITED`, reached through `IOC SWEEDEN AB` and
   `OIL INDIA SWEDEN AB` respectively.
2. *Attribution artefacts.* Six Reliance US entities appear at level 0 under
   `RELIANCE INDUSTRIES LTD` (their own UIN) and again at level 1–2 under
   `RELIANCE ENERGY GENERATION & DI`. These are the same legal entities
   counted twice because two parent buckets and two UINs describe the same
   chain. Any entity count is therefore an upper bound by roughly 0.6%.

## 3. Reconstructed hierarchy

`src/claude/02_build_hierarchy.py` builds a directed graph in which each entity
contributes one edge from its `immediate_parent` to itself, namespaced by
parent bucket, with a synthetic root per Indian parent.

- The graph is a **directed acyclic graph with maximum in-degree 1**, i.e. a
  forest. Both properties are asserted in code.
- 1,854 edges over 1,884 nodes.
- Of the 1,650 non-level-0 entities, 90.4% have an `immediate_parent` that
  matches an entity inside the *same UIN*; 95.1% match inside the same
  *parent bucket*. The gap means chains cross UIN boundaries.
- **20 named intermediaries never appear as an entity themselves.** They are
  parents of 81 entities and are the root of subtrees containing 150 entities
  (8.2% of the file). Examples: `DR REDDY'S LABORATORIES SA` (29 children),
  `RIZING LLC`, `INFOSYS GERMANY GMBH`, `NOVELIS HOLDINGS INC.`. The build
  re-anchors each of these under its Indian parent and flags the affected
  entities with `is_orphan_bridged == 1` and `path_has_unobserved == 1`.
  Full list: `outputs/claude/tables/unobserved_intermediaries.md`.

### Depth: two measures, and where they disagree

| Measure | Definition |
|---|---|
| `level` | as supplied by the mapping; used as the **primary** depth measure |
| `depth_graph` | distance from the Indian parent through `immediate_parent` links, with orphan subtrees offset by their implied level |

They agree for **87.1%** of entities. All 237 disagreements have
`depth_graph < level`, and **208 of them (88%) are Samvardhana Motherson**.
The mechanism: within the Motherson bucket the same entity is reached through
a short cross-UIN link while `level` was assigned inside a longer single-UIN
chain (e.g. `CELULOSA FABRIL (CEFA) S.A.` has `level == 6` but its recorded
`immediate_parent`, `SMP AUTOMOTIVE TECHNOLOGY IBERICA S.L.`, is a level-1
entity registered under a different UIN). Neither measure is wrong; they
answer different questions. Every depth-based result below is reported with
`level` and checked against `depth_graph`.

## 4. Geography and sector

- `entity_country`: 122 values, never missing. `INDIA` (10 entities) and
  `IFSC GIFT CITY` (9) are treated as distinct jurisdictions by the source;
  GIFT City is India's onshore IFSC.
- `immediate_parent_country`: 63 values, never missing.
- Country strings are inconsistent in places (`HONGKONG`, `MARSHALL ISLAND`,
  `UNITED STATES OF AMERICA`) but internally consistent, so no recoding was
  applied.
- `sector_label` / `sector_code`: 17 categories. **Sector is not a UIN
  attribute** — it varies within UIN for 67 of 186 UINs — so entity-level
  sector analysis is meaningful.

## 5. Ownership stake

`stake` is missing for exactly the 184 level-0 entities, i.e. the RBI-registered
first-hop stake is not in this file. For the remaining 1,650:

- 865 (52.4%) equal exactly 100
- **406 (24.6%) equal exactly 0**, which cannot be a real ownership share for
  a listed subsidiary; this is almost certainly "not recorded" coded as zero.
  The zero share falls monotonically with depth: 33.5% at level 1, 17.5% at
  levels 2–3, 0% at levels 8 and below. Treat `stake == 0` as missing.
- 14 entities have `stake == 0.0001`, all Reliance venture-portfolio holdings.

## 6. The UIN string is structured (undocumented)

The dictionary describes `uin` only as an identifier. All 186 values are
13 characters and parse cleanly as
`[2-char RBI regional office][1-char investment type][2-char series][4-digit year][4-digit serial]`.
Three independent checks support this reading
(`outputs/claude/tables/uin_*.md`):

1. **Investment type.** The third character takes values W (117 UINs),
   J (50) and P (19). Mean stake of the level-1 entities beneath them is
   82.8% (W, 65.8% at exactly 100), 60.1% (J, 50.0% at 100) and 13.6%
   (P, 1.6% at 100). The reading W = wholly owned subsidiary,
   J = joint venture, P = participating interest in an unincorporated entity
   is further supported by the level-0 names under P, which are almost all
   oil and gas blocks and consortia
   (`PETROLEUM PRODUCTION SHARING CONTRACT IN MYANMAR, BLOCK A-1`,
   `NORTH SEA EXPLORATION BLOCK 48`, `EUROPE INDIA GATEWAY (EIG)`) plus a
   venture fund (`BREAKTHROUGH ENERGY VENTURES LLC`).
2. **Regional office.** The first two characters map to the parent's home
   region: AH → Adani only; BG → Infosys, Wipro, Biocon; HY → Dr Reddy's;
   ND → ONGC Videsh, Oil India, Bharti, Jindal, Motherson; PJ → Vedanta
   (Goa) only.
3. **Year.** Characters 6–9 range 1989–2025. Of 125 UINs with a dated
   statement, only 10 (8%) have a statement year before the decoded year, and
   those gaps are 1–10 years, consistent with restatements and re-registration
   rather than a wrong reading.

This decoding is used for vintage analysis and is flagged as an inference
throughout, not as documented metadata.

## 7. Missingness and extraction quality

Entity level (1,834 entities):

| Stage | Entities | % |
|---|---|---|
| Any source located | 847 | 46.2 |
| Balance sheet parsed (non-missing `equity`) | 444 | 24.2 |
| Valuation-ready in at least one year | **265** | **14.4** |

Row level (3,742 rows): `ready_for_valuation == 1` for 560 rows (15.0%);
`needs_manual_review == 1` for 3,182 (85.0%). The dominant review reasons are
`balance_sheet_variables_missing` (2,717 rows, 72.6%), `period_end_missing`
(2,264, 60.5%) and `currency_missing` (2,206, 59.0%).

**Currency and units are the binding constraint on financial work.**
`currency` is blank on 2,350 rows (62.8%) and takes 10 values elsewhere;
`units` is blank on 3,680 rows (98.3%). Only 62 rows state units at all
(38 `INR crore`, 24 `INR millions`). Any cross-entity comparison of
`total_assets`, `equity` or `turnover` must be done **within a single
currency**, and even then the unit scale is unverified. The largest
single-currency subsample with parsed equity is USD (191 entities).

Cash-flow variables are effectively unusable at scale: `cash_flow_operating`
is present on 8.9% of rows, `dividends_paid` on 5.2%, `issue_share_capital`
on 1.2%.

## 8. Data-quality problems to carry forward

1. `stake == 0` is a missing-value code, not a zero share (406 entities).
2. `level` and the `immediate_parent` chain disagree for 12.9% of entities,
   almost entirely in one parent group.
3. 20 intermediaries in the chain are named but never scraped, leaving 150
   entities on paths with an unobserved node.
4. Six Reliance entities are double-counted across two parent buckets.
5. `currency` missing on 63% of rows; `units` missing on 98%.
6. Parent names are truncated at 30 characters.
7. 109 of Reliance's 196 entities are venture-fund portfolio companies held at
   stakes at or near zero. They are not subsidiaries in any control sense and
   inflate any unweighted entity count. See
   `outputs/claude/tables/parent_denominator_check.md`.
8. `fiscal_year` runs to `2025-26` and three rows carry a `period_end_date`
   after 2026-12-31 (latest 2028-03-31), i.e. some parsed dates are
   forward-looking and cannot be statement dates.
