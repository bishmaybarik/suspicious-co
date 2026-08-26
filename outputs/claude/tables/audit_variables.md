| variable                      | dtype   |   n_unique |   n_missing |   pct_missing | example                                                      |
|:------------------------------|:--------|-----------:|------------:|--------------:|:-------------------------------------------------------------|
| target_id                     | object  |       1834 |           0 |           0   | 000-stimul-t__NDWAZ20140643__l2__534b1a97ac                  |
| parent                        | object  |         28 |           0 |           0   | OIL INDIA LIMITED                                            |
| level                         | int32   |         13 |           0 |           0   | 2                                                            |
| entity_name                   | object  |       1828 |           0 |           0   | 000 STIMUL T,                                                |
| entity_country                | object  |        122 |           0 |           0   | RUSSIA                                                       |
| immediate_parent              | object  |        457 |           0 |           0   | WORLACE INVESTMENTS LTD                                      |
| immediate_parent_country      | object  |         63 |           0 |           0   | CYPRUS                                                       |
| stake                         | float64 |        212 |         508 |          13.6 | 100.0                                                        |
| sector_code                   | object  |         17 |           0 |           0   | MIN                                                          |
| sector_label                  | object  |         17 |           0 |           0   | Mining & Extraction                                          |
| uin                           | object  |        186 |           0 |           0   | NDWAZ20140643                                                |
| shared_uin                    | int32   |          2 |           0 |           0   | 0                                                            |
| n_top30_claimants             | int32   |          1 |           0 |           0   | 1                                                            |
| top30_claimants               | object  |         28 |           0 |           0   | OIL INDIA LIMITED                                            |
| attribution_rule              | object  |          2 |           0 |           0   | not_shared_uin                                               |
| fiscal_year                   | object  |         16 |         993 |          26.5 | 2025-26                                                      |
| period_end_date               | object  |         72 |        2408 |          64.4 | 2022-03-31                                                   |
| source_type                   | object  |          2 |           0 |           0   | standalone_or_combined_subsidiary_pdf                        |
| source_url                    | object  |       1595 |         992 |          26.5 | https://www.hindalco.com/upload/pdf/subsidiary-financial-sta |
| source_domain                 | object  |         26 |         992 |          26.5 | www.hindalco.com                                             |
| source_title                  | object  |        738 |         848 |          22.7 | Hindalco subsidiary financial statements 2025-26 foreign sub |
| local_file                    | object  |       1635 |        1054 |          28.2 | /Users/bishmaybarik/Library/CloudStorage/Dropbox/rbi_odi/01_ |
| currency                      | object  |          9 |        2350 |          62.8 | USD                                                          |
| units                         | object  |          2 |        3680 |          98.3 | INR millions                                                 |
| total_assets                  | float64 |        930 |        2733 |          73   | 40244.0                                                      |
| total_liabilities             | float64 |        789 |        2853 |          76.2 | 819409.0                                                     |
| equity                        | float64 |        912 |        2719 |          72.7 | 39425.0                                                      |
| share_capital                 | float64 |        529 |        2563 |          68.5 | 200.0                                                        |
| reserves_surplus              | float64 |        463 |        3231 |          86.3 | -83218.0                                                     |
| turnover                      | float64 |        834 |        2733 |          73   | 2372.0                                                       |
| profit_before_tax             | float64 |        782 |        2874 |          76.8 | 7870.0                                                       |
| provision_tax                 | float64 |        690 |        2773 |          74.1 | 578.0                                                        |
| profit_after_tax              | float64 |        634 |        2976 |          79.5 | 6178.0                                                       |
| cash_flow_operating           | float64 |        295 |        3410 |          91.1 | -3108.0                                                      |
| cash_flow_investing           | float64 |        227 |        3433 |          91.7 | -2276.0                                                      |
| cash_flow_financing           | float64 |        210 |        3446 |          92.1 | -38595.0                                                     |
| cash_end                      | float64 |        256 |        3441 |          92   | 72662.0                                                      |
| dividends_paid                | float64 |         90 |        3546 |          94.8 | -38595.0                                                     |
| interest_paid                 | float64 |        228 |        3450 |          92.2 | -138330.0                                                    |
| issue_share_capital           | float64 |         13 |        3698 |          98.8 | 0.0                                                          |
| proceeds_borrowings           | float64 |         66 |        3656 |          97.7 | 713906.0                                                     |
| repayment_borrowings          | float64 |         75 |        3636 |          97.2 | 1092465.0                                                    |
| shareholding_percent          | float64 |          5 |        3685 |          98.5 | 100.0                                                        |
| total_assets_evidence         | object  |        892 |        2775 |          74.2 | Total assets $ 40,244 $ 40,244                               |
| total_liabilities_evidence    | object  |        464 |        2903 |          77.6 | Total liabilities 819409                                     |
| equity_evidence               | object  |        767 |        2708 |          72.4 | Total equity 39,425 39,835                                   |
| share_capital_evidence        | object  |        917 |        2614 |          69.9 | Share capital 16 2 00200                                     |
| reserves_surplus_evidence     | object  |        428 |        3283 |          87.7 | Accumulated deficit (83,218) (82,808)                        |
| turnover_evidence             | object  |        887 |        2776 |          74.2 | Net Sales and Operating Revenue $ 2,372 $ 2,722 $ 8,383 $ 11 |
| profit_before_tax_evidence    | object  |        768 |        2927 |          78.2 | (Loss)/Profit before tax 7,870 (12,885)                      |
| provision_tax_evidence        | object  |        819 |        2804 |          74.9 | Tax expense 578 1,505                                        |
| profit_after_tax_evidence     | object  |        672 |        3029 |          80.9 | (loss)/profit for the year 6,178 (10,826)                    |
| cash_flow_operating_evidence  | object  |        314 |        3410 |          91.1 | Net cash used in operating activities (3,108) (2,096)        |
| cash_flow_investing_evidence  | object  |        273 |        3433 |          91.7 | Net cash used in investing activities $ (2,276)              |
| cash_flow_financing_evidence  | object  |        257 |        3446 |          92.1 | Net cash used in financing activities $ (38,595) $ (17,465)  |
| cash_end_evidence             | object  |        266 |        3441 |          92   | Cash and cash equivalents at end of year 72,662 51,075       |
| dividends_paid_evidence       | object  |        166 |        3546 |          94.8 | Dividends paid $ (38,595) $ (17,465)                         |
| interest_paid_evidence        | object  |        267 |        3450 |          92.2 | Interest paid (138,330) (142,697)                            |
| issue_share_capital_evidence  | object  |         26 |        3698 |          98.8 | Issue of share capital (by offsetting liabilities) - - - - - |
| proceeds_borrowings_evidence  | object  |         83 |        3656 |          97.7 | Proceeds from borrowings 713906                              |
| repayment_borrowings_evidence | object  |         98 |        3636 |          97.2 | Repayment of loans by subsidiaries and others 10,92,465 1,49 |
| extraction_method             | object  |          2 |         848 |          22.7 | regex_text_v1                                                |
| match_score                   | float64 |        124 |         848 |          22.7 | 8.0                                                          |
| source_found                  | int32   |          2 |           0 |           0   | 0                                                            |
| pdf_downloaded                | int32   |          2 |           0 |           0   | 0                                                            |
| variables_parsed              | int32   |          2 |           0 |           0   | 0                                                            |
| accounting_identity_gap       | float64 |        102 |        2873 |          76.8 | -818590.0                                                    |
| accounting_identity_ok        | int32   |          2 |           0 |           0   | 0                                                            |
| needs_manual_review           | int32   |          2 |           0 |           0   | 1                                                            |
| ready_for_valuation           | int32   |          2 |           0 |           0   | 0                                                            |
| review_reason                 | object  |         23 |         560 |          15   | no_official_pdf_found;balance_sheet_variables_missing;curren |
| aoc_match_status              | object  |          2 |        3536 |          94.5 | not_matched                                                  |
| aoc_company_name              | object  |         61 |        3680 |          98.3 | betapharm Arzneimittel GmbH(3)                               |
| data_quality_tier             | object  |          4 |           0 |           0   | full_pdf_review                                              |
| pl_identity_ok                | int32   |          3 |           0 |           0   | -1                                                           |
| source_priority               | int32   |          4 |           0 |           0   | 3                                                            |
| preferred_for_target_year     | int32   |          2 |           0 |           0   | 1                                                            |