# Claude research state

**Phase:** cross-agent review and continued independent exploration.
**Increment:** 2 — complete.
**Last updated:** 2026-08-26.

---

## Other-agent commits reviewed

| Branch | Commit SHA | Subject | Reviewed |
|---|---|---|---|
| `origin/agent/codex` | `bb67b9331f54eb7b9bfe9070c962f5664337c777` | `research(codex): reconstruct ownership networks and audit blind-discovery patterns` | 2026-08-26, this increment |

This is the only commit on `origin/agent/codex` ahead of `main`
(`29109a3`). It is the first Codex commit I have inspected; nothing on that
branch was read during increment 1. No Codex code was executed, imported or
copied — only the numeric claims in `research/codex/FINDINGS.md` were used as
reproduction targets, and every statistic was recomputed from the immutable
input through my own pipeline.

## What this increment did

1. **Reviewed eight Codex findings.** Reproduced each from the raw input and
   classified it. Written to `research/reviews/` with a machine-readable
   ledger at `outputs/claude/tables/review_codex_reproduction_ledger.md`.
2. **Corrected one of my own rules** as a result of the review (see below).
3. **Opened five new lines of enquiry** that neither branch had investigated,
   recorded as C-F018 to C-F022 in `FINDINGS.md`.
4. Added four figures and 18 tables; the whole pipeline still rebuilds with
   one command.

## Review verdicts

| Codex finding | Verdict | Note |
|---|---|---|
| X-F001 raw rows misweight parent exposure | CONFIRMED | reproduces exactly; Tata Communications is 1st by rows and 11th by entities |
| X-F006 deep hierarchy is parent-driven | CONFIRMED | every number exact; disciplines my C-F004 |
| X-F007 Netherlands and Mauritius as intermediaries | CONFIRMED | survives the unique-node and leaf-only tests Codex proposed but did not run |
| X-F008 most non-root edges cross jurisdictions | CONFIRMED | 948/1,650 vs 951/1,650; I adopted Codex's exclusion of level-0 edges |
| X-F010 zero stakes are not literal zero | CONFIRMED | 7/7 contradicted by AOC-1; forced a correction to my own filter |
| X-F012 ready rows need extra gates | CONFIRMED | reproduces to the row |
| X-F014 US concentration is denominator-sensitive | PARTIALLY CONFIRMED | motif share is 49–61% depending on path definition |
| X-F017 repeated balance-sheet signatures | CONFIRMED, sharpened to DATA ARTIFACT | all 33 same-URL clusters have byte-identical evidence text |

## Corrections to my own increment-1 work

1. **Minority-stake filter (C-F015).** My 10% floor deleted the 406 entities
   whose stake is recorded as the zero *code*. Corrected rule: apply a minority
   filter only to entities with a **strictly positive** recorded stake. The
   minority set falls from 481 entities to **75**. Recorded in
   `outputs/claude/tables/corrected_minority_filter.md`.
2. **Cross-border edge share.** My increment-1 figure of 64.1% included the
   level-0 India-to-foreign edges, which cross by construction. The correct
   denominator is non-root edges only: **57.5%**.
3. **Idea A4 refuted.** I predicted "partners at the top, wholly owned below".
   The raw 15.7-point gradient is 2.0 points within parent and vanishes
   entirely once Reliance is excluded. Recorded as part of C-F021.
4. **Negative equity by jurisdiction downgraded.** My increment-1 note that
   Mauritius shows 53.8% negative equity (n = 13) should be read with the
   caution Codex applies in X-F012; negative book equity is ordinary in
   loan-funded holding companies.

## New findings this increment

| Code | Claim | Robustness |
|---|---|---|
| C-F018 | median large group routes 43% of its foreign network through one company; ten route over 60% | high; correlation with gateway count is only −0.35, so not mechanical |
| C-F019 | Netherlands, United States and Mauritius sit above 61% of all 1,834 entities | high; equal-parent and leave-one-parent-out reported per jurisdiction |
| C-F020 | a holding-type name predicts holding behaviour by 23pp *within* parent × country cells | high; LOO 45–49pp raw; precision 64%, recall 28% |
| C-F021 | layering does not dilute ownership (median cumulative 100%); the depth gradient in stakes is a composition effect | medium; chain-completion selection stated on the figure |
| C-F022 | the Netherlands and Mauritius split the world regionally as gateways | medium; strong only on multi-parent routes |

## Stable headline counts (unchanged)

3,742 rows → 1,834 entities → 186 UINs → 28 parents → 122 jurisdictions,
depth 0–12. Forest: acyclic, maximum in-degree 1, 1,854 edges.

## Reproducibility

```
python3 src/claude/make_claude.py
```

Runs `01_audit_rows` → `02_build_hierarchy` → `03_analyse_hierarchy` →
`04_analyse_jurisdiction` → `05_analyse_coverage_financials` →
`06_audit_uin_structure` → `07_make_figures` → `08_review_codex` →
`09_analyse_chokepoints` → `10_analyse_names_and_stakes` →
`11_make_figures_increment2`. Rebuilt from clean this increment: 59 tables and
12 figures. `src/claude/config.py` holds all paths; no script uses a relative
path or `cd`. The input files were opened read-only and never modified.

Environment: Python 3, pandas 2.3.2, numpy 1.26.4, networkx 3.2.1,
matplotlib 3.10.8.

## Limitations carried into increment 3

1. Any pooled depth statistic in this file is a statement about two groups
   (X-F006). Sector-by-depth claims are not estimable with 28 parents.
2. The valuation sample is contaminated in two independent ways: 39 of 560
   ready rows fail basic sign checks, and 70 carry a balance sheet shared with
   another target. The usable sample is closer to 460.
3. Chain-completion selection limits the cumulative-ownership work (C-F021).
4. The UIN decoding (C-F009) remains an inference from three consistency
   checks, not documented metadata.
5. Jersey, Estonia and Cyprus appear as high-leverage jurisdictions on one to
   five parents each; they are single-group facts until more parents are added.

## Next increment — planned order

1. **Duplicate-evidence filter as a deliverable.** Build the row-level flag
   (`*_evidence` text shared with another target) and re-run every financial
   statistic on the cleaned sample. This is the highest-value item for the
   parent project and follows directly from my X-F017 review.
2. **A1 largest-subtree test** on gateway amplification (C-F002), now more
   pressing because C-F018 shows how much of each network sits in one subtree.
3. **A8 transition matrix against an independence benchmark** with parent
   bootstrap, to put C-F007 and C-F022 on a statistical footing.
4. **Extend C-F020**: test whether the name signal predicts *descendant count*
   and not merely the binary holder flag, and whether it transfers across
   groups (train on 27 parents, test on the held-out one).

## Git

No commits, pushes, merges, rebases, cherry-picks, checkouts of another
branch, or history rewrites were performed. `origin/agent/codex` was read via
`git show` and `git log` only. The commit subject for the controller is in
`.agent_runtime/commit_message.txt`.
