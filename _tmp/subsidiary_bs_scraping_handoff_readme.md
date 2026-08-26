# Subsidiary Balance-Sheet and Cash-Flow Scraping — Handoff

Last updated: 2026-08-26. This replaces all earlier versions of this note; earlier
figures in previous revisions are stale, use the numbers here.

---

## 1. What this is for

A subsidiary-level financial dataset for the RBI ODI project, covering the top
Indian parents and their foreign subsidiaries, to be used later for IRR/XIRR
construction. The IRR framework itself lives in `_tmp/xirr_cashflow_framework.md`.

**The current task is scraping and extraction only. Do not compute IRR here.**

What the IRR work actually needs from this dataset is the **book-value net worth**
(`equity`) per subsidiary-year, for the OFBV valuation. Transaction-level
remittances, disinvestments and dividends are *not* recoverable from subsidiary
PDFs and must come from the APR/transaction data and be merged later. The P&L and
cash-flow variables here are supplementary.

Ground rule carried through all of this work: **do not fill a value unless the
extraction is defensible.** A wrong number that silently enters a valuation is
worse than a missing one.

---

## 2. Current state

### Main outputs (`02_clean/subsidiary/`)

| file | rows |
|---|---|
| `subsidiary_financial_variables_refined.csv` / `.dta` | 3,742 |
| `subsidiary_financial_variables_refined_summary.csv` | 4 |
| `subsidiary_balance_sheet_panel_all_official.csv` / `.dta` | 3,536 |
| `subsidiary_aoc1_fallback_combined.csv` / `.dta` | 206 |

`.dta` files are Stata-ready: valid variable names, row parity with the CSVs.

### Refined dataset composition

```
source_type                            data_quality_tier   rows  targets
parent_annual_report_aoc1              aoc1_ready            44       44
parent_annual_report_aoc1              aoc1_review          162      162
standalone_or_combined_subsidiary_pdf  full_pdf_ready       516      221
standalone_or_combined_subsidiary_pdf  full_pdf_review     2845     1576
```

### Validation status — all passing

- 1,834 expected targets present, 0 missing, 0 extra
- 0 rows with `attribution_rule == multiple_top30_claimants_review` (correctly excluded)
- 3,567 preferred rows, exactly one per target-year
- 560 ready rows: all have non-missing `total_assets`/`total_liabilities`/`equity`,
  `accounting_identity_ok == 1`, `needs_manual_review == 0`
- 5 year-like values remaining (was 339 before the parser fixes)

### Coverage, counted as **distinct subsidiaries** (of 1,834)

This is the number that matters. Row counts flatter the dataset.

| | PDF downloaded | variables parsed | any financial value | **ready** |
|---|---|---|---|---|
| first pass | 842 | 361 | 435 | 211 |
| before combined-PDF work | 842 | 342 | 491 | 213 |
| **now** | 842 | **395** | **554** | **265** |

**265 of 1,834 subsidiaries (14%) are valuation-ready.** That is the honest headline.

---

## 3. How to run the pipeline

All scripts are in `05_scrape/`. Run from the repo root.

| script | stage |
|---|---|
| `01_build_scrape_targets.py` | build target list from subsidiary mapping |
| `02_discover_balance_sheet_sources.py` | find official/company PDF sources (network) |
| `03_download_balance_sheet_pdfs.py` | download PDFs into `01_raw/subsidiary_bs/` |
| `04_extract_balance_sheet_tables.py` | PDF → text + table CSVs |
| **`04b_ocr_scanned_pdfs.py`** | OCR image-only PDFs, merge into extracted text |
| `05_parse_balance_sheet_variables.py` | parse variables from text/tables |
| `06_build_subsidiary_balance_sheet_panel.py` | per-parent clean panel |
| **`06b_combine_parent_panels.py`** | combine parent panels → `all_official` |
| `07_run_parent_pipeline.py` | orchestrates the above, parent by parent |
| `08_extract_parent_aoc1_fallback.py` | AOC-1 fallback from parent annual reports |
| `09_build_refined_subsidiary_financial_dataset.py` | final refined dataset |
| **`combined_sections.py`** | locate one entity's pages inside a combined PDF (library) |
| **`test_parse_numbers.py`** | 49 parser regression tests |

