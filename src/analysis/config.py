"""Paths and transparent normalization rules for the canonical pipeline."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    Path.home()
    / ".agent-inputs/suspicious-co/subsidiary_financial_variables_refined.dta"
)
DEFAULT_DICTIONARY = (
    Path.home()
    / ".agent-inputs/suspicious-co/"
    "subsidiary_financial_variables_refined_data_dictionary.txt"
)
INPUT_PATH = Path(os.environ.get("SUSPICIOUS_CO_INPUT", DEFAULT_INPUT))
DICTIONARY_PATH = Path(
    os.environ.get("SUSPICIOUS_CO_DICTIONARY", DEFAULT_DICTIONARY)
)
OUTPUT_ROOT = ROOT / "outputs/final"
TABLE_DIR = OUTPUT_ROOT / "tables"
FIGURE_DIR = OUTPUT_ROOT / "figures"
PAPER_DIR = ROOT / "paper"

INPUT_SHA256 = "65251cd99ff1cd1b5f3b44cab12ba68eed3935787cbc35b5541eb07e9dd30cea"
DICTIONARY_SHA256 = "4f3285c0bb55e3578a73686d0fb27f9110b0d1c6e0a4000b2ff357aa8e35ac05"

# Spelling and formatting harmonization only. Conceptually ambiguous labels
# remain separate and are flagged in the output tables.
COUNTRY_FIXES = {
    "CAYMAN ISLAND": "CAYMAN ISLANDS",
    "EUROPIAN UNION": "EUROPEAN UNION",
    "GIBRALTER": "GIBRALTAR",
    "HONGKONG": "HONG KONG",
    "MARSHALL ISLAND": "MARSHALL ISLANDS",
    "NICARAQUA": "NICARAGUA",
    "VENEZULA": "VENEZUELA",
}

# This maintained list is used only in a labeled sensitivity analysis. It is
# not treated as an observed legal or tax classification.
DECLARED_CENTRES = {
    "BARBADOS",
    "BERMUDA",
    "BRITISH VIRGIN ISLANDS",
    "CAYMAN ISLANDS",
    "CYPRUS",
    "GUERNSEY",
    "HONG KONG",
    "IFSC GIFT CITY",
    "IRELAND",
    "ISLE OF MAN",
    "JERSEY",
    "LUXEMBOURG",
    "MARSHALL ISLANDS",
    "MAURITIUS",
    "NETHERLANDS",
    "PANAMA",
    "SINGAPORE",
    "SWITZERLAND",
    "UNITED ARAB EMIRATES",
}

PARENT_SHORT = {
    "ADANI PORT AND SPECIAL ECONOMIC": "Adani Ports",
    "BHARAT PETRORESOURCES LTD": "Bharat Petroresources",
    "BHARTI AIRTEL LIMITED": "Bharti Airtel",
    "BIOCON BIOLOGICS LIMITED": "Biocon Biologics",
    "DR REDDYS LABORATORIES LTD": "Dr Reddy's",
    "GLENMARK PHARMACEUTICALS LTD.": "Glenmark",
    "HINDALCO INDUSTRIES LIMITED": "Hindalco",
    "ICICI BANK LIMITED": "ICICI Bank",
    "INDIAN OIL CORPORATION LTD.": "Indian Oil",
    "INFOSYS LTD": "Infosys",
    "JINDAL STEEL AND POWER LTD": "Jindal Steel & Power",
    "JSW STEEL LIMITED": "JSW Steel",
    "MAHINDRA & MAHINDRA LTD": "Mahindra & Mahindra",
    "OIL INDIA LIMITED": "Oil India",
    "ONGC VIDESH LTD.": "ONGC Videsh",
    "PIRAMAL ENTERPRISES LTD": "Piramal",
    "RELIANCE ENERGY GENERATION & DI": "Reliance Energy",
    "RELIANCE INDUSTRIES LTD": "Reliance Industries",
    "SAMVARDHANA MOTHERSON INTERNATI": "Motherson",
    "SUN PHARMACEUTICAL INDUSTRIES L": "Sun Pharma",
    "SUZLON ENERGY LTD.": "Suzlon",
    "TATA CHEMICALS LIMITED": "Tata Chemicals",
    "TATA COMMUNICATIONS LIMITED": "Tata Communications",
    "TATA MOTORS PASSENGER VEHICLES": "Tata Motors PV",
    "TATA STEEL LTD": "Tata Steel",
    "UPL LIMITED": "UPL",
    "VEDANTA LIMITED": "Vedanta",
    "WIPRO LTD": "Wipro",
}

COUNTRY_SHORT = {
    "UNITED STATES OF AMERICA": "United States",
    "UNITED ARAB EMIRATES": "UAE",
    "UNITED KINGDOM": "United Kingdom",
    "NETHERLANDS": "Netherlands",
    "MAURITIUS": "Mauritius",
    "SINGAPORE": "Singapore",
    "SWITZERLAND": "Switzerland",
    "CYPRUS": "Cyprus",
}
