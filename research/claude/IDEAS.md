# Research directions — Claude, blind discovery increment 1

Directions are grouped by what they need. Codes cross-reference
`FINDINGS.md`. Nothing here has been run unless it says so.

---

## A. Directions that can be executed on this file alone

**A1 · Is gateway amplification an acquisition artefact? (tests C-F002)**
For each level-0 gateway compute the share of its descendants that sit in the
single largest subtree. If Dutch and Mauritian gateways are amplifying purely
because they were the vehicle for one large acquisition, their amplification
should collapse once the largest subtree is removed, while a genuine
"structuring" jurisdiction would keep a broad fan. Cheap, and it decides how
C-F002 gets written.

**A2 · A depth-invariant complexity index for parents (extends C-F004)**
Build a small index from dimensions that are not mechanically nested:
number of distinct jurisdictions, jurisdiction Herfindahl, share of entities
reached through a centre, mean border crossings per path, share of holding
nodes with exactly one child. Compare its ranking with the naive entity count.
The interesting question is which groups move most between the two rankings.

**A3 · Where does an ownership chain "turn operational"? (extends C-F006)**
For each root-to-leaf path, find the first node whose jurisdiction has a
below-median pass-through rate. The number of hops before that point is a
clean scalar measure of holding-stack length, comparable across groups and
independent of how many operating subsidiaries sit at the bottom.

**A4 · Are joint ventures held deeper than wholly owned subsidiaries?**
`stake` (excluding the zero code) by `level`, within parent. The raw data show
mean stake rising from 68% at level 1 to above 93% at levels 2–6, i.e. control
appears to *increase* with depth. If that survives parent fixed effects it is
a real and non-obvious fact: partners are taken on at the top of the stack,
and the layers below are wholly owned.

**A5 · Sector composition by position in the chain**
`sector_label` varies within UIN, so entity-level sector analysis is valid.
Preliminary: 71.7% of Financial & Insurance Services entities sit at level ≥ 2
versus 19.2% of Professional & Business Services, and Financial & Insurance
has the highest non-leaf rate (44%). Worth formalising as "which sector labels
mark a holding node", and then checking whether the sector label is assigned
to the entity or inherited from the ODI registration.

**A6 · The 0.0001% stake cluster and what else looks like it**
14 entities carry `stake == 0.0001`; all are Reliance venture holdings.
Search for other stake values that recur suspiciously often across unrelated
parents — they are likely codes rather than shares, and each one found makes
the control-weighted denominators in C-F015 more reliable.

**A7 · Do parents replicate one template across many operating units? (C-F007)**
Formalise "template reuse": for each parent, the ratio of distinct collapsed
jurisdiction sequences to entities. Motherson has 309 entities; how many
distinct sequences? A low ratio means one structure stamped out repeatedly;
a high ratio means bespoke structuring per investment.

**A8 · Jurisdiction transition matrix against an independence benchmark**
Build the parent-country → child-country matrix and compare each cell with
the product of marginals. Over-represented transitions are the structural
motifs; this puts C-F007 on a statistical rather than an anecdotal footing,
with parent bootstrap standard errors.

---

## B. Directions that need one additional data source

**B1 · The full RBI ODI register (highest value)**
This file covers 186 UINs for 28 parents. Merging the complete ODI register
would (i) let C-F008's vintage shift be estimated on thousands of
registrations rather than 184, (ii) provide the level-0 stake that is missing
here, (iii) allow the "entities per registration" multiplier to be estimated
outside the top-30 sample, and (iv) validate the UIN decoding in C-F009
directly against RBI's own field definitions.

**B2 · Parent financials (Prowess/CMIE or annual reports)**
Every complexity measure here is unnormalised. Complexity per unit of assets,
per unit of foreign revenue, or per acquisition is the economically meaningful
object. It would also settle whether C-F004's Reliance–Hindalco contrast is
about size, about industry, or about acquisition history.

**B3 · Acquisition event dates (SDC, Bloomberg, or annual reports)**
The single best test of the "acquired stack" explanation running through
C-F002, C-F005 and C-F007: does the holding stack pre-date the Indian
acquisition, or was it built afterwards? If most Dutch and Mauritian layers
were inherited, the story is about M&A; if built afterwards, it is about
structuring choices.

**B4 · Orbis or an equivalent structural database**
Directly addresses C-F016 (20 unobserved intermediaries) and C-F017 (the
level-versus-chain disagreement), and would let measured depth be validated
against an external benchmark — which is the main threat to C-F004.

**B5 · Treaty and IIA network data**
C-F008 is currently a coincidence in time. With bilateral tax-treaty and
investment-treaty coverage by year, the gateway choice could be modelled
properly, with the 2016 India–Mauritius protocol as a candidate shock.

---

## C. Framings that could carry a paper

**C1 · "The registered investment is the tip of the structure."**
Built on C-F001, C-F002 and C-F008. Core claim: outward FDI statistics record
a first-hop jurisdiction that predicts the *size and shape* of everything
downstream, so first-hop-based statistics are not a neutral summary of where
capital ends up. Needs B1.

