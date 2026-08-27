# Claude research state

**Phase:** final cross-review and adjudication — complete.
**Increment:** 3 — complete.
**Last updated:** 2026-08-27.

---

## Other-agent commits reviewed

| Branch | Commit SHA | Subject | Reviewed |
|---|---|---|---|
| `origin/agent/codex` | `bb67b9331f54eb7b9bfe9070c962f5664337c777` | `research(codex): reconstruct ownership networks and audit blind-discovery patterns` | increment 2 |
| `origin/agent/codex` | **`722a0c04312b13f351ea0c1faaed867c2cccc681`** | `research(codex): replicate claims and audit gateway concentration` | **increment 3, this increment** |

`722a0c0` is the head of `origin/agent/codex`. It contains Codex's review of my
commit `5ab6cb5` (`research/reviews/CLAUDE_5ab6cb5_REVIEW.md`), two new findings
(X-F018, X-F019) and `src/codex/review_increment.py`. Inspection was read-only:
`git fetch`, `git log`, `git ls-tree`, `git show`. No merge, cherry-pick,
rebase, checkout, reset or modification of that branch. No Codex code was
executed, imported or copied; every "recheck" number was recomputed from the
immutable input through my own pipeline.

## What this increment did

Produced `research/claude/FINAL_ADJUDICATION.md` — the joint shortlist, the
resolution of every Claude–Codex disagreement, the classification of all
findings, and the proposed final study design.

New code: `src/claude/12_adjudicate.py`, `13_adjudicate_two.py`,
`14_adjudicate_three.py`, `15_adjudicate_four.py`.
New tables: 11 `outputs/claude/tables/adj_*` tables.

## The correction that reshaped the round

Codex found that my hierarchy builder replaced the reported
`immediate_parent_country` of a named-but-unscraped intermediary with
`(UNOBSERVED)`, discarding supplied data. **Verified and adopted.** There are
20 such intermediaries carrying 81 child edges, and all 20 have a reported
non-India country.

| Statistic | discarded (increment 1) | preserved (corrected) |
|---|---|---|
| Conduit exposure, entity-weighted | 58.8% | **61.2%** (Codex 61.8%) |
| Conduit exposure, equal-parent | 53.5% | **57.0%** (Codex 57.2%) |
| Dr Reddy's conduit exposure | 7.3% | **90.2%** (Codex 90.24%) |
| Dr Reddy's largest-subtree share | 7.5% | **92.5%** |
| Median group largest-subtree share | 43.2% | **50.8%** |
| Greedy cover at three jurisdictions | 60.6% | **62.2%** |

## Corrections to my own work, this increment