Bold entries were added during this work.

### Standard local rebuild (no re-downloading)

```bash
python3 05_scrape/test_parse_numbers.py            # always run first: 49 cases
python3 05_scrape/07_run_parent_pipeline.py --stages parse build --workers 4 \
  --summary-output _tmp/intermediate/subsidiary_bs/parent_pipeline_summary.csv
python3 05_scrape/06b_combine_parent_panels.py
python3 05_scrape/08_extract_parent_aoc1_fallback.py
python3 05_scrape/09_build_refined_subsidiary_financial_dataset.py
```

**Budget about an hour for the parse/build step.** It is I/O-bound on Dropbox
(thousands of small table CSVs read through the CloudStorage provider), not
CPU-bound. Processes sitting at 0% CPU are waiting on file reads, not hung.

---

## 4. Where the remaining gaps are

Per-parent, distinct subsidiaries:

| parent | targets | PDF | ready | ready % |
|---|---|---|---|---|
| SAMVARDHANA MOTHERSON INTERNATI | 309 | 128 | 19 | 6 |
| WIPRO LTD | 213 | 96 | 50 | 23 |
| RELIANCE INDUSTRIES LTD | 196 | 30 | 15 | 8 |
| BHARTI AIRTEL LIMITED | 134 | 72 | 26 | 19 |
| JINDAL STEEL AND POWER LTD | 108 | 25 | 16 | 15 |
| UPL LIMITED | 81 | 4 | 1 | 1 |
| HINDALCO INDUSTRIES LIMITED | 81 | 81 | 6 | 7 |
| SUN PHARMACEUTICAL INDUSTRIES L | 75 | 29 | 6 | 8 |
| MAHINDRA & MAHINDRA LTD | 73 | 73 | 9 | 12 |
| INFOSYS LTD | 57 | 13 | 8 | 14 |
| **TATA COMMUNICATIONS LIMITED** | 50 | 50 | **46** | **92** |
| TATA CHEMICALS LIMITED | 44 | 18 | 3 | 7 |
| JSW STEEL LIMITED | 42 | 10 | 0 | 0 |
| ONGC VIDESH LTD. | 41 | 3 | 1 | 2 |
| DR REDDYS LABORATORIES LTD | 41 | 24 | 20 | 49 |
| PIRAMAL ENTERPRISES LTD | 38 | 38 | 1 | 3 |
| GLENMARK PHARMACEUTICALS LTD. | 38 | 22 | 4 | 11 |
| SUZLON ENERGY LTD. | 37 | 20 | 4 | 11 |
| VEDANTA LIMITED | 34 | 26 | 10 | 29 |
| TATA STEEL LTD | 27 | 13 | 7 | 26 |
| BIOCON BIOLOGICS LIMITED | 23 | 23 | 0 | 0 |
| BHARAT PETRORESOURCES LTD | 20 | 6 | 6 | 30 |
| INDIAN OIL CORPORATION LTD. | 15 | 5 | 1 | 7 |
| ADANI PORT AND SPECIAL ECONOMIC | 15 | 11 | 2 | 13 |
| OIL INDIA LIMITED | 12 | 2 | 0 | 0 |
| ICICI BANK LIMITED | 11 | 11 | 0 | 0 |
| RELIANCE ENERGY GENERATION & DI | 10 | 8 | 4 | 40 |
| TATA MOTORS PASSENGER VEHICLES | 9 | 1 | 0 | 0 |

Read this table as two different problems:

- **`PDF` far below `targets`** → a *discovery* problem (UPL 4/81, Reliance 30/196,
  ONGC 3/41, Motherson 128/309).
- **`ready` far below `PDF`** → an *extraction* problem (Hindalco 81 → 6,
  Mahindra 73 → 9, Piramal 38 → 1, Biocon 23 → 0, ICICI 11 → 0).

