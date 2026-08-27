# Final release audit

**Scope.** Independent audit of the canonical synthesis produced in commit
`3653505` (`research(synthesis): build canonical analysis and draft paper`,
Codex/GPT-5.6 Sol), plus the completion and repair work carried out in this
increment by Claude Opus 5.

**Date:** 2026-08-27.
**Input audited:**
`~/.agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta`,
SHA-256 `65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea`
(verified by the pipeline before any output is written; the file was never
modified).

---

## 1. Status of the canonical pipeline

**Working, and reproducible from a clean state.** The audit deleted
`outputs/final/`, `RESULTS.md`, `REPLICATION.md`, and every LaTeX build
artifact, then ran the documented commands verbatim. All three stages
completed with exit code 0.

The pipeline was read in full (`config.py`, `data_model.py`, `statistics.py`,
`rendering.py`, `figures.py`, `run_pipeline.py`, `validate.py`) and checked
against the two adjudication documents on every dimension the protocol
requires:

| Dimension | Finding |
|---|---|
| Unit of observation | Six units are constructed and kept separate: source rows (3,742), preferred target-years (3,567), target occurrences (1,834), parent-scoped entities (1,830), global entities (1,818), parent buckets (28). No table substitutes one for another. **Correct.** |
| Entity/path definitions | Parent-scoped key is parent × standardized country × punctuation-normalized name; global key drops the parent. A path is complete only when recursion reaches the Indian root through observed entities (1,687). **Correct, and matches the adjudicated definitions.** |
| Denominators | Every generated audit table carries numerator, denominator, value, and unit. An independent check of all such triples in tables 08, 09, and 10 found **one** inconsistency (the repeated-signature row reported a cluster count against a row-based percentage); it is **fixed** in this increment. |
| Duplicate treatment | Structural fields are asserted invariant within `target_id` before rows are collapsed; the assertion is live and would abort the build. Global-vs-parent-scoped entity counts are reported side by side rather than reconciled by assumption. **Correct.** |
| Hierarchy construction | Conservative alias matching within the parent bucket, lexicographic candidate ranking, no fuzzy match, ambiguity preserved as an explicit node type. Named-but-unscraped parents are retained as unresolved nodes with their supplied countries (18 nodes, 78 edges) — this is the §0 correction of the adjudication round, and it is implemented in the canonical builder, not only in the adjudication scripts. **Correct.** |
| Parent weighting | Equal-parent estimands compute the within-parent statistic first, then average over the 28 buckets; leave-one-parent-out repeats the pooled or fixed-effect estimator. Fixed-effect coefficients residualize treatment as well as outcome (the estimator error caught during adjudication is not present). **Correct.** |
| Financial weighting | Absolute monetary values are never pooled. Units are blank for 516 of 560 ready rows, and no value-weighted structural statistic is computed anywhere. **Correct, and the non-estimability is stated in the paper.** |
| Robustness calculations | The robustness matrix carries pooled/primary, equal-parent or FE, LOO range, and a labeled alternative definition for twelve estimands, with blanks where an estimand does not apply. **Correct.** |
| Final tables and figures | See §6 and §7 below. |

### Independent recomputation

The following were recomputed directly from the Stata input with code written
for this audit, not through the canonical pipeline, and matched exactly:
3,742 rows; 1,834 targets; 186 UINs; 28 parents; 184 level-0 targets; 1,650
nonroot edges; 871 targets at level 2+; 342 at level 5+; 406 zero stakes;
3,567 preferred rows; 560 ready rows; 948 raw-label cross-border edges;
1,095 modal-UIN targets (59.71% pooled, 62.05% equal-parent, 61.16% median);
24 parents with at least 15 targets; 508 manufacturing targets of which 242 at
level 5+ and 240 from two parents; and targets per UIN of mean 9.86, median 2,
89 single-target channels, top-ten share 49.2%.