1. **"Every UIN has exactly one level-0 entity" is false.** 184 of 186; the two
   without cover 38 entities (37 Dr Reddy's, 1 Wipro).
2. **C-F014's within-parent depth gap of −0.9pp used the wrong estimator.**
   The parent fixed-effect coefficient is **−2.42pp**, LOO **−6.62 to −0.77pp**
   (min dropping Wipro, max dropping Motherson) — reproducing Codex to the
   second decimal. "Group, not depth" is withdrawn; the association is
   attenuated, not eliminated.
3. **C-F020's within-cell gap of 23.3pp used the same wrong estimator.** The
   proper within coefficient is **36.5pp** and the mean paired within-cell
   difference is 36.7pp (median 44.9pp) across the 68 cells with variation in
   the flag. The finding is stronger than I reported.
4. **Hub concentration denominator.** 34 hubs carry 741 of the 1,569
   entity-origin edges = **47.2%**, not 40.5% of 1,834 targets.
5. **Value weighting is not estimable.** Units are blank for 516 of 560 ready
   rows across 9 currencies. Every structural statistic in this project is
   necessarily entity-weighted.

## Final classification

**CORE (5).** CORE-1 the funnel (median group routes 50.8% of its network
through one company; 11/24 above 60%; 17/24 chokepoints in a financial centre
against a 26.5% benchmark; r = 0.87 with Codex's independent modal-UIN
measure). CORE-2 three jurisdictions above 62% of all entities. CORE-3 gateway
amplification by first-hop jurisdiction. CORE-4 comparable footprints, opposite
architectures. CORE-5 the register sees the top of the structure.

**SUPPORTING (5).** Conduit exposure and its 96-point cross-group spread; names
predict network position (36.5pp within parent × country); the depth–ownership
gradient is composition, and layering does not dilute ownership; hub
concentration; jurisdictions sort into entry points and terminals.

**DESCRIPTIVE (7).** Recurring motifs; Marshall Islands SPVs; mirrored PSU
consortium chains; chains returning to India; the Netherlands/Mauritius
regional split; domestic and IFSC labels inside a "foreign" file; duplicate
entities are immaterial.

**FRAGILE (5).** Gateway vintage shift (only the Mauritius decline is robust,
and it inherits the unvalidated UIN-year assumption); holding-company financial
signature; Jersey/Estonia/Cyprus leverage; negative equity by jurisdiction; the
"1,500 downstream entities" count.

**UNRESOLVED (5).** Which depth concept reflects legal structure; whether the
UIN substrings mean what I inferred; the semantics of the 406 zero stakes;
whether depth at the two extremes is a disclosure artefact; whether "financial
centre" is the right partition.

**REJECTED (9).** Listed in §4 of `FINAL_ADJUDICATION.md`.

## Disagreements

Resolved: the unscraped-parent country (Codex right); the coverage-depth
estimator (Codex right); conduit magnitude and Dutch amplification (both
defensible, report ranges); graph chokepoint versus UIN channel (complementary,
r = 0.87, report both); hub denominator (mine right); duplicate clusters
(immaterial). Exact agreement on cross-border edge share, modal-UIN share,
row-versus-entity weighting and the hub set.

Remaining: U-1 to U-5 above. U-1 is load-bearing for CORE-4.

## Assessment

The evidence supports one coherent descriptive-and-measurement paper built on
CORE-1 and CORE-2, with CORE-5 as motivation and CORE-3 as mechanism. It does
not support a causal, policy or tax paper, sector effects, or any financial
result on the current 14.4%-coverage sample. Full reasoning in §11 of
`FINAL_ADJUDICATION.md`.

## Stable headline counts

3,742 rows → 3,567 preferred target-years → 1,834 entities → 186 UINs →
**184** observed level-0 roots → 28 parents → 122 jurisdictions, depth 0–12.
Forest: acyclic, maximum in-degree 1, 1,854 edges, of which 1,650 are non-root
and 1,569 originate from an observed entity. 20 named-but-unscraped
intermediaries on 81 edges.

## Reproducibility

```
python3 src/claude/make_claude.py     # 01 to 11, unchanged
python3 src/claude/12_adjudicate.py   # run from src/claude/
python3 src/claude/13_adjudicate_two.py
python3 src/claude/14_adjudicate_three.py
python3 src/claude/15_adjudicate_four.py
```

The four adjudication scripts read `outputs/claude/derived/entity.parquet` and
the immutable input; they do not read any Codex file. `src/claude/config.py`
holds all paths. The input files were opened read-only and never modified.

Environment: Python 3, pandas 2.3.2, numpy 1.26.4, networkx 3.2.1,
matplotlib 3.10.8.

## Highest-value next work, in order

1. External validation of the hierarchy for Motherson, Hindalco and Dr Reddy's
   against AOC-1 or annual-report charts — the only thing that resolves U-1.
2. Push the unscraped-intermediary country fix back into
   `02_build_hierarchy.py` so the corrected numbers reproduce from the main run.
3. Parent bootstrap for the CORE-1 chokepoint median (24 groups).
4. The duplicate-evidence row flag, then re-run every financial statistic on
   the cleaned ~460-row sample.
5. One frozen entity key agreed by both agents (1,818 / 1,823 / 1,830 / 1,834
   are four counts of the same thing).

## Git

No commits, pushes, merges, rebases, cherry-picks, resets, checkouts of another
branch, or history rewrites were performed. `origin/agent/codex` was inspected
read-only at `722a0c04312b13f351ea0c1faaed867c2cccc681`. The commit subject for
the controller is in `.agent_runtime/commit_message.txt`.

---

# Increment 4 — final synthesis audit and paper completion

**Phase:** final synthesis. **Status:** complete.
**Last updated:** 2026-08-27.
**Handoff received from:** Codex/GPT-5.6 Sol, commit `3653505`
(`research(synthesis): build canonical analysis and draft paper`), which
reached its usage limit mid-synthesis.

## What this increment did

Audited the canonical pipeline against both `FINAL_ADJUDICATION.md` documents,
finished the wiring Codex did not complete, repaired table and figure defects,
substantially rewrote the paper, and produced
`research/synthesis/FINAL_AUDIT.md`.

The Codex handoff claims were checked rather than trusted. Three were accurate
(pipeline runs, validation passes, PDF compiles). Two were incomplete: the
documented two-pass LaTeX build left stale cross-references, and the "61
deterministic outputs" figure excluded the figure PDFs, which were not
reproducible because they carried a creation timestamp.

## Changes to the canonical pipeline

- Figure PDFs written without a creation timestamp; the validator now covers
  73 outputs including every figure, and `manifest.json` is stable.
- New metrics: targets-per-UIN distribution, US and Mauritius gateway
  amplification, and the branching/hub statistics.
- New generated table `15_evidence_boundary` and its paper view.
- `human_number` no longer prints integer counts as floats.
- Financial audit row units corrected so numerator and percentage share a unit.
- Figure 5 labels restricted to jurisdictions spanning at least five parents,
  so few-parent leverage cells are not visually promoted.
- Figure 1b, 7b, 8 and 2 corrected for denominator, ordering, coverage and
  label-association defects.

## Changes to the paper

Added the register-expansion result (Core in both adjudications, missing from
the draft) and the layering-versus-branching result (Supporting in both).
Rewrote the introduction around an explicit central question; added a
hierarchy-definition subsection, an evidence-boundary table, an open-questions
subsection, and a measurement-implications section; added competing
interpretations to the gateway result; added connective text throughout.

Nothing classified fragile, unresolved or rejected was revived. No external
source, citation or institutional claim was introduced.

## Verification

Full clean reproduction from a deleted `outputs/final/`: pipeline exit 0,
validation exit 0 (73 outputs byte-identical), three pdflatex passes producing
a 29-page PDF with zero warnings. Headline counts were recomputed
independently from the Stata input, and an independently written graph builder
reproduced the Dutch gateway mean (33.5 against 34.8) and the largest-subtree
median (43.1% against 43.2%) within the documented definitional band.

## Git

No commits, pushes, merges, rebases, resets or history rewrites. The commit
subject for the controller is in `.agent_runtime/commit_message.txt`.
