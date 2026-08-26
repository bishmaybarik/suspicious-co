You are performing one autonomous research collaboration increment.

Read, in this order:

1. your repository-specific agent instructions;
2. RESEARCH_PROTOCOL.md;
3. your own research/<agent>/STATE.md;
4. your own FINDINGS.md and IDEAS.md;
5. relevant recent Git history.

The orchestration message supplied with this prompt tells you:

- which research cycle this is;
- the other agent's remote branch;
- the latest commit currently available from that agent.

Do not merge, rebase, cherry-pick, checkout, switch to, or modify the other
agent's branch.

Inspect it using read-only Git operations such as git log, git show and
git diff.

Your objective in this cycle has THREE components.

==================================================
1. CROSS-AGENT REVIEW
==================================================

Identify the most important new work produced by the other agent since the
last commit you recorded as reviewed in STATE.md.

Select the highest-value claims rather than mechanically reviewing everything.

For substantive claims, independently reproduce them from the canonical
research data.

Check, where applicable:

- exact denominator;
- unique entities versus ownership paths;
- duplicates;
- ultimate-parent definitions;
- parent weighting versus entity weighting;
- whether one corporate group dominates;
- leave-one-parent-out robustness;
- missing-data sensitivity;
- hierarchy/depth mechanics;
- financial weighting versus simple entity counts;
- alternative reasonable definitions.

Classify reviewed findings as:

CONFIRMED
PARTIALLY CONFIRMED
FRAGILE
DATA ARTIFACT
NOT REPRODUCIBLE
INTERESTING BUT NEEDS EXTERNAL VALIDATION

Record useful reviews under research/reviews/.

==================================================
2. NEW EMPIRICAL EXPLORATION
==================================================

Do not spend the entire cycle reviewing.

Use what both agents already know to avoid unnecessary duplication and push
the research frontier forward.

Search for high-value empirical patterns that have not yet been adequately
studied.

Possible dimensions include, when supported by the data:

- numbers of subsidiaries;
- unique legal entities;
- foreign versus domestic structure;
- jurisdiction concentration;
- HHI and entropy;
- ownership depth;
- branching;
- geography by hierarchy depth;
- country-to-country ownership transitions;
- recurrent ownership-path motifs;
- intermediate jurisdictions;
- foreign-intermediated structures;
- parent-group heterogeneity;
- structural complexity;
- financial value by geography;
- financial value by ownership depth;
- discrepancies between entity counts and economic importance;
- unusual combinations of structural and financial variables;
- temporal restructuring if dates exist;
- clustering or taxonomies of corporate structures.

These are examples, NOT a checklist.

Actively invent better analyses when the actual data suggests them.

For promising new findings, try to falsify them yourself before promoting
them.

Prioritize:

1. surprise;
2. robustness;
3. economic meaning;
4. interpretability;
5. potential contribution to a research paper.

Do not manufacture novelty by trying hundreds of arbitrary specifications.

==================================================
3. RESEARCH CONSOLIDATION
==================================================

Improve the project's existing outputs rather than endlessly creating new
disconnected files.

Where appropriate:

- refine existing tables;
- improve visualisations;
- consolidate duplicate analyses;
- strengthen robustness;
- improve documentation;
- turn strong candidate findings into well-defined research facts.

Every important statistic must remain reproducible from code.

Update:

research/<agent>/STATE.md
research/<agent>/FINDINGS.md
research/<agent>/IDEAS.md

Record the exact other-agent commit SHA reviewed in STATE.md.

Use your own agent-specific source and output directories unless the project
has explicitly entered synthesis.

Do not claim illegality, fraud, tax evasion, corruption, wrongdoing or abuse
based solely on unusual corporate structure.

Do NOT commit, push, merge, rebase or modify Git history.

Complete ONE coherent and substantial research increment, then stop.

Before stopping, write one concise Git commit subject describing what was
actually accomplished to:

.agent_runtime/commit_message.txt