An independently written graph builder (target-level, different alias rule, no
unresolved nodes) reproduced the substantive magnitudes: Dutch gateway mean
33.5 / median 11 against the canonical 34.8 / 12, and a largest-subtree median
of 43.1% against the canonical 43.2%. The differences are within the
documented definitional band and do not change any statement in the paper.

## 2. Validation status

**Passing, and materially stronger than at handoff.**

`python -m src.analysis.validate` rebuilds the entire analysis into a
temporary directory and byte-compares the result. At handoff it covered 61
outputs and deliberately excluded figure PDFs, whose bytes carried a run-time
creation timestamp. Figure PDFs are now written without that timestamp, so the
validator covers **73 outputs**, including every figure in both formats, and
`outputs/final/manifest.json` is now stable across rebuilds instead of churning
on every run.

The pipeline also asserts twenty-odd central invariants (counts, edge and path
totals, mismatch counts, and five point estimates to 1e-8) before writing any
reported output.

## 3. Central findings verified

Each of the following is in the paper, is reproduced by the canonical
pipeline, and was classified Core or Supporting by **both** independent
adjudications:

1. **Denominators are first order.** Tata Communications is the largest group
   by source rows (550) and roughly a sixth the size of Motherson by network
   entities (49 against 309). Ranking reversal verified.
2. **One mapping channel stands for a variable amount of structure.** 186
   channels resolve to 1,834 targets; mean 9.9, median 2; 89 channels (47.8%)
   resolve to one target; the ten largest carry 49.2%; 184 of 186 have an
   observed first hop and none has more than one. Verified independently.
3. **Networks are concentrated.** Modal channel 59.7% pooled / 62.1%
   equal-parent; median largest observed subtree 43.2%, 41.7% under a strict
   DAG dominator, 50.8% admitting named unresolved nodes. Concentration takes
   the form of layering rather than branching: 78.0% of entities hold nothing,
   49.1% of holders hold exactly one entity, and 34 hubs originate 47.2% of the
   edges beginning at an observed entity.
4. **First-hop jurisdiction predicts downstream reach.** Dutch gateways mean
   34.8 / median 12 across 13 gateways and 12 parents; parent-equal mean 37.1;
   LOO 21.2–39.7; no-majority-branch subset 37.8. United States: 28 gateways,
   mean 9.9, median 1.5. Ordering survives parent balance and omission.
5. **A majority of nonroot edges cross jurisdictions.** 951/1,650 (57.6%);
   equal-parent 58.7%; LOO 56.1–61.8%; raw-label sensitivity 57.5%. The most
   definition-stable statistic in the study.
6. **Depth is two variables, not one.** Reported level 5+ is 18.6% pooled but
   7.3% equal-parent; reconstructed distance 5+ is 7.4% of complete paths; the
   measures disagree for 236/1,687 complete paths and one parent supplies
   88.1% of the disagreements.
7. **Negative results.** Deep manufacturing is 240/242 from two parents; the
   pooled full-ownership depth gap of 26.4 points falls to 2.3 equal-parent and
   6.1 excluding one parent; the financial layer supports a data-quality result
   only (14.4% of targets ever ready, 92.1% of ready rows without units, 33
   demonstrated evidence-reuse clusters).

## 4. Qualifications attached to the above

- Every result describes the 28 supplied parent buckets. There is no sampling
  frame, and no result is generalized to Indian outward investment.
- Subtree and dominator statistics are properties of the reconstructed mapping,
  not verified legal control. The paper uses "largest observed subtree", never
  an unconditional chokepoint counterfactual.
- Upstream-path exposure counts a shared ancestor once per descendant; the
  unique-node estimand is reported beside it wherever the path estimand
  appears (62.2% versus 46.7% equal-parent for the three-country union; 61.8%
  versus 38.0% for the maintained-centre category).
- Gateway amplification is stated one estimand at a time. The Dutch/US ratio is
  about 3.5 on means and about 8 on medians, and the paper says so rather than
  quoting a single multiple.