**842 subsidiaries have a downloaded PDF but only 265 are ready. Those 577 lost in
extraction are the largest remaining opportunity, and the work is entirely local —
no network, no re-downloading.** Start there.

Tata Communications at 92% shows what a correctly handled combined filing looks
like; it was 0% before this round.

---

## 5. Remaining work, in priority order

### 5.1 Tata Steel is now done

Tata Steel has now been rerun under the latest parser. Final Tata Steel status:
70 rows, 27 targets, 56 downloaded-PDF rows, 34 parsed balance sheets, and 23
valuation-ready rows.

```bash
python3 05_scrape/07_run_parent_pipeline.py --stages parse build \
  --parents "TATA STEEL LTD" --workers 1 \
  --summary-output _tmp/intermediate/subsidiary_bs/parent_pipeline_summary_tata_steel_enhanced_final.csv
```

### 5.2 Resume Piramal OCR (~1 h unattended)

38 targets, 38 with PDFs, only 1 ready. Its 3 combined PDFs are sparsely scanned.
The 2021 combined PDF has now been OCR'd and merged; the 2023 and 2024 combined
PDFs were interrupted and still need OCR. The partial 2021 OCR increased Piramal
parsed balance sheets from 7 to 8, but ready rows stayed at 1.

```bash
python3 05_scrape/04b_ocr_scanned_pdfs.py \
  --extractions _tmp/intermediate/subsidiary_bs/extracted_tables_piramal-enterprises-ltd_official.csv \
  --min-chars-per-page 1200 --workers 8
python3 05_scrape/07_run_parent_pipeline.py --stages parse build \
  --parents "PIRAMAL ENTERPRISES LTD" --workers 1
```

Caveat, so you are not surprised: Piramal's combined PDFs produced **no parseable
contents index** before OCR. If OCR does not reveal one, the index-anchored locator
cannot help and you will fall back to header matching. Check
`combined_section_found` in the panel afterwards to see whether it worked.

### 5.3 Investigate the "PDF but not ready" parents (highest value, local only)

The 577 subsidiaries with a downloaded PDF and no usable extraction. Suggested
order by size of gap: Motherson (109), Hindalco (75), Mahindra (64), Wipro (46),
Piramal (37), Biocon (23), Reliance (15), ICICI (11).

Method that worked well and is worth repeating:

```bash
# 1. Is the text layer real, or is the PDF scanned?
python3 - <<'PY'
import pandas as pd, re
from pathlib import Path
PAGE=re.compile(r"\n\n--- (?:page|ocr page) (\d+) ---\n")
e=pd.read_csv('_tmp/intermediate/subsidiary_bs/extracted_tables_<slug>_official.csv', low_memory=False)
for lf,g in e.groupby('local_file'):
    tf=Path(str(g['text_file'].iloc[0]))
    if not tf.exists(): continue
    t=tf.read_text(encoding='utf-8',errors='replace')
    n=(len(PAGE.split(t))-1)//2
    print(f"{Path(lf).name[:50]:50s} pages={n:5d} chars/page={len(t)//max(1,n):6d}")
PY
```

A real statement page is **2,000–4,000 characters**. Anything under ~1,200 is
partially or fully scanned and needs `04b_ocr_scanned_pdfs.py`.

Then check whether the failure is section location or value parsing:

```bash
python3 - <<'PY'
import pandas as pd
p=pd.read_csv('02_clean/subsidiary/subsidiary_balance_sheet_panel_<slug>_official.csv', low_memory=False)
print(p['review_reason'].value_counts().head(10).to_string())
print(p['combined_section_found'].value_counts().to_dict())
PY
```

`review_reason` tells you exactly which gate failed.

### 5.4 Extend discovery with a different source type (needs new code)

**Do not simply re-run `02_discover_balance_sheet_sources.py`.** It has already been
run for all 1,628 targets of the 25 official parents:

```
discovery attempted:           1628   (0 never attempted)
found an ok source:             785
attempted, found nothing:       843
```

Re-running issues identical queries and returns identical results. Additional
coverage requires a genuinely different source: **UK Companies House** (free API),
**Dutch KvK / handelsregister**, **Singapore ACRA**, **OpenCorporates**. Many of the
992 subsidiaries without a PDF are small holding entities that may not publish
standalone accounts at all — establish that before investing heavily.

### 5.5 P&L reporting-scale normalisation

`pl_identity_ok == 0` for 174 rows. Scoping extraction to a single statement page
moved reconciliation only 55.5% → 56.1%, so label selection was not the cause. The
residual problem is **mixed reporting scales within one filing** (one statement in
millions, a note in units). Fixing it means detecting the scale per statement and
normalising. Until then, filter on `pl_identity_ok`.

---

## 6. Traps — please read before changing the parser

These were all found the hard way. Each one silently corrupted data.

### 6.1 Never locate a combined-PDF section by page-offset arithmetic

An earlier version derived a document-wide "printed page → PDF page" offset from
the contents index. It produced Mahindra offset `862`, then `-2332`, and only 3 of
23 located sections actually contained the right company — i.e. it was writing a
**neighbouring subsidiary's balance sheet into the wrong entity's row**, while the
accounting identity still passed because all three figures were shifted together.

`combined_sections.py` now uses the index only for the section **length**. The start
page must be anchored by finding the company's own heading in the document. No
anchor → no section returned. Under this rule every located section is
name-verified (280/280 Tata Communications, 21/21 Hindalco, 3/3 Mahindra).

Related: page-offset calibration must **skip the index pages themselves** — they
name every company in the document and therefore match anything.

Related: one company name is often a prefix of several others in the same group, so
only the single best-matching index entry may be used, **never the union of matches**.

### 6.2 Never overwrite the native text layer with OCR

In scanned filings the contents index is frequently a *real text page*. The 2025
Tata Communications index reads cleanly as `1. NOVAMESH LIMITED 03`; OCR of that
same page yields `Fata Communications (Ameria) Ine SSSd «SO`. Overwriting destroys
the only reliable way to locate each subsidiary.

`04b_ocr_scanned_pdfs.py` merges per page: native text preferred, OCR fills only
genuinely empty pages. Originals are kept as `*.native.bak`.

### 6.3 The scanned-document threshold must be ~1,200 chars/page, not 300

300 chars/page missed 4 of 11 Tata PDFs sitting at 393–998 chars/page. They looked
fine, parsed a contents index, and produced **zero** anchors because their body
pages were images. Use `--min-chars-per-page 1200`.

### 6.4 Number parsing hazards, all covered by the test suite

`test_parse_numbers.py` encodes 49 real evidence strings. **Run it before and after
any parser change.** The classes it protects against:

- European thousands separators — `2.258.699.082` was read as `699.08`
- Space-grouped thousands — `682 045 571 413 987 855` was read as `682`
- OCR-split leading digits — `1 99.435.490` was read as `490`
- Note numbers that look identical to OCR splits — `25 111,395,699` must **not** join
- Scale markers — `Total assets (1000 yen) 47,120,159` was read as `1000`
- Prose — `0.7% of total assets` was read as `0.7`
- UK subtotals — `Total assets less current liabilities` is not total assets
- Bare years in sentences read as values (339 such values dataset-wide, now 5)

All of these were present in the "validated" first-pass dataset. **Evidence columns
are the audit trail — every variable has a `*_evidence` string. Use them.**

### 6.5 Do not trust a passing accounting identity

Consistently mangled figures still balance. `accounting_identity_ok == 1` says the
three numbers are mutually consistent, not that they are correct. Check evidence.

---

## 7. How to validate your work

A ready-to-run validation script is worth recreating; the checks that matter:

```bash
python3 - <<'PY'
import pandas as pd, numpy as np
df=pd.read_csv('02_clean/subsidiary/subsidiary_financial_variables_refined.csv', low_memory=False)

# structure
print('rows', len(df), 'targets', df['target_id'].nunique())
print('shared-UIN rows (must be 0):',
      int(df['attribution_rule'].astype(str).eq('multiple_top30_claimants_review').sum()))
g=df.groupby(['target_id','fiscal_year'],dropna=False)['preferred_for_target_year'].sum()
print('target-years with != 1 preferred (must be 0):', int((g!=1).sum()))

# ready rows
r=df[df['ready_for_valuation'].eq(1)].copy()
for c in ['total_assets','total_liabilities','equity','accounting_identity_ok','needs_manual_review']:
    r[c]=pd.to_numeric(r[c],errors='coerce')
print('ready', len(r),
      'missing_BS', int(r[['total_assets','total_liabilities','equity']].isna().any(axis=1).sum()),
      'identity_bad', int(r['accounting_identity_ok'].ne(1).sum()),
      'needs_review', int(r['needs_manual_review'].fillna(0).ne(0).sum()))

# coverage as distinct subsidiaries, not rows
num=lambda c: pd.to_numeric(df[c],errors='coerce').fillna(0)
for lbl,c in [('pdf','pdf_downloaded'),('parsed','variables_parsed'),('ready','ready_for_valuation')]:
    print(lbl, df.loc[num(c).eq(1),'target_id'].nunique())

# junk sweep
for c in ['equity','total_assets','turnover','profit_after_tax']:
    v=pd.to_numeric(df[c],errors='coerce')
    print(c,'year-like:', int((v.notna()&(v==v.round())&v.between(1990,2035)).sum()))
PY
```

Then spot-check evidence strings for 20+ rows across different parents, especially
where values are very small, very large, or equal to 2024/2025/2026.

---

## 8. Using the data correctly

- **For the OFBV/net-worth valuation, filter `ready_for_valuation == 1`.** Those 560
  rows have complete, identity-consistent balance sheets.
- **Before using any P&L variable, filter `pl_identity_ok`.** `1` = profit before
  tax, tax and profit after tax reconcile (either tax sign convention); `0` = they
  do not; `-1` = not testable because one is missing. Currently 222 / 174 / 3,346.
  Balance-sheet fields are unaffected by this.
- `preferred_for_target_year == 1` gives one row per subsidiary-year.
- Every variable has a `*_evidence` column containing the source line. When a number
  looks wrong, read the evidence before assuming the filing is wrong.
- Rows with `attribution_rule == multiple_top30_claimants_review` are excluded by
  design (UINs shared by multiple top-30 parents) and must not be added back
  without deciding attribution.

### AOC-1 fallback

Three parents have no usable standalone subsidiary PDFs and use AOC-1 tables from
the parent annual report instead: **Jindal Steel and Power, Dr Reddy's, Infosys**
(206 rows: 44 ready, 162 review). Downloaded reports are in
`_tmp/intermediate/subsidiary_bs/fallback_parent_reports/`.

Sources in use:
- Jindal — `https://www.bseindia.com/xml-data/corpfiling/AttachHis/b945c787-ab25-48e3-b56f-28d4a39a2927.pdf`
- Dr Reddy's — `https://www.drreddys.com/cms/cms/sites/default/files/2025-06/Integrated%20Annual%20Report%202024-25.pdf`
- Infosys — `https://www.bseindia.com/xml-data/corpfiling/AttachHis/4527f4d2-dac4-4528-a1dc-5070fd9e140d.pdf`

⚠️ **`468b09a3-a212-4066-bbaa-4b0ba524d2ce.pdf` is not Infosys — it is Reliance.**
An earlier session matched it by mistake. It is not referenced in any script and is
not on disk. Do not reintroduce it.

---

## 9. Useful paths

```
01_raw/subsidiary_bs/<parent>/<target_id>/filings/   downloaded PDFs
_tmp/intermediate/subsidiary_bs/                     per-parent intermediates
_tmp/intermediate/subsidiary_bs/ocr_cache/           OCR text, keyed by file digest (11 MB)
_tmp/intermediate/subsidiary_bs/logs/                per-parent run logs
02_clean/subsidiary/                                 final CSV + DTA outputs
```

The OCR cache is keyed by PDF digest and is **reused automatically** — re-running
`04b_ocr_scanned_pdfs.py` will not redo completed documents. Keep it.
