"""Test whether the RBI ODI UIN string is systematically structured.

The data dictionary describes uin only as an identifier. This script checks a
specific reading of the 13-character string and reports the evidence for and
against it, so downstream use of the decoded fields is auditable.

Proposed reading: [2-char RBI regional office][1-char investment type]
[2-char series][4-digit registration year][4-digit serial].
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from config import derived_path, load_rows, write_table

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")
df_row = load_rows()


# GOAL: CHECK THE STRING IS FIXED-FORMAT BEFORE READING ANY FIELD FROM IT

df_uin = df_entity.drop_duplicates("uin")[["uin", "parent"]].copy()
df_uin["office"] = df_uin.uin.str.slice(0, 2)
df_uin["invest_type"] = df_uin.uin.str.slice(2, 3)
df_uin["series"] = df_uin.uin.str.slice(3, 5)
df_uin["year"] = pd.to_numeric(df_uin.uin.str.slice(5, 9), errors="coerce")
df_uin["serial"] = df_uin.uin.str.slice(9)

format_row_list = [
    {"check": "all uin are 13 characters",
     "result": bool((df_uin.uin.str.len() == 13).all())},
    {"check": "characters 6-9 parse as a year between 1980 and 2026",
     "result": bool(df_uin.year.between(1980, 2026).all())},
    {"check": "characters 10-13 are always four digits",
     "result": bool(df_uin.serial.str.fullmatch(r"\d{4}").all())},
    {"check": "distinct investment-type characters",
     "result": ", ".join(sorted(df_uin.invest_type.unique()))},
    {"check": "distinct office codes",
     "result": ", ".join(sorted(df_uin.office.unique()))},
]
write_table(pd.DataFrame(format_row_list), "uin_format_checks")


# GOAL: TEST THE INVESTMENT-TYPE CHARACTER AGAINST OBSERVED OWNERSHIP STAKES

# if the character separates wholly owned, joint-venture and participating
# interests, recorded stakes should fall in that order
df_stake = df_entity[(df_entity.level == 1) & df_entity.stake.notna() & (df_entity.stake > 0)].copy()
df_stake["invest_type"] = df_stake.uin.str.slice(2, 3)

df_type = df_stake.groupby("invest_type").agg(
    n_entities=("stake", "size"),
    mean_stake=("stake", "mean"),
    median_stake=("stake", "median"),
    pct_stake_100=("stake", lambda s: 100 * (s == 100).mean()),
).round(1).reset_index()

# structure size by type is a second, independent signal
df_type["n_uins"] = df_type.invest_type.map(df_uin.invest_type.value_counts())
df_type["mean_entities_per_uin"] = df_type.invest_type.map(
    df_entity.assign(t=df_entity.uin.str.slice(2, 3)).groupby(["t", "uin"]).size().groupby(level=0).mean()
).round(2)
write_table(df_type, "uin_investment_type_evidence")

# the level-0 names under the P character are the clearest qualitative evidence
df_p_names = df_entity[(df_entity.uin.str.slice(2, 3) == "P") & (df_entity.level == 0)][
    ["parent", "entity_name", "entity_country", "uin"]
].sort_values("entity_name")
write_table(df_p_names, "uin_participation_type_level0_names")


# GOAL: TEST THE OFFICE CHARACTERS AGAINST THE PARENT COMPANY'S HOME REGION

df_office = pd.crosstab(df_uin.parent, df_uin.office)
write_table(df_office.reset_index(), "uin_office_by_parent")


# GOAL: TEST THE YEAR FIELD AGAINST OBSERVED FINANCIAL-STATEMENT YEARS

df_row = df_row.assign(
    fiscal_year_start=pd.to_numeric(df_row.fiscal_year.str.slice(0, 4), errors="coerce"),
    uin_year=pd.to_numeric(df_row.uin.str.slice(5, 9), errors="coerce"),
).dropna(subset=["fiscal_year_start"])

# a registration year should not post-date the earliest statement it explains
df_first = df_row.groupby("uin").agg(
    uin_year=("uin_year", "first"), first_statement_year=("fiscal_year_start", "min")
)
year_row_list = [
    {"check": "uins with an observed statement year", "value": len(df_first)},
    {"check": "uins where the first statement precedes the decoded year",
     "value": int((df_first.first_statement_year < df_first.uin_year).sum())},
    {"check": "pct of those uins",
     "value": round(100 * (df_first.first_statement_year < df_first.uin_year).mean(), 1)},
    {"check": "median years between decoded year and first statement",
     "value": float((df_first.first_statement_year - df_first.uin_year).median())},
]
write_table(pd.DataFrame(year_row_list), "uin_year_checks")

print("uin structure audit written")
print(df_type.to_string(index=False))