- Descendant counts cannot distinguish an inherited acquisition structure from
  a constructed one; the paper states this explicitly and draws no inference.

## 5. Remaining fragile or unresolved claims

None is asserted as a finding. All appear either as labeled sensitivities or in
the generated disposition table.

| Item | Status in the release |
|---|---|
| Fixed 19-jurisdiction "centre" exposure | **Fragile.** Presented in a subsection titled "Why a fixed centre category is not a core result", always beside the unique-node estimand, and flagged as an imposed classification. |
| Three-country descendant cover | **Descriptive.** Always quoted with the equal-parent union and the fund-excluded alternative. |
| Cumulative no-dilution along paths | **Excluded.** The paper states that cumulative ownership is not computed because it would condition on positive recorded stakes. |
| UIN substring semantics and vintage | **Unresolved and unused.** No office, type, or year reading appears anywhere; the register-expansion result is stated as a property of the supplied mapping only. |
| Tiny-jurisdiction leverage (Jersey, Estonia, Cyprus) | **Not promoted.** Figure 5 now labels only jurisdictions appearing on at least five parents' paths, and the caption says why. |
| Sector–depth association | **Rejected**, and reported as a rejected hypothesis. |
| Financial health by depth or jurisdiction | **Rejected**, and reported as a rejected hypothesis. |
| Any tax, treaty, legal, regulatory, or misconduct reading | **Out of scope.** Table 7 states the boundary; no such language appears in the paper. |

## 6. Tables checked

All fourteen generated tables plus the seven paper views and the appendix views
were inspected in CSV and in the compiled PDF.

- **Fixed:** integer-valued counts were printing as floats ("13.0", "33.0",
  "45.0") in four paper tables; `human_number` now formats any whole-numbered
  value as an integer.
- **Fixed:** the repeated-signature row of the financial audit reported a
  cluster count as numerator against a row-share percentage. It is now
  "Parsed rows sharing a numeric signature", 104/863, with the cluster count in
  the unit label.
- **Fixed:** Table 6 (robustness) was scaled down to near-illegibility. It is
  now set at `\scriptsize` at natural width in landscape.
- **Added:** Table 7, the evidence boundary, generated by the pipeline so that
  the boundary travels with the results rather than with the prose.
- **Checked and unchanged:** the denominator ladder, parent examples, gateway
  amplification, jurisdiction roles, financial audit, depth audit, ownership
  audit, and evidence classification. Every numerator/denominator/percentage
  triple in the audit tables is now internally consistent.

## 7. Figures checked

All eight figures were inspected as rendered images and in the compiled PDF.

- **Figure 1b:** previously plotted raw counts on two different denominators
  (1,834 targets against 1,687 complete paths) on a shared axis. Now plots each
  measure as a share of its own denominator.
- **Figure 2:** labels were ambiguously offset and one was clipped at the axis
  edge. Every label now carries a leader line, offsets are set so no leader
  crosses another marker, and the axis has right-hand margin.
- **Figure 4:** the jurisdiction label "Ifsc Gift City" is now "IFSC GIFT City".
- **Figure 5:** labels are now restricted to jurisdictions appearing on at
  least five parents' paths, so that one- and two-parent leverage cells are not
  visually promoted; the caption states the rule.
- **Figure 7b:** bars were ordered 560, 521, 105, 460, breaking the funnel
  reading. Now ordered by count.
- **Figure 8:** the largest-observed-subtree row was missing from the lead
  robustness figure although it is a core estimand; it is now included.
- **Captions:** seven captions repeated the in-figure title verbatim. Captions
  now state what is plotted and on what unit; the in-figure titles keep the
  released images self-describing.
- **Figures 3 and 6** were already sound and are unchanged apart from float
  placement.

No figure was found to use a misleading scale. Log and symlog axes are labeled
as such.

## 8. Paper compilation status

