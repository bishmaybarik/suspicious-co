# Canonical results

This document summarizes the first canonical, jointly adjudicated result set.
It describes the 28 parent buckets in the supplied dataset; it does not claim
population representativeness, causal effects, tax motives, illegality, or
current legal control.

## Analytical units

The 3,742 raw rows are source candidates, not firms. They
collapse to 3,567 preferred target-years,
1,834 structural target occurrences,
1,830 parent-scoped normalized
entity candidates, and 1,818 global
normalized candidates. The structural mapping contains 186
UINs, 184 observed level-0 targets, and
28 parent buckets.

## Defensible core results

1. **One mapping channel stands for a variable amount of structure.** The
   186 channels resolve to 1,834
   targets: mean 9.9, median
   2. The distribution is skewed:
   89 channels
   (47.8%) resolve to a single target while
   the ten largest carry 49.2% of targets,
   and 47.5% of targets sit at reported
   level 2 or deeper. This describes the supplied mapping only; the file
   contains no evidence on registration practice or UIN semantics.
2. **Denominators are first order.** Source-panel length reverses parent
   rankings; firm and jurisdiction results use target/entity and parent-balanced
   denominators, never raw rows.
3. **Parent architectures are multidimensional.** Size, geographic breadth,
   reported depth, observed graph distance, branching, stake structure, and
   channel concentration do not collapse to one defensible complexity score.
4. **Dominant channels and large subtrees are common.** The modal UIN contains
   59.7% of targets pooled and
   62.1% under equal-parent weighting.
   Among 24 groups with at least 15 targets, the median largest observed
   subtree contains 43.2% of
   normalized entities below its top node. The median is
   41.7% under a strict DAG
   dominator sensitivity and 50.8%
   when named-but-unscraped parents are admitted as nodes. These are mapping and
   observed-topology estimands, not verified legal chokepoints.
5. **Gateway jurisdictions occupy different network roles.** Dutch observed
   level-0 gateways have a mean of 34.8
   and median of 12.0 downstream
   normalized entities, compared with a parent-equal mean of
   37.1. The Netherlands is
   strictly upstream of 29.4% of
   target paths, but 20.9%
   under equal-parent weighting.
6. **A majority of nonroot edges cross jurisdictions.** The standardized-label
   estimate is 57.6%, the equal-parent
   estimate is 58.7%, and the
   leave-one-parent-out range is 56.1–
   61.8%.
7. **Depth is definition- and parent-sensitive.** Reported level 5+ contains
   342 targets
   (18.6%), but the equal-parent mean is
   7.3% and reconstructed
   distance 5+ is 7.4% of complete
   paths. Reported and reconstructed depth disagree for
   236 complete paths
   (14.0%); Motherson supplies
   88.1% of those mismatches.

## Supporting and negative results

- The Netherlands, United States, and Mauritius are strictly upstream of
  1,140/1,834
  target paths (62.2%), but the
  equal-parent union is only 46.7%.
  This is a descendant-weighted descriptive exposure, not a counterfactual
  detachment estimate.
- 406 nonroot stakes are recorded as zero
  (24.6%). Direct AOC comparisons contradict
  literal zero in every comparable zero case, so control-weighted claims are
  not defensible. The pooled full-ownership depth gap of
  26.4 points shrinks to
  2.3 points with equal-parent
  weighting and 6.1 points when
  Reliance is excluded.
- Only 265/1,834
  targets are valuation-ready at least once. There are
  33 demonstrated same-URL/different-name
  evidence-reuse clusters, and units are blank for
  516/560
  ready rows. The financial layer supports a data-quality result, not financial
  performance inference.

## Excluded from the core narrative

The canonical study excludes sector-depth generalizations, financial-health
rankings, cumulative no-dilution claims, gateway-vintage or policy claims,
regional routing narratives, tiny-jurisdiction leverage rankings, and any tax,
legal, regulatory, misconduct, or intent interpretation. The full disposition
is generated in `outputs/final/tables/14_evidence_classification.*`.
