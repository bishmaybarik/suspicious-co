# Claude outputs

Regenerate everything here with:

```
python3 src/claude/make_claude.py
```

- `tables/` — one `.md` and one `.csv` per table. The markdown copies are the
  committed record; the `.csv` copies are gitignored and exist only for local
  reuse.
- `figures/` — 200-dpi PNGs, one per candidate finding.
- `derived/` — parquet analytical datasets (`entity`, `entity_enriched`,
  `edge`, `path`, `parent`, `parent_country`). Gitignored; rebuilt by
  `02_build_hierarchy.py` onwards.

Nothing in this directory is edited by hand.
