# Claude outputs

Regenerate everything here with:

```
python3 src/claude/make_claude.py
```

- `tables/` — one `.md` and one `.csv` per table. The markdown copies are the
  committed record; the `.csv` copies are gitignored and exist only for local
  reuse.
- `figures/` — 200-dpi PNGs, one per candidate finding (fig01–08 from
  increment 1, fig09–12 from increment 2).
- `derived/` — parquet analytical datasets (`entity`, `entity_enriched`,
  `edge`, `path`, `parent`, `parent_country`). Gitignored; rebuilt by
  `02_build_hierarchy.py` onwards.

Tables prefixed `review_` are independent reproductions of findings on the
Codex branch; see `research/reviews/`.

Nothing in this directory is edited by hand.