**C2 · "Corporate complexity as a firm choice."**
Built on C-F003, C-F004 and C-F005. Core claim: two Indian groups of similar
size and sector choose architectures that differ by an order of magnitude in
depth and by 80+ percentage points in conduit exposure, and that choice
predicts something — financing cost, disclosure quality, tax position, or
survival of foreign affiliates. Needs B2 and B3.

**C3 · "What the outward-FDI register cannot see."**
Built on C-F014, C-F015 and C-F016. A measurement paper aimed at the OFBV/IRR
literature: the entities available for valuation are a 14.4% subsample
selected on parent identity, and entity counts are inflated by non-controlling
holdings. Directly serves the parent project.

**C4 · "Round-tripping through the corporate structure."**
Built on C-F010, and currently far too thin (12 entities). Only worth pursuing
with B1, where the round-trip cases would be counted across the whole
register rather than a 28-parent sample.

---

## D. Things deliberately not done, and why

- **No fraud, avoidance, evasion or wrongdoing language anywhere.** Holding
  structures in the jurisdictions measured here are ordinary corporate
  finance. This file measures position and count, and cannot speak to intent,
  tax outcomes or legality.
- **No cross-currency financial aggregation.** `currency` is missing on 63% of
  rows and `units` on 98%, so any pooled sum of assets or equity would be
  meaningless. C-F013 is reported within USD for exactly this reason.
- **No time-series of financial variables.** Only 444 entities have any parsed
  balance sheet and few have more than one year; a panel is not available.
- **No claim that `level` measures true ownership depth.** See C-F017; two
  measures are carried side by side throughout.


---

# Increment 2 additions

Written after reviewing Codex commit `bb67b93`. Directions that duplicate work
already done on that branch have been dropped; what remains is either new or
explicitly complementary.

## E. Highest priority for the parent project

**E1 · Build the duplicate-evidence filter and re-run every financial result.**
Follows directly from my review of X-F017. All 33 same-URL/different-name
clusters share byte-identical `*_evidence` text, so the flag is mechanical:
mark any row whose `equity_evidence` or `total_assets_evidence` string is
shared with another `target_id`. 70 of the 560 valuation-ready rows are
affected. Deliverable: a cleaned ready sample of roughly 460 rows, plus the
gates from X-F012 (`total_assets > 0`, `total_liabilities >= 0`). Everything
financial on either branch should be re-estimated on it.

**E2 · Re-parse the multi-column combined PDFs.** The Tata Communications
evidence line is a garbled OCR capture of a four-column table. That is a
fixable upstream bug, not an irreducible data limit, and it is plausibly the
largest single source of error in the financial layer.

## F. Structural directions opened by increments 1 and 2

**F1 · Largest-subtree test on gateway amplification (was A1, now more urgent).**
C-F018 shows that 43% of the median group's network sits below one node, so
C-F002's amplification numbers may be one subtree each. Recompute
descendants-per-gateway after removing each gateway's single largest child
subtree. If the Netherlands-versus-United States gap survives, C-F002 is about
structuring; if it collapses, it is about acquisition size.

**F2 · Does the name signal transfer across groups?** C-F020 is measured
in-sample. Train the holding-name flag on 27 parents and test on the held-out
one, rotating through all 28. A signal that transfers is a usable proxy for
datasets with names but no ownership edges; one that does not is a description
of these 28 groups' naming habits.

**F3 · Predict descendant count, not just the holder flag.** C-F020 uses a
binary outcome. Holding-named entities have 5.19 mean descendants against 1.14
for unnamed ones. A count model within parent × country would say how much of
the *size* of a subtree the name predicts.

**F4 · Chokepoint vintage.** Combine C-F018 with the UIN year (C-F009): are
single-node chokepoints characteristic of older structures built around one
acquisition, or of newer ones too? This is testable inside the file and would
distinguish "legacy architecture" from "current practice".

**F5 · Independence benchmark for the routing matrix (was A8).** C-F022 and
Codex's X-F007 both describe gateway-to-destination routing. Neither has a null.
Compare each cell against the product of marginals and bootstrap by parent, so
that "Mauritius routes Africa" becomes a tested statement rather than a
description of two groups' subtrees.

## G. Directions now closed

- **A4 (partners at the top, wholly owned below): refuted.** See C-F021. The
  raw gradient is a Reliance composition effect.
- **Sector-by-depth: not estimable.** X-F006 shows 240 of the 242 deep
  manufacturing entities come from two groups. With 28 parents and one dominant
  group per deep sector there is no design that recovers a sector effect here.
- **Sector transition along edges: low yield.** 54% of edges are same-sector
  and the matrix is close to diagonal, because sector is largely inherited from
  the ODI registration. The one informative cell is Financial & Insurance
  Services above Manufacturing (35.9% of that row), which is just the holding
  signature already captured by C-F013 and C-F020.
- **Cross-border edge share: settled by Codex.** X-F008 is the most robust
  structural number on either branch and needs no further work in this file.