**Clean.** `pdflatex -interaction=nonstopmode -halt-on-error` run three times
from a deleted auxiliary state produces a 29-page PDF with **zero** warnings:
no `Overfull`, no `Underfull`, no `LaTeX Warning`, no unresolved references.

At handoff the documented build used two passes and left
`LaTeX Warning: Label(s) may have changed` — cross-references were stale. A
third pass is required and is now documented in `REPLICATION.md`, in the
reproducibility appendix, and in the audit commands above. The remaining
underfull boxes in the wide `p{}` columns were removed by setting those columns
ragged-right.

Every page of the compiled PDF was inspected. Two spacing defects introduced
during revision (a percent macro absorbing the following space) were found by
inspection and fixed.

## 9. Paper content changes made in this increment

The audit found the analysis sound but the paper incomplete in one substantive
respect and thin in several rhetorical ones.

- **Added the register-expansion result** (adjudicated Core by both agents,
  absent from the draft): 186 channels expand into 1,834 targets, median 2,
  with the skew and the two channels lacking an observed first hop. It is now
  the paper's motivating fact and gives the title its meaning.
- **Added the layering-versus-branching result** (adjudicated Supporting by
  both agents, absent from the draft), with the hub statistics and the caveat
  that two of the three largest hubs are named investment funds.
- **Rewrote the introduction** around a stated central question, with the
  contributions, the four positive results, the three negative results, and a
  section roadmap.
- **Added a subsection defining the hierarchy** before the graph mechanics, so
  that a reader knows what a level and a path are before reading estimands.
- **Added the evidence-boundary table and an open-questions subsection**
  naming the four questions this file cannot settle.
- **Added a measurement-implications section** stating the three consequences
  that follow without institutional assumptions.
- **Strengthened interpretation** in the gateway section with the competing
  readings (acquisition inheritance, financing, governance, operating
  location, mapping attribution) and the statement that the data cannot
  separate them.
- Added connective text between every pair of adjacent sections.

No claim was added that is not generated by the pipeline. No external source,
citation, or institutional fact was introduced.

## 10. Remaining limitations

These are properties of the evidence base, not defects of the release.

1. **True ownership distance is unresolved.** Reported level and reconstructed
   graph distance disagree for 14.0% of complete paths, concentrated in one
   parent. External ownership charts are the only resolution. This is the
   largest single threat to any depth statement, and every depth statement is
   labeled by measure because of it.
2. **Legal identity is unresolved.** Normalized name–country keys are
   candidates without registration identifiers or effective dates.
3. **Recorded zero stakes are uninterpretable.** 406 nonroot relations record
   exactly zero and every comparable case with an independent shareholding
   field contradicts a literal zero, so no control-weighted network statistic
   is available.
4. **The financial layer cannot support performance inference.** Coverage is
   14.4% of targets, parent coverage ranges from 0% to 92%, units are missing
   for 92.1% of ready rows, and 33 clusters demonstrably reuse identical
   extracted evidence across differently named targets.
5. **There is no sampling frame.** 28 parent buckets support parent-weighted
   description and omission sensitivity; they do not support population
   inference, sector effects, or regressions with covariates.
6. **Point estimates carry no confidence intervals.** With 28 groups and no
   probability sample, the paper reports sensitivity to measurement and
   composition instead of sampling-error inference. A parent bootstrap around
   the concentration medians would strengthen a submission and is not done
   here.
7. **The "financial centre" partition remains imposed.** No test in this file
   can separate a holding jurisdiction from an operating one without
   circularity; the name-based proxy is a partial substitute only.

## 11. What a sourced revision would need

Ranked by how much a negative answer would change the paper: dated ownership
charts for the two groups that drive the depth disagreement; company
registration identifiers to freeze one entity key; an authoritative
specification for the mapping identifiers; dated stake sources that distinguish
unknown from zero; acquisition histories to separate inherited from constructed
structure; unit- and currency-resolved financial extraction; and a documented
sampling frame.

---

READY FOR HUMAN REVIEW
