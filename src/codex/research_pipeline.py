#!/usr/bin/env python3
"""Blind-discovery data engineering and empirical audit pipeline.

The input Stata file is treated as immutable.  This script constructs explicit
row/target/entity/edge/path denominators, audits the hierarchy, and writes all
Codex-only analytical outputs used in the research notes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from rapidfuzz.fuzz import ratio as fuzzy_ratio
from rapidfuzz.fuzz import token_sort_ratio


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
DEFAULT_OUTPUT = ROOT / "outputs/codex"

STRUCTURAL_COLUMNS = [
    "parent",
    "level",
    "entity_name",
    "entity_country",
    "immediate_parent",
    "immediate_parent_country",
    "stake",
    "sector_code",
    "sector_label",
    "uin",
    "shared_uin",
    "n_top30_claimants",
    "top30_claimants",
    "attribution_rule",
]

FINANCIAL_COLUMNS = [
    "total_assets",
    "total_liabilities",
    "equity",
    "share_capital",
    "reserves_surplus",
    "turnover",
    "profit_before_tax",
    "provision_tax",
    "profit_after_tax",
    "cash_flow_operating",
    "cash_flow_investing",
    "cash_flow_financing",
    "cash_end",
    "dividends_paid",
    "interest_paid",
    "issue_share_capital",
    "proceeds_borrowings",
    "repayment_borrowings",
]

EVIDENCE_COLUMNS = [f"{c}_evidence" for c in FINANCIAL_COLUMNS]

# Only transparent spelling/format harmonization is performed.  Raw labels are
# always retained, and conceptually ambiguous labels remain distinct.
COUNTRY_FIXES = {
    "CAYMAN ISLAND": "CAYMAN ISLANDS",
    "EUROPIAN UNION": "EUROPEAN UNION",
    "GIBRALTER": "GIBRALTAR",
    "HONGKONG": "HONG KONG",
    "MARSHALL ISLAND": "MARSHALL ISLANDS",
    "NICARAQUA": "NICARAGUA",
    "VENEZULA": "VENEZUELA",
}

COUNTRY_LABEL_NOTES = {
    "CHANNEL ISLAND": "broad region rather than a specific jurisdiction",
    "CONGO": "ambiguous between two sovereign jurisdictions",
    "EUROPIAN UNION": "misspelled supranational region, not a country",
    "IFSC GIFT CITY": "special financial zone label, not a sovereign country",
    "VENEZULA": "obvious spelling variant standardized to VENEZUELA",
    "GIBRALTER": "obvious spelling variant standardized to GIBRALTAR",
    "NICARAQUA": "obvious spelling variant standardized to NICARAGUA",
    "HONGKONG": "format variant standardized to HONG KONG",
    "CAYMAN ISLAND": "singular variant standardized to CAYMAN ISLANDS",
    "MARSHALL ISLAND": "singular variant standardized to MARSHALL ISLANDS",
}

DEPTH_BINS = [-1, 0, 1, 2, 4, np.inf]
DEPTH_LABELS = ["0", "1", "2", "3-4", "5+"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *values: Any) -> str:
    text = "\x1f".join("<NA>" if pd.isna(v) else str(v) for v in values)
    return f"{prefix}_{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


def ascii_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def light_name_key(value: Any) -> str:
    """Punctuation/spacing-insensitive key; legal suffixes are retained."""
    text = ascii_text(value).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", text)


def strip_country_suffix_key(name: Any, country: Any) -> str:
    """Linkage-only alias that removes a trailing country phrase."""
    name_text = ascii_text(name).replace("&", " and ")
    country_text = ascii_text(country).replace("&", " and ")
    name_tokens = re.findall(r"[a-z0-9]+", name_text)
    country_tokens = re.findall(r"[a-z0-9]+", country_text)
    if country_tokens and name_tokens[-len(country_tokens) :] == country_tokens:
        name_tokens = name_tokens[: -len(country_tokens)]
    return "".join(name_tokens)


def normalize_country(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    text = re.sub(r"\s+", " ", str(value).strip().upper())
    return COUNTRY_FIXES.get(text, text)


def join_unique(values: Iterable[Any], limit: int | None = None) -> str:
    result = sorted({str(v) for v in values if not pd.isna(v) and str(v) != ""})
    if limit is not None and len(result) > limit:
        return " | ".join(result[:limit]) + f" | ... (+{len(result) - limit})"
    return " | ".join(result)


def list_unique_int(values: Iterable[Any]) -> str:
    vals = sorted({int(v) for v in values if not pd.isna(v)})
    return " | ".join(map(str, vals))


def entropy_and_hhi(counts: pd.Series) -> tuple[float, float, float]:
    if counts.sum() <= 0:
        return np.nan, np.nan, np.nan
    shares = counts / counts.sum()
    hhi = float(np.square(shares).sum())
    entropy = float(-(shares * np.log(shares)).sum())
    effective = float(np.exp(entropy))
    return entropy, hhi, effective


def pct(numerator: float, denominator: float) -> float:
    return float(100 * numerator / denominator) if denominator else np.nan


def parse_period_date(value: Any) -> pd.Timestamp | pd.NaT:
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip()
    # Do not let parsers silently impute a year for strings such as "Dec 31,".
    if not re.search(r"\b(?:19|20)\d{2}\b", text):
        return pd.NaT
    text = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", text, flags=re.I)
    dayfirst_options = (True,) if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", text) else (False, True)
    for dayfirst in dayfirst_options:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                parsed = pd.to_datetime(text, errors="raise", dayfirst=dayfirst)
            return pd.Timestamp(parsed)
        except (ValueError, TypeError):
            continue
    return pd.NaT


def fiscal_window(fiscal_year: Any) -> tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]:
    if pd.isna(fiscal_year):
        return pd.NaT, pd.NaT
    match = re.fullmatch(r"(\d{4})-(\d{2})", str(fiscal_year).strip())
    if not match:
        return pd.NaT, pd.NaT
    start_year = int(match.group(1))
    end_year = (start_year // 100) * 100 + int(match.group(2))
    if end_year < start_year:
        end_year += 100
    return pd.Timestamp(start_year, 4, 1), pd.Timestamp(end_year, 3, 31)


def read_input(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    reader = pd.io.stata.StataReader(path)
    labels = reader.variable_labels()
    df = reader.read(convert_categoricals=False)
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].replace(r"^\s*$", pd.NA, regex=True)
    return df, labels


def prepare_occurrences(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    invariance_rows: list[dict[str, Any]] = []
    for column in STRUCTURAL_COLUMNS:
        counts = df.groupby("target_id", dropna=False)[column].nunique(dropna=False)
        invariance_rows.append(
            {
                "variable": column,
                "targets_with_conflict": int((counts > 1).sum()),
                "maximum_distinct_values_within_target": int(counts.max()),
            }
        )
    invariance = pd.DataFrame(invariance_rows)
    if invariance["targets_with_conflict"].sum() != 0:
        raise ValueError("Structural fields are not invariant within target_id")

    occurrences = df.drop_duplicates("target_id", keep="first").copy()
    occurrences["entity_country_std"] = occurrences["entity_country"].map(
        normalize_country
    )
    occurrences["immediate_parent_country_std"] = occurrences[
        "immediate_parent_country"
    ].map(normalize_country)
    occurrences["entity_name_key"] = occurrences["entity_name"].map(light_name_key)
    occurrences["entity_link_alias"] = occurrences.apply(
        lambda row: strip_country_suffix_key(
            row["entity_name"], row["entity_country"]
        ),
        axis=1,
    )
    occurrences["immediate_parent_name_key"] = occurrences["immediate_parent"].map(
        light_name_key
    )
    occurrences["immediate_parent_link_alias"] = occurrences.apply(
        lambda row: strip_country_suffix_key(
            row["immediate_parent"], row["immediate_parent_country"]
        ),
        axis=1,
    )
    occurrences["parent_name_key"] = occurrences["parent"].map(light_name_key)
    occurrences["global_entity_id"] = occurrences.apply(
        lambda row: stable_id(
            "ge", row["entity_country_std"], row["entity_name_key"]
        ),
        axis=1,
    )
    occurrences["group_entity_id"] = occurrences.apply(
        lambda row: stable_id(
            "pe",
            row["parent"],
            row["entity_country_std"],
            row["entity_name_key"],
        ),
        axis=1,
    )
    occurrences["depth_bin"] = pd.cut(
        occurrences["level"], DEPTH_BINS, labels=DEPTH_LABELS
    ).astype("string")
    return occurrences, invariance


def aggregate_entities(
    occurrences: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    group_entities = (
        occurrences.groupby("group_entity_id", dropna=False)
        .agg(
            parent=("parent", "first"),
            canonical_entity_name=("entity_name", "first"),
            entity_name_aliases=("entity_name", join_unique),
            entity_country=("entity_country_std", "first"),
            target_occurrences=("target_id", "size"),
            target_ids=("target_id", join_unique),
            reported_levels=("level", list_unique_int),
            minimum_reported_level=("level", "min"),
            maximum_reported_level=("level", "max"),
            immediate_parents=("immediate_parent", join_unique),
            immediate_parent_countries=("immediate_parent_country_std", join_unique),
            uins=("uin", join_unique),
            n_uins=("uin", "nunique"),
            sector_codes=("sector_code", join_unique),
            n_immediate_parents=("immediate_parent_name_key", "nunique"),
            n_reported_levels=("level", "nunique"),
            global_entity_id=("global_entity_id", "first"),
        )
        .reset_index()
    )
    group_entities["repeated_within_parent"] = (
        group_entities["target_occurrences"] > 1
    )
    group_entities["multiple_paths_or_versions"] = (
        (group_entities["n_immediate_parents"] > 1)
        | (group_entities["n_reported_levels"] > 1)
    )

    global_entities = (
        occurrences.groupby("global_entity_id", dropna=False)
        .agg(
            canonical_entity_name=("entity_name", "first"),
            entity_name_aliases=("entity_name", join_unique),
            entity_country=("entity_country_std", "first"),
            target_occurrences=("target_id", "size"),
            group_entity_count=("group_entity_id", "nunique"),
            parent_count=("parent", "nunique"),
            parents=("parent", join_unique),
            target_ids=("target_id", join_unique),
            uins=("uin", join_unique),
            n_uins=("uin", "nunique"),
            reported_levels=("level", list_unique_int),
            immediate_parents=("immediate_parent", join_unique),
        )
        .reset_index()
    )
    global_entities["repeated_across_parent_groups"] = (
        global_entities["parent_count"] > 1
    )
    global_entities["repeated_target_or_path"] = (
        global_entities["target_occurrences"] > 1
    )

    duplicate_clusters = global_entities[
        global_entities["target_occurrences"] > 1
    ].copy()
    return group_entities, global_entities, duplicate_clusters


def fuzzy_duplicate_candidates(occurrences: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (parent, country), group in occurrences.groupby(
        ["parent", "entity_country_std"], dropna=False
    ):
        values = group[
            ["target_id", "entity_name", "entity_name_key", "level", "uin"]
        ].to_dict("records")
        for left_index in range(len(values)):
            for right_index in range(left_index + 1, len(values)):
                left = values[left_index]
                right = values[right_index]
                if left["entity_name_key"] == right["entity_name_key"]:
                    continue
                char_score = fuzzy_ratio(
                    left["entity_name_key"], right["entity_name_key"]
                )
                token_score = token_sort_ratio(
                    str(left["entity_name"]), str(right["entity_name"])
                )
                score = max(char_score, token_score)
                if score < 94:
                    continue
                rows.append(
                    {
                        "parent": parent,
                        "entity_country": country,
                        "left_target_id": left["target_id"],
                        "right_target_id": right["target_id"],
                        "left_name": left["entity_name"],
                        "right_name": right["entity_name"],
                        "left_level": left["level"],
                        "right_level": right["level"],
                        "left_uin": left["uin"],
                        "right_uin": right["uin"],
                        "character_similarity": char_score,
                        "token_sort_similarity": token_score,
                        "maximum_similarity": score,
                        "manual_review_required": 1,
                    }
                )
    if not rows:
        return pd.DataFrame(
            columns=[
                "parent",
                "entity_country",
                "left_target_id",
                "right_target_id",
            ]
        )
    return pd.DataFrame(rows).sort_values(
        ["maximum_similarity", "parent"], ascending=[False, True]
    )


def build_edges(occurrences: pd.DataFrame) -> pd.DataFrame:
    records = occurrences.set_index("target_id", drop=False).to_dict("index")
    alias_index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for target_id, record in records.items():
        for alias in {record["entity_name_key"], record["entity_link_alias"]}:
            if alias:
                alias_index[(record["parent"], alias)].add(target_id)

    rows: list[dict[str, Any]] = []
    for child_id, child in records.items():
        parent_key = child["immediate_parent_name_key"]
        parent_alias = child["immediate_parent_link_alias"]
        root_match = child["parent_name_key"] in {parent_key, parent_alias}
        chosen_id: str | None = None
        status = ""
        ambiguity_count = 0
        fuzzy_score = np.nan

        if root_match:
            status = "ultimate_parent_root" if child["level"] == 0 else "root_level_mismatch"
            parent_node_id = stable_id("root", child["parent"])
            parent_node_type = "ultimate_parent"
            matched_parent_level = -1
            matched_parent_name = child["parent"]
            matched_parent_country = "INDIA"
        else:
            candidate_ids: set[str] = set()
            for alias in {parent_key, parent_alias}:
                candidate_ids.update(alias_index.get((child["parent"], alias), set()))
            candidate_ids.discard(child_id)

            def candidate_score(candidate_id: str) -> tuple[int, int, int, int]:
                candidate = records[candidate_id]
                expected = int(candidate["level"] == child["level"] - 1)
                country = int(
                    candidate["entity_country_std"]
                    == child["immediate_parent_country_std"]
                )
                exact = int(candidate["entity_name"] == child["immediate_parent"])
                same_uin = int(candidate["uin"] == child["uin"])
                return expected, country, exact, same_uin

            if not candidate_ids:
                # Conservative fuzzy rescue: same group, expected level, same
                # country, a very high score, and a unique best match.
                pool = occurrences[
                    (occurrences["parent"] == child["parent"])
                    & (occurrences["level"] == child["level"] - 1)
                    & (
                        occurrences["entity_country_std"]
                        == child["immediate_parent_country_std"]
                    )
                    & (occurrences["target_id"] != child_id)
                ]
                fuzzy_candidates: list[tuple[float, str]] = []
                for candidate in pool.itertuples():
                    score = fuzzy_ratio(
                        parent_alias or parent_key,
                        candidate.entity_link_alias or candidate.entity_name_key,
                    )
                    fuzzy_candidates.append((score, candidate.target_id))
                fuzzy_candidates.sort(reverse=True)
                if fuzzy_candidates and fuzzy_candidates[0][0] >= 96:
                    if len(fuzzy_candidates) == 1 or (
                        fuzzy_candidates[0][0] - fuzzy_candidates[1][0] >= 2
                    ):
                        chosen_id = fuzzy_candidates[0][1]
                        fuzzy_score = fuzzy_candidates[0][0]
                        status = "fuzzy_expected_level"

            if candidate_ids:
                scored = [(candidate_score(cid), cid) for cid in candidate_ids]
                best_score = max(score for score, _ in scored)
                best_ids = sorted(cid for score, cid in scored if score == best_score)
                ambiguity_count = len(best_ids)
                if len(best_ids) == 1:
                    chosen_id = best_ids[0]
                    candidate = records[chosen_id]
                    expected, country, exact, _ = best_score
                    if expected and exact:
                        status = "exact_expected_level"
                    elif expected:
                        status = "normalized_expected_level"
                    elif exact:
                        status = "exact_other_level"
                    else:
                        status = "normalized_other_level"
                else:
                    status = "ambiguous_observed_parent"

            if chosen_id is not None:
                parent_record = records[chosen_id]
                parent_node_id = parent_record["group_entity_id"]
                parent_node_type = "observed_entity"
                matched_parent_level = parent_record["level"]
                matched_parent_name = parent_record["entity_name"]
                matched_parent_country = parent_record["entity_country_std"]
            elif status == "ambiguous_observed_parent":
                parent_node_id = stable_id(
                    "amb",
                    child["parent"],
                    child["immediate_parent_country_std"],
                    parent_alias or parent_key,
                )
                parent_node_type = "ambiguous_entity"
                matched_parent_level = np.nan
                matched_parent_name = child["immediate_parent"]
                matched_parent_country = child["immediate_parent_country_std"]
            else:
                status = "unobserved_parent"
                parent_node_id = stable_id(
                    "unobs",
                    child["parent"],
                    child["immediate_parent_country_std"],
                    parent_alias or parent_key,
                )
                parent_node_type = "unobserved_entity"
                matched_parent_level = np.nan
                matched_parent_name = child["immediate_parent"]
                matched_parent_country = child["immediate_parent_country_std"]

        rows.append(
            {
                "edge_occurrence_id": stable_id("edge", child_id),
                "parent": child["parent"],
                "child_target_id": child_id,
                "child_group_entity_id": child["group_entity_id"],
                "child_global_entity_id": child["global_entity_id"],
                "child_entity_name": child["entity_name"],
                "child_country": child["entity_country_std"],
                "reported_level": child["level"],
                "reported_immediate_parent": child["immediate_parent"],
                "reported_immediate_parent_country": child[
                    "immediate_parent_country_std"
                ],
                "parent_node_id": parent_node_id,
                "parent_node_type": parent_node_type,
                "matched_parent_target_id": chosen_id,
                "matched_parent_name": matched_parent_name,
                "matched_parent_country": matched_parent_country,
                "matched_parent_level": matched_parent_level,
                "link_status": status,
                "candidate_tie_count": ambiguity_count,
                "fuzzy_link_score": fuzzy_score,
                "reported_level_delta": (
                    child["level"] - matched_parent_level
                    if not pd.isna(matched_parent_level)
                    else np.nan
                ),
                "same_jurisdiction_edge": int(
                    child["entity_country_std"] == matched_parent_country
                ),
                "cross_border_edge": int(
                    child["entity_country_std"] != matched_parent_country
                ),
                "stake": child["stake"],
                "uin": child["uin"],
                "sector_code": child["sector_code"],
            }
        )
    return pd.DataFrame(rows)


def build_paths(
    occurrences: pd.DataFrame, edges: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    occurrence_records = occurrences.set_index("target_id", drop=False).to_dict("index")
    edge_records = edges.set_index("child_target_id", drop=False).to_dict("index")
    path_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []

    for target_id in occurrences["target_id"]:
        chain: list[dict[str, Any]] = []
        seen: set[str] = set()
        current_id: str | None = target_id
        path_status = ""
        terminal_note = ""

        while current_id is not None:
            if current_id in seen:
                path_status = "cycle_detected"
                terminal_note = current_id
                break
            seen.add(current_id)
            current = occurrence_records[current_id]
            chain.append(
                {
                    "node_kind": "observed_entity",
                    "node_id": current["group_entity_id"],
                    "target_id": current_id,
                    "entity_name": current["entity_name"],
                    "country": current["entity_country_std"],
                    "reported_level": current["level"],
                }
            )
            edge = edge_records[current_id]
            if edge["parent_node_type"] == "ultimate_parent":
                chain.append(
                    {
                        "node_kind": "ultimate_parent",
                        "node_id": edge["parent_node_id"],
                        "target_id": pd.NA,
                        "entity_name": edge["parent"],
                        "country": "INDIA",
                        "reported_level": -1,
                    }
                )
                path_status = "complete_to_ultimate_parent"
                break
            if edge["parent_node_type"] == "observed_entity":
                current_id = edge["matched_parent_target_id"]
                continue
            chain.append(
                {
                    "node_kind": edge["parent_node_type"],
                    "node_id": edge["parent_node_id"],
                    "target_id": pd.NA,
                    "entity_name": edge["reported_immediate_parent"],
                    "country": edge["reported_immediate_parent_country"],
                    "reported_level": pd.NA,
                }
            )
            path_status = (
                "truncated_ambiguous_parent"
                if edge["parent_node_type"] == "ambiguous_entity"
                else "truncated_unobserved_parent"
            )
            terminal_note = edge["link_status"]
            break

        ordered = list(reversed(chain))
        observed_count = sum(step["node_kind"] == "observed_entity" for step in ordered)
        reconstructed_level = (
            observed_count - 1
            if path_status == "complete_to_ultimate_parent"
            else np.nan
        )
        occurrence = occurrence_records[target_id]
        path_rows.append(
            {
                "target_id": target_id,
                "parent": occurrence["parent"],
                "group_entity_id": occurrence["group_entity_id"],
                "global_entity_id": occurrence["global_entity_id"],
                "entity_name": occurrence["entity_name"],
                "entity_country": occurrence["entity_country_std"],
                "reported_level": occurrence["level"],
                "path_status": path_status,
                "terminal_note": terminal_note,
                "observed_entities_in_path": observed_count,
                "reconstructed_level": reconstructed_level,
                "reported_level_matches_reconstruction": (
                    int(reconstructed_level == occurrence["level"])
                    if not pd.isna(reconstructed_level)
                    else pd.NA
                ),
                "path_node_ids": " > ".join(str(step["node_id"]) for step in ordered),
                "path_target_ids": " > ".join(
                    str(step["target_id"])
                    for step in ordered
                    if not pd.isna(step["target_id"])
                ),
                "path_entity_names": " > ".join(
                    str(step["entity_name"]) for step in ordered
                ),
                "path_countries": " > ".join(
                    str(step["country"]) for step in ordered
                ),
            }
        )
        for position, step in enumerate(ordered):
            step_rows.append(
                {
                    "terminal_target_id": target_id,
                    "parent": occurrence["parent"],
                    "path_status": path_status,
                    "step_from_upstream": position,
                    "step_from_terminal": len(ordered) - position - 1,
                    **step,
                }
            )
    return pd.DataFrame(path_rows), pd.DataFrame(step_rows)


def graph_tables(
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    edges: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, set[str]]:
    logical_edges = (
        edges.groupby(
            [
                "parent",
                "parent_node_id",
                "parent_node_type",
                "matched_parent_name",
                "matched_parent_country",
                "child_group_entity_id",
                "child_entity_name",
                "child_country",
            ],
            dropna=False,
        )
        .agg(
            target_occurrences=("child_target_id", "size"),
            child_target_ids=("child_target_id", join_unique),
            reported_levels=("reported_level", list_unique_int),
            link_statuses=("link_status", join_unique),
            stakes=("stake", join_unique),
        )
        .reset_index()
    )
    logical_edges["logical_edge_id"] = logical_edges.apply(
        lambda row: stable_id(
            "ledge", row["parent"], row["parent_node_id"], row["child_group_entity_id"]
        ),
        axis=1,
    )

    indegree = logical_edges.groupby("child_group_entity_id").agg(
        distinct_parent_nodes=("parent_node_id", "nunique"),
        parent_nodes=("parent_node_id", join_unique),
        parent_names=("matched_parent_name", join_unique),
        parent_countries=("matched_parent_country", join_unique),
    )
    multiple_parent_entities = (
        group_entities.merge(
            indegree, left_on="group_entity_id", right_index=True, how="left"
        )
        .query("distinct_parent_nodes > 1")
        .sort_values("distinct_parent_nodes", ascending=False)
    )

    node_meta: dict[str, dict[str, Any]] = {}
    for row in group_entities.itertuples():
        node_meta[row.group_entity_id] = {
            "node_type": "observed_entity",
            "node_name": row.canonical_entity_name,
            "node_country": row.entity_country,
            "parent": row.parent,
        }
    for row in logical_edges.itertuples():
        node_meta.setdefault(
            row.parent_node_id,
            {
                "node_type": row.parent_node_type,
                "node_name": row.matched_parent_name,
                "node_country": row.matched_parent_country,
                "parent": row.parent,
            },
        )

    outdegree = logical_edges.groupby("parent_node_id").agg(
        direct_children=("child_group_entity_id", "nunique"),
        child_countries=("child_country", "nunique"),
        cross_border_children=(
            "child_country",
            lambda values: 0,
        ),
    )
    # Compute cross-border counts explicitly because groupby aggregators do not
    # have row-wise access to the parent country.
    cross_counts = (
        logical_edges.assign(
            cross=lambda frame: frame["matched_parent_country"] != frame["child_country"]
        )
        .groupby("parent_node_id")["cross"]
        .sum()
    )
    outdegree["cross_border_children"] = cross_counts
    hub_rows: list[dict[str, Any]] = []
    for node_id, metrics in outdegree.iterrows():
        meta = node_meta[node_id]
        hub_rows.append(
            {
                "node_id": node_id,
                **meta,
                "direct_children": int(metrics["direct_children"]),
                "child_countries": int(metrics["child_countries"]),
                "cross_border_children": int(metrics["cross_border_children"]),
            }
        )
    branch_hubs = pd.DataFrame(hub_rows).sort_values(
        ["direct_children", "child_countries"], ascending=False
    )

    observed_nodes = set(group_entities["group_entity_id"])
    parent_nodes = set(logical_edges["parent_node_id"])
    leaf_nodes = observed_nodes - parent_nodes
    return logical_edges, multiple_parent_entities, branch_hubs, leaf_nodes


def add_financial_fields(
    df: pd.DataFrame, occurrences: pd.DataFrame, paths: pd.DataFrame
) -> pd.DataFrame:
    preferred = df[df["preferred_for_target_year"] == 1].copy()
    attachment = occurrences[
        [
            "target_id",
            "group_entity_id",
            "global_entity_id",
            "entity_country_std",
            "depth_bin",
        ]
    ]
    preferred = preferred.merge(attachment, on="target_id", how="left", validate="many_to_one")
    preferred = preferred.merge(
        paths[
            [
                "target_id",
                "path_status",
                "reconstructed_level",
                "reported_level_matches_reconstruction",
            ]
        ],
        on="target_id",
        how="left",
        validate="many_to_one",
    )
    preferred["reconstructed_depth_bin"] = pd.cut(
        preferred["reconstructed_level"], DEPTH_BINS, labels=DEPTH_LABELS
    ).astype("string")
    preferred["period_date_parsed"] = preferred["period_end_date"].map(
        parse_period_date
    )
    windows = preferred["fiscal_year"].map(fiscal_window)
    preferred["fiscal_window_start"] = [value[0] for value in windows]
    preferred["fiscal_window_end"] = [value[1] for value in windows]
    comparable = (
        preferred["period_date_parsed"].notna()
        & preferred["fiscal_window_start"].notna()
    )
    preferred["period_date_within_fiscal_window"] = pd.Series(pd.NA, index=preferred.index, dtype="Int64")
    preferred.loc[comparable, "period_date_within_fiscal_window"] = (
        (
            preferred.loc[comparable, "period_date_parsed"]
            >= preferred.loc[comparable, "fiscal_window_start"]
        )
        & (
            preferred.loc[comparable, "period_date_parsed"]
            <= preferred.loc[comparable, "fiscal_window_end"]
        )
    ).astype(int)

    preferred["leverage_assets"] = (
        preferred["total_liabilities"] / preferred["total_assets"]
    )
    preferred["equity_assets"] = preferred["equity"] / preferred["total_assets"]
    preferred["roa_pat"] = preferred["profit_after_tax"] / preferred["total_assets"]
    preferred["profit_margin"] = (
        preferred["profit_after_tax"] / preferred["turnover"]
    )
    preferred["balance_ready"] = preferred["ready_for_valuation"].eq(1)
    preferred["balance_basic_plausible"] = (
        preferred["balance_ready"]
        & preferred["total_assets"].gt(0)
        & preferred["total_liabilities"].ge(0)
        & np.isfinite(preferred["leverage_assets"])
    )
    preferred["balance_ratio_sensitivity"] = (
        preferred["balance_basic_plausible"]
        & preferred["leverage_assets"].between(0, 10, inclusive="both")
    )
    preferred["pl_valid"] = (
        preferred["balance_basic_plausible"]
        & preferred["pl_identity_ok"].eq(1)
        & preferred["profit_after_tax"].notna()
        & np.isfinite(preferred["roa_pat"])
    )
    preferred["pl_ratio_sensitivity"] = preferred["pl_valid"] & preferred[
        "roa_pat"
    ].between(-2, 2, inclusive="both")
    preferred["negative_equity"] = preferred["equity"].lt(0)
    preferred["loss_after_tax"] = preferred["profit_after_tax"].lt(0)
    preferred["negative_operating_cash_flow"] = preferred["cash_flow_operating"].lt(0)
    return preferred


def audit_tables(
    df: pd.DataFrame,
    preferred: pd.DataFrame,
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    global_entities: pd.DataFrame,
    invariance: pd.DataFrame,
    edges: pd.DataFrame,
    paths: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    target_year_size = df.groupby(["target_id", "fiscal_year"], dropna=False).size()
    preferred_per_key = df.groupby(
        ["target_id", "fiscal_year"], dropna=False
    )["preferred_for_target_year"].sum()
    denominators = pd.DataFrame(
        [
            ("source_observation_rows", len(df), "all source candidates"),
            (
                "preferred_target_year_rows",
                len(preferred),
                "one selected row per target_id x fiscal_year, blank year is a key",
            ),
            ("structural_target_occurrences", len(occurrences), "unique target_id"),
            (
                "parent_scoped_exact_named_entities",
                occurrences[["parent", "entity_country", "entity_name"]]
                .drop_duplicates()
                .shape[0],
                "parent + raw country + exact entity name",
            ),
            (
                "parent_scoped_normalized_entities",
                group_entities["group_entity_id"].nunique(),
                "parent + standardized country + punctuation-normalized name",
            ),
            (
                "global_exact_named_entities",
                occurrences[["entity_country", "entity_name"]]
                .drop_duplicates()
                .shape[0],
                "raw country + exact entity name; parent ignored",
            ),
            (
                "global_normalized_entities",
                global_entities["global_entity_id"].nunique(),
                "standardized country + punctuation-normalized name; parent ignored",
            ),
            ("unique_uins", occurrences["uin"].nunique(), "UIN is not an entity ID"),
            ("ultimate_parent_buckets", occurrences["parent"].nunique(), "parent"),
            (
                "complete_paths",
                int(paths["path_status"].eq("complete_to_ultimate_parent").sum()),
                "recursion reaches named Indian parent",
            ),
        ],
        columns=["denominator", "count", "definition"],
    )

    missing_rows: list[dict[str, Any]] = []
    for column in df.columns:
        for sample_name, sample in [
            ("raw_source_rows", df),
            ("preferred_target_year_rows", preferred),
            ("structural_target_occurrences", occurrences),
        ]:
            if column not in sample.columns:
                continue
            n_missing = int(sample[column].isna().sum())
            missing_rows.append(
                {
                    "sample": sample_name,
                    "variable": column,
                    "rows": len(sample),
                    "missing": n_missing,
                    "missing_percent": pct(n_missing, len(sample)),
                    "nonmissing": len(sample) - n_missing,
                }
            )
    missingness = pd.DataFrame(missing_rows)

    duplicate_target_years = (
        target_year_size.rename("source_rows")
        .reset_index()
        .merge(
            preferred_per_key.rename("preferred_rows").reset_index(),
            on=["target_id", "fiscal_year"],
            how="left",
        )
        .query("source_rows > 1")
        .sort_values("source_rows", ascending=False)
    )
    duplicate_summary = pd.DataFrame(
        {
            "source_rows_per_target_year": target_year_size.value_counts()
            .sort_index()
            .index,
            "target_year_keys": target_year_size.value_counts().sort_index().values,
        }
    )
    duplicate_structure_summary = pd.DataFrame(
        [
            {
                "structure": "fully identical source rows beyond first",
                "count": int(df.duplicated().sum()),
                "definition": "all 77 fields identical",
            },
            {
                "structure": "source rows involved in a fully identical duplicate",
                "count": int(df.duplicated(keep=False).sum()),
                "definition": "all 77 fields identical",
            },
            {
                "structure": "target-year keys with multiple candidate source rows",
                "count": int((target_year_size > 1).sum()),
                "definition": "target_id x fiscal_year, missing year retained as a value",
            },
            {
                "structure": "nonpreferred candidate source rows",
                "count": int(df["preferred_for_target_year"].eq(0).sum()),
                "definition": "rows removed by upstream within-target-year preference",
            },
            {
                "structure": "targets represented by multiple source rows or years",
                "count": int((df.groupby("target_id").size() > 1).sum()),
                "definition": "unique target_id with two or more raw rows",
            },
            {
                "structure": "maximum raw rows for one target",
                "count": int(df.groupby("target_id").size().max()),
                "definition": "panel/source multiplicity",
            },
        ]
    )

    nonroot_edges = edges[edges["reported_level"] > 0]
    nonroot_status_counts = nonroot_edges["link_status"].value_counts()
    link_summary = (
        edges.groupby("link_status", dropna=False)
        .agg(edges=("child_target_id", "size"), parents=("parent", "nunique"))
        .reset_index()
    )
    link_summary["percent_all_edges"] = 100 * link_summary["edges"] / len(edges)
    link_summary["nonroot_edges"] = link_summary["link_status"].map(
        nonroot_status_counts
    ).fillna(0).astype(int)
    link_summary["percent_nonroot_edges"] = (
        100 * link_summary["nonroot_edges"] / len(nonroot_edges)
    )
    linkage_problems = edges[
        ~edges["link_status"].isin(
            [
                "ultimate_parent_root",
                "exact_expected_level",
                "normalized_expected_level",
                "fuzzy_expected_level",
            ]
        )
    ].copy()

    path_summary = (
        paths.groupby("path_status", dropna=False)
        .agg(paths=("target_id", "size"), parents=("parent", "nunique"))
        .reset_index()
    )
    path_summary["percent"] = 100 * path_summary["paths"] / len(paths)
    path_reconstruction_mismatches = paths[
        paths["reported_level_matches_reconstruction"].eq(0)
    ].copy()
    path_reconstruction_mismatches["reconstructed_minus_reported"] = (
        path_reconstruction_mismatches["reconstructed_level"]
        - path_reconstruction_mismatches["reported_level"]
    )

    depth_reconstruction = (
        paths[paths["path_status"].eq("complete_to_ultimate_parent")]
        .groupby(["reported_level", "reconstructed_level"], dropna=False)
        .size()
        .rename("target_occurrences")
        .reset_index()
    )

    country_labels = []
    raw_country_values = pd.concat(
        [occurrences["entity_country"], occurrences["immediate_parent_country"]]
    )
    for raw, count in raw_country_values.value_counts().items():
        raw_text = str(raw)
        country_labels.append(
            {
                "raw_label": raw_text,
                "standardized_label": normalize_country(raw_text),
                "occurrences_across_child_and_parent_fields": int(count),
                "flagged_for_review": int(raw_text in COUNTRY_LABEL_NOTES),
                "note": COUNTRY_LABEL_NOTES.get(raw_text, ""),
            }
        )
    country_label_quality = pd.DataFrame(country_labels).sort_values(
        ["flagged_for_review", "occurrences_across_child_and_parent_fields"],
        ascending=[False, False],
    )

    review_counter: Counter[str] = Counter()
    for value in preferred["review_reason"].dropna():
        for reason in str(value).split(";"):
            if reason.strip():
                review_counter[reason.strip()] += 1
    review_reasons = pd.DataFrame(
        [
            {
                "review_reason": reason,
                "preferred_rows": count,
                "percent_preferred_rows": pct(count, len(preferred)),
            }
            for reason, count in review_counter.most_common()
        ]
    )

    quality_flags = []
    for variable in [
        "source_found",
        "pdf_downloaded",
        "variables_parsed",
        "accounting_identity_ok",
        "needs_manual_review",
        "ready_for_valuation",
        "pl_identity_ok",
    ]:
        counts = preferred[variable].value_counts(dropna=False)
        for value, count in counts.items():
            quality_flags.append(
                {
                    "variable": variable,
                    "value": value,
                    "preferred_rows": int(count),
                    "percent": pct(count, len(preferred)),
                }
            )
    quality_flags = pd.DataFrame(quality_flags)

    nonroot = occurrences[occurrences["level"] > 0]
    stake_rows = []
    for sample_name, sample in [
        ("all_structural_targets", occurrences),
        ("nonroot_targets", nonroot),
    ]:
        stake_rows.extend(
            [
                {
                    "sample": sample_name,
                    "category": "missing",
                    "count": int(sample["stake"].isna().sum()),
                    "percent": pct(sample["stake"].isna().sum(), len(sample)),
                },
                {
                    "sample": sample_name,
                    "category": "zero",
                    "count": int(sample["stake"].eq(0).sum()),
                    "percent": pct(sample["stake"].eq(0).sum(), len(sample)),
                },
                {
                    "sample": sample_name,
                    "category": "between_0_and_100",
                    "count": int(sample["stake"].between(0, 100, inclusive="neither").sum()),
                    "percent": pct(
                        sample["stake"].between(0, 100, inclusive="neither").sum(),
                        len(sample),
                    ),
                },
                {
                    "sample": sample_name,
                    "category": "exactly_100",
                    "count": int(sample["stake"].eq(100).sum()),
                    "percent": pct(sample["stake"].eq(100).sum(), len(sample)),
                },
            ]
        )
    stake_quality = pd.DataFrame(stake_rows)

    date_rows = [
        ("preferred_rows", len(preferred)),
        ("blank_fiscal_year", int(preferred["fiscal_year"].isna().sum())),
        ("blank_period_end", int(preferred["period_end_date"].isna().sum())),
        (
            "parseable_period_end",
            int(preferred["period_date_parsed"].notna().sum()),
        ),
        (
            "date_and_fiscal_year_comparable",
            int(preferred["period_date_within_fiscal_window"].notna().sum()),
        ),
        (
            "period_end_outside_fiscal_window",
            int(preferred["period_date_within_fiscal_window"].eq(0).sum()),
        ),
    ]
    date_quality = pd.DataFrame(date_rows, columns=["metric", "count"])

    return {
        "row_denominators": denominators,
        "variable_missingness": missingness,
        "structural_invariance": invariance,
        "duplicate_target_years": duplicate_target_years,
        "duplicate_target_year_summary": duplicate_summary,
        "duplicate_structure_summary": duplicate_structure_summary,
        "hierarchy_linkage_summary": link_summary,
        "hierarchy_linkage_problems": linkage_problems,
        "path_completion_summary": path_summary,
        "path_reconstruction_mismatches": path_reconstruction_mismatches,
        "reported_vs_reconstructed_depth": depth_reconstruction,
        "country_label_quality": country_label_quality,
        "review_reasons": review_reasons,
        "quality_flags": quality_flags,
        "stake_quality": stake_quality,
        "date_quality": date_quality,
    }


def parent_analytics(
    df: pd.DataFrame,
    preferred: pd.DataFrame,
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    edges: pd.DataFrame,
    paths: pd.DataFrame,
    logical_edges: pd.DataFrame,
    leaf_nodes: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel_by_parent = preferred.groupby("parent").agg(
        preferred_target_year_rows=("target_id", "size"),
        dated_target_year_rows=("fiscal_year", "count"),
        panel_years=("fiscal_year", "nunique"),
        ready_target_year_rows=("ready_for_valuation", "sum"),
        source_found_target_year_rows=("source_found", "sum"),
        basic_plausible_target_year_rows=("balance_basic_plausible", "sum"),
        pl_valid_target_year_rows=("pl_valid", "sum"),
    )
    entity_coverage = (
        preferred.groupby(["parent", "target_id"])
        .agg(
            any_ready=("ready_for_valuation", "max"),
            observed_target_years=("target_id", "size"),
        )
        .reset_index()
        .groupby("parent")
        .agg(
            entities_with_any_ready=("any_ready", "sum"),
            mean_target_years_per_entity=("observed_target_years", "mean"),
        )
    )

    parent_rows: list[dict[str, Any]] = []
    for parent, occurrence_group in occurrences.groupby("parent"):
        ge = group_entities[group_entities["parent"] == parent]
        edge_group = edges[edges["parent"] == parent]
        logical_group = logical_edges[logical_edges["parent"] == parent]
        path_group = paths[paths["parent"] == parent]
        complete_path_group = path_group[
            path_group["path_status"].eq("complete_to_ultimate_parent")
        ]
        country_counts = ge["entity_country"].value_counts()
        entropy, hhi, effective = entropy_and_hhi(country_counts)
        top_country = country_counts.index[0]
        top_country_count = int(country_counts.iloc[0])
        observed_parent_edges = logical_group[
            logical_group["parent_node_type"] == "observed_entity"
        ]
        outdegrees = observed_parent_edges.groupby("parent_node_id")[
            "child_group_entity_id"
        ].nunique()
        leaf_count = int(ge["group_entity_id"].isin(leaf_nodes).sum())
        nonroot_edges = edge_group[edge_group["reported_level"] > 0]
        expected_links = nonroot_edges["link_status"].isin(
            [
                "exact_expected_level",
                "normalized_expected_level",
                "fuzzy_expected_level",
            ]
        ).sum()
        panel = panel_by_parent.loc[parent]
        coverage = entity_coverage.loc[parent]
        parent_rows.append(
            {
                "parent": parent,
                "raw_source_rows": int((df["parent"] == parent).sum()),
                "structural_target_occurrences": len(occurrence_group),
                "normalized_group_entities": len(ge),
                "global_entity_ids_in_group": occurrence_group[
                    "global_entity_id"
                ].nunique(),
                "unique_uins": occurrence_group["uin"].nunique(),
                "entities_per_uin": len(ge) / occurrence_group["uin"].nunique(),
                "jurisdictions": ge["entity_country"].nunique(),
                "country_entropy": entropy,
                "country_hhi": hhi,
                "effective_jurisdictions": effective,
                "top_jurisdiction": top_country,
                "top_jurisdiction_entities": top_country_count,
                "top_jurisdiction_share_percent": pct(top_country_count, len(ge)),
                "direct_level_0_occurrences": int(occurrence_group["level"].eq(0).sum()),
                "mean_reported_level": occurrence_group["level"].mean(),
                "median_reported_level": occurrence_group["level"].median(),
                "maximum_reported_level": occurrence_group["level"].max(),
                "level_3plus_occurrences": int(occurrence_group["level"].ge(3).sum()),
                "level_3plus_share_percent": pct(
                    occurrence_group["level"].ge(3).sum(), len(occurrence_group)
                ),
                "level_5plus_occurrences": int(occurrence_group["level"].ge(5).sum()),
                "level_5plus_share_percent": pct(
                    occurrence_group["level"].ge(5).sum(), len(occurrence_group)
                ),
                "complete_paths": int(
                    path_group["path_status"].eq("complete_to_ultimate_parent").sum()
                ),
                "complete_path_share_percent": pct(
                    path_group["path_status"].eq("complete_to_ultimate_parent").sum(),
                    len(path_group),
                ),
                "complete_paths_with_depth_mismatch": int(
                    complete_path_group[
                        "reported_level_matches_reconstruction"
                    ].eq(0).sum()
                ),
                "complete_depth_mismatch_share_percent": pct(
                    complete_path_group[
                        "reported_level_matches_reconstruction"
                    ].eq(0).sum(),
                    len(complete_path_group),
                ),
                "mean_reconstructed_level_complete": complete_path_group[
                    "reconstructed_level"
                ].mean(),
                "maximum_reconstructed_level_complete": complete_path_group[
                    "reconstructed_level"
                ].max(),
                "reconstructed_level_5plus_complete": int(
                    complete_path_group["reconstructed_level"].ge(5).sum()
                ),
                "reconstructed_level_5plus_share_complete_percent": pct(
                    complete_path_group["reconstructed_level"].ge(5).sum(),
                    len(complete_path_group),
                ),
                "nonroot_edges": len(nonroot_edges),
                "expected_level_links": int(expected_links),
                "expected_level_link_share_percent": pct(
                    expected_links, len(nonroot_edges)
                ),
                "cross_border_edges": int(edge_group["cross_border_edge"].sum()),
                "cross_border_edge_share_percent": pct(
                    edge_group["cross_border_edge"].sum(), len(edge_group)
                ),
                "nonroot_cross_border_edges": int(
                    nonroot_edges["cross_border_edge"].sum()
                ),
                "nonroot_cross_border_share_percent": pct(
                    nonroot_edges["cross_border_edge"].sum(), len(nonroot_edges)
                ),
                "leaf_entities": leaf_count,
                "leaf_share_percent": pct(leaf_count, len(ge)),
                "branching_entities": int(len(outdegrees)),
                "maximum_observed_outdegree": int(outdegrees.max())
                if len(outdegrees)
                else 0,
                "mean_observed_outdegree_among_parents": outdegrees.mean()
                if len(outdegrees)
                else 0,
                "zero_stake_nonroot_edges": int(nonroot_edges["stake"].eq(0).sum()),
                "zero_stake_nonroot_share_percent": pct(
                    nonroot_edges["stake"].eq(0).sum(), len(nonroot_edges)
                ),
                "preferred_target_year_rows": int(
                    panel["preferred_target_year_rows"]
                ),
                "dated_target_year_rows": int(panel["dated_target_year_rows"]),
                "panel_years": int(panel["panel_years"]),
                "mean_target_years_per_entity": coverage[
                    "mean_target_years_per_entity"
                ],
                "ready_target_year_rows": int(panel["ready_target_year_rows"]),
                "ready_target_year_rate_percent": pct(
                    panel["ready_target_year_rows"],
                    panel["preferred_target_year_rows"],
                ),
                "entities_with_any_ready": int(coverage["entities_with_any_ready"]),
                "entity_any_ready_rate_percent": pct(
                    coverage["entities_with_any_ready"], len(occurrence_group)
                ),
                "source_found_target_year_rate_percent": pct(
                    panel["source_found_target_year_rows"],
                    panel["preferred_target_year_rows"],
                ),
                "basic_plausible_target_year_rows": int(
                    panel["basic_plausible_target_year_rows"]
                ),
                "pl_valid_target_year_rows": int(panel["pl_valid_target_year_rows"]),
            }
        )
    parent_table = pd.DataFrame(parent_rows).sort_values(
        "normalized_group_entities", ascending=False
    )
    parent_table["pooled_entity_share_percent"] = (
        100
        * parent_table["normalized_group_entities"]
        / parent_table["normalized_group_entities"].sum()
    )
    parent_table["raw_row_share_percent"] = (
        100 * parent_table["raw_source_rows"] / parent_table["raw_source_rows"].sum()
    )
    parent_table["raw_to_entity_share_ratio"] = (
        parent_table["raw_row_share_percent"]
        / parent_table["pooled_entity_share_percent"]
    )

    parent_jurisdiction = (
        occurrences.groupby(["parent", "entity_country_std"], dropna=False)
        .agg(
            target_occurrences=("target_id", "size"),
            normalized_group_entities=("group_entity_id", "nunique"),
            global_entities=("global_entity_id", "nunique"),
            unique_uins=("uin", "nunique"),
            mean_reported_level=("level", "mean"),
            maximum_reported_level=("level", "max"),
            direct_level_0=("level", lambda values: int((values == 0).sum())),
            level_3plus=("level", lambda values: int((values >= 3).sum())),
        )
        .reset_index()
        .rename(columns={"entity_country_std": "jurisdiction"})
    )
    totals = parent_jurisdiction.groupby("parent")["normalized_group_entities"].transform(
        "sum"
    )
    parent_jurisdiction["within_parent_entity_share_percent"] = (
        100 * parent_jurisdiction["normalized_group_entities"] / totals
    )

    parent_depth = pd.crosstab(occurrences["parent"], occurrences["depth_bin"])
    parent_depth = parent_depth.reindex(columns=DEPTH_LABELS, fill_value=0).reset_index()
    parent_depth["total"] = parent_depth[DEPTH_LABELS].sum(axis=1)
    for label in DEPTH_LABELS:
        parent_depth[f"share_{label}_percent"] = 100 * parent_depth[label] / parent_depth["total"]
    return parent_table, parent_jurisdiction, parent_depth


def geography_tables(
    df: pd.DataFrame,
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    global_entities: pd.DataFrame,
    edges: pd.DataFrame,
    paths: pd.DataFrame,
    path_steps: pd.DataFrame,
    logical_edges: pd.DataFrame,
    leaf_nodes: set[str],
) -> dict[str, pd.DataFrame]:
    raw_counts = df.groupby(df["entity_country"].map(normalize_country)).size()
    occurrence_counts = occurrences.groupby("entity_country_std").size()
    group_counts = group_entities.groupby("entity_country").size()
    global_counts = global_entities.groupby("entity_country").size()
    parent_presence = group_entities.groupby("entity_country")["parent"].nunique()

    complete_steps = path_steps[
        (path_steps["path_status"] == "complete_to_ultimate_parent")
        & (path_steps["node_kind"] == "observed_entity")
    ]
    ancestry_counts = complete_steps.groupby("country").size()
    ancestry_parent = (
        complete_steps.groupby(["parent", "country"])
        .size()
        .rename("n")
        .reset_index()
    )
    ancestry_parent["share"] = ancestry_parent["n"] / ancestry_parent.groupby(
        "parent"
    )["n"].transform("sum")
    ancestry_grid = pd.MultiIndex.from_product(
        [
            sorted(group_entities["parent"].unique()),
            sorted(group_entities["entity_country"].dropna().unique()),
        ],
        names=["parent", "country"],
    ).to_frame(index=False)
    ancestry_grid = ancestry_grid.merge(
        ancestry_parent, on=["parent", "country"], how="left"
    ).fillna({"n": 0, "share": 0})
    ancestry_balanced = ancestry_grid.groupby("country")["share"].mean()
    leaf_occurrences = occurrences[occurrences["group_entity_id"].isin(leaf_nodes)]
    leaf_counts = leaf_occurrences.groupby("entity_country_std").size()

    parent_country_counts = (
        group_entities.groupby(["parent", "entity_country"]).size().rename("n").reset_index()
    )
    parent_totals = parent_country_counts.groupby("parent")["n"].transform("sum")
    parent_country_counts["share"] = parent_country_counts["n"] / parent_totals
    parents = sorted(group_entities["parent"].unique())
    countries = sorted(group_entities["entity_country"].dropna().unique())
    full_grid = pd.MultiIndex.from_product(
        [parents, countries], names=["parent", "entity_country"]
    ).to_frame(index=False)
    full_grid = full_grid.merge(
        parent_country_counts, on=["parent", "entity_country"], how="left"
    ).fillna({"n": 0, "share": 0})
    balanced = full_grid.groupby("entity_country")["share"].agg(
        equal_parent_mean_share="mean",
        median_parent_share="median",
        maximum_parent_share="max",
    )
    max_parent = (
        full_grid.sort_values("share", ascending=False)
        .drop_duplicates("entity_country")
        .set_index("entity_country")["parent"]
    )

    rows: list[dict[str, Any]] = []
    total_group = len(group_entities)
    total_global = len(global_entities)
    for country in countries:
        country_parent_counts = parent_country_counts[
            parent_country_counts["entity_country"] == country
        ].set_index("parent")["n"]
        loo_shares = []
        for omitted in parents:
            numerator = group_counts.get(country, 0) - country_parent_counts.get(omitted, 0)
            denominator = total_group - int(
                (group_entities["parent"] == omitted).sum()
            )
            loo_shares.append(numerator / denominator if denominator else np.nan)
        rows.append(
            {
                "jurisdiction": country,
                "raw_source_rows": int(raw_counts.get(country, 0)),
                "raw_row_share_percent": pct(raw_counts.get(country, 0), len(df)),
                "structural_target_occurrences": int(occurrence_counts.get(country, 0)),
                "normalized_group_entities": int(group_counts.get(country, 0)),
                "pooled_group_entity_share_percent": pct(
                    group_counts.get(country, 0), total_group
                ),
                "global_unique_entities": int(global_counts.get(country, 0)),
                "global_entity_share_percent": pct(
                    global_counts.get(country, 0), total_global
                ),
                "parent_groups_present": int(parent_presence.get(country, 0)),
                "equal_parent_mean_share_percent": 100
                * balanced.loc[country, "equal_parent_mean_share"],
                "median_parent_share_percent": 100
                * balanced.loc[country, "median_parent_share"],
                "maximum_parent_share_percent": 100
                * balanced.loc[country, "maximum_parent_share"],
                "maximum_share_parent": max_parent.loc[country],
                "complete_path_ancestry_appearances": int(ancestry_counts.get(country, 0)),
                "complete_path_ancestry_share_percent": pct(
                    ancestry_counts.get(country, 0), ancestry_counts.sum()
                ),
                "equal_parent_ancestry_share_percent": 100
                * ancestry_balanced.get(country, 0),
                "leaf_target_occurrences": int(leaf_counts.get(country, 0)),
                "leaf_share_percent": pct(leaf_counts.get(country, 0), leaf_counts.sum()),
                "leave_one_parent_out_min_share_percent": 100 * np.nanmin(loo_shares),
                "leave_one_parent_out_max_share_percent": 100 * np.nanmax(loo_shares),
            }
        )
    jurisdiction_counts = pd.DataFrame(rows).sort_values(
        "normalized_group_entities", ascending=False
    )

    loo_rows = []
    for omitted in parents:
        retained = group_entities[group_entities["parent"] != omitted]
        counts = retained["entity_country"].value_counts()
        for country in countries:
            loo_rows.append(
                {
                    "omitted_parent": omitted,
                    "jurisdiction": country,
                    "retained_entities": len(retained),
                    "jurisdiction_entities": int(counts.get(country, 0)),
                    "share_percent": pct(counts.get(country, 0), len(retained)),
                }
            )
    country_loo = pd.DataFrame(loo_rows)

    transition_occ = (
        edges.groupby(
            ["matched_parent_country", "child_country"], dropna=False
        )
        .agg(
            target_occurrences=("child_target_id", "size"),
            parent_groups=("parent", "nunique"),
            parent_nodes=("parent_node_id", "nunique"),
            child_entities=("child_group_entity_id", "nunique"),
        )
        .reset_index()
        .rename(
            columns={
                "matched_parent_country": "source_jurisdiction",
                "child_country": "destination_jurisdiction",
            }
        )
    )
    logical_transition = (
        logical_edges.groupby(
            ["matched_parent_country", "child_country"], dropna=False
        )
        .size()
        .rename("logical_edges")
        .reset_index()
        .rename(
            columns={
                "matched_parent_country": "source_jurisdiction",
                "child_country": "destination_jurisdiction",
            }
        )
    )
    transition_counts = transition_occ.merge(
        logical_transition,
        on=["source_jurisdiction", "destination_jurisdiction"],
        how="left",
    )
    transition_counts["cross_border"] = (
        transition_counts["source_jurisdiction"]
        != transition_counts["destination_jurisdiction"]
    ).astype(int)
    # Dominant-parent sensitivity for each transition.
    transition_parent = (
        edges.groupby(["matched_parent_country", "child_country", "parent"])
        .size()
        .rename("n")
        .reset_index()
    )
    dominant = (
        transition_parent.sort_values("n", ascending=False)
        .drop_duplicates(["matched_parent_country", "child_country"])
        .rename(
            columns={
                "matched_parent_country": "source_jurisdiction",
                "child_country": "destination_jurisdiction",
                "parent": "dominant_parent",
                "n": "dominant_parent_edges",
            }
        )
    )
    transition_counts = transition_counts.merge(
        dominant[
            [
                "source_jurisdiction",
                "destination_jurisdiction",
                "dominant_parent",
                "dominant_parent_edges",
            ]
        ],
        on=["source_jurisdiction", "destination_jurisdiction"],
        how="left",
    )
    transition_counts["dominant_parent_share_percent"] = (
        100
        * transition_counts["dominant_parent_edges"]
        / transition_counts["target_occurrences"]
    )
    transition_counts = transition_counts.sort_values(
        ["logical_edges", "parent_groups"], ascending=False
    )

    nonroot_edges = edges[edges["reported_level"] > 0]
    intermediary_rows = []
    for country, group in nonroot_edges.groupby("matched_parent_country", dropna=False):
        entity_count = int((group_entities["entity_country"] == country).sum())
        by_parent = group.groupby("parent").size()
        intermediary_rows.append(
            {
                "intermediary_jurisdiction": country,
                "outgoing_target_occurrences": len(group),
                "distinct_parent_nodes": group["parent_node_id"].nunique(),
                "resident_group_entities": entity_count,
                "outgoing_edges_per_resident_entity": (
                    len(group) / entity_count if entity_count else np.nan
                ),
                "cross_border_outgoing": int(group["cross_border_edge"].sum()),
                "cross_border_outgoing_share_percent": pct(
                    group["cross_border_edge"].sum(), len(group)
                ),
                "destination_jurisdictions": group["child_country"].nunique(),
                "parent_groups": group["parent"].nunique(),
                "dominant_parent": by_parent.idxmax(),
                "dominant_parent_share_percent": pct(by_parent.max(), len(group)),
            }
        )
    intermediary = pd.DataFrame(intermediary_rows).sort_values(
        ["cross_border_outgoing", "outgoing_target_occurrences"], ascending=False
    )

    depth_country = (
        occurrences.groupby(["depth_bin", "entity_country_std"], dropna=False)
        .agg(
            target_occurrences=("target_id", "size"),
            group_entities=("group_entity_id", "nunique"),
            parent_groups=("parent", "nunique"),
        )
        .reset_index()
        .rename(columns={"entity_country_std": "jurisdiction"})
    )
    depth_country["share_within_depth_percent"] = (
        100
        * depth_country["target_occurrences"]
        / depth_country.groupby("depth_bin")["target_occurrences"].transform("sum")
    )
    depth_parent_country = (
        occurrences.groupby(["depth_bin", "entity_country_std", "parent"])
        .size()
        .rename("n")
        .reset_index()
    )
    depth_dominant = (
        depth_parent_country.sort_values("n", ascending=False)
        .drop_duplicates(["depth_bin", "entity_country_std"])
        .rename(
            columns={
                "entity_country_std": "jurisdiction",
                "parent": "dominant_parent",
                "n": "dominant_parent_entities",
            }
        )
    )
    depth_country = depth_country.merge(
        depth_dominant[
            [
                "depth_bin",
                "jurisdiction",
                "dominant_parent",
                "dominant_parent_entities",
            ]
        ],
        on=["depth_bin", "jurisdiction"],
        how="left",
    )
    depth_country["dominant_parent_share_percent"] = (
        100
        * depth_country["dominant_parent_entities"]
        / depth_country["target_occurrences"]
    )
    depth_country = depth_country.sort_values(
        ["depth_bin", "target_occurrences"], ascending=[True, False]
    )

    edge_by_level_rows = []
    for level, group in edges.groupby("reported_level"):
        by_parent = group.groupby("parent")["cross_border_edge"].mean()
        edge_by_level_rows.append(
            {
                "reported_level": int(level),
                "edges": len(group),
                "parent_groups": group["parent"].nunique(),
                "cross_border_edges": int(group["cross_border_edge"].sum()),
                "pooled_cross_border_share_percent": pct(
                    group["cross_border_edge"].sum(), len(group)
                ),
                "equal_parent_cross_border_share_percent": 100 * by_parent.mean(),
                "same_jurisdiction_edges": int(group["same_jurisdiction_edge"].sum()),
            }
        )
    edge_geography_by_level = pd.DataFrame(edge_by_level_rows)

    category = np.select(
        [
            occurrences["entity_country_std"].eq("INDIA"),
            occurrences["entity_country_std"].eq("IFSC GIFT CITY"),
            occurrences["entity_country_std"].eq("EUROPEAN UNION"),
        ],
        ["India", "IFSC GIFT CITY special-zone label", "non-country regional label"],
        default="foreign jurisdiction label",
    )
    foreign_work = occurrences.assign(jurisdiction_category=category)
    foreign_domestic_summary = (
        foreign_work.groupby("jurisdiction_category")
        .agg(
            target_occurrences=("target_id", "size"),
            group_entities=("group_entity_id", "nunique"),
            parent_groups=("parent", "nunique"),
            minimum_level=("level", "min"),
            maximum_level=("level", "max"),
        )
        .reset_index()
    )
    foreign_domestic_summary["target_share_percent"] = (
        100 * foreign_domestic_summary["target_occurrences"] / len(occurrences)
    )
    domestic_special_entities = foreign_work[
        foreign_work["jurisdiction_category"] != "foreign jurisdiction label"
    ][
        [
            "target_id",
            "parent",
            "level",
            "entity_name",
            "entity_country",
            "entity_country_std",
            "jurisdiction_category",
            "immediate_parent",
            "uin",
        ]
    ].copy()

    # Leaf-only motifs avoid counting every prefix once per internal node, but
    # branching still repeats shared prefixes; parent concentration is reported.
    leaf_paths = paths[
        paths["group_entity_id"].isin(leaf_nodes)
        & paths["path_status"].eq("complete_to_ultimate_parent")
    ]
    motif_counter: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)
    full_counter: dict[str, list[str]] = defaultdict(list)
    for row in leaf_paths.itertuples():
        sequence = tuple(str(row.path_countries).split(" > "))
        full_counter[" > ".join(sequence)].append(row.parent)
        for ngram in (2, 3, 4):
            for index in range(len(sequence) - ngram + 1):
                motif_counter[sequence[index : index + ngram]].append(
                    (row.target_id, row.parent)
                )
    motif_rows = []
    for motif, path_parent_values in motif_counter.items():
        parent_values = [value[1] for value in path_parent_values]
        by_parent = Counter(parent_values)
        motif_rows.append(
            {
                "motif_length": len(motif),
                "jurisdiction_motif": " > ".join(motif),
                "motif_occurrences_within_leaf_paths": len(path_parent_values),
                "distinct_leaf_paths": len({value[0] for value in path_parent_values}),
                "parent_groups": len(by_parent),
                "dominant_parent": by_parent.most_common(1)[0][0],
                "dominant_parent_share_percent": pct(
                    by_parent.most_common(1)[0][1], len(parent_values)
                ),
            }
        )
    motifs = pd.DataFrame(motif_rows).sort_values(
        ["motif_occurrences_within_leaf_paths", "parent_groups"], ascending=False
    )
    full_rows = []
    for sequence, parent_values in full_counter.items():
        by_parent = Counter(parent_values)
        full_rows.append(
            {
                "full_jurisdiction_path": sequence,
                "leaf_path_occurrences": len(parent_values),
                "parent_groups": len(by_parent),
                "dominant_parent": by_parent.most_common(1)[0][0],
                "dominant_parent_share_percent": pct(
                    by_parent.most_common(1)[0][1], len(parent_values)
                ),
            }
        )
    full_motifs = pd.DataFrame(full_rows).sort_values(
        ["leaf_path_occurrences", "parent_groups"], ascending=False
    )
    return {
        "jurisdiction_counts": jurisdiction_counts,
        "leave_one_parent_out_country_shares": country_loo,
        "country_transitions": transition_counts,
        "intermediary_jurisdictions": intermediary,
        "jurisdiction_by_depth": depth_country,
        "edge_geography_by_level": edge_geography_by_level,
        "foreign_domestic_summary": foreign_domestic_summary,
        "domestic_special_zone_entities": domestic_special_entities,
        "leaf_path_motifs": motifs,
        "full_leaf_jurisdiction_paths": full_motifs,
    }


def financial_tables(
    df: pd.DataFrame,
    preferred: pd.DataFrame,
    occurrences: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    sample_rows = [
        {
            "sample": "preferred_target_year",
            "n": len(preferred),
            "definition": "preferred_for_target_year == 1; blank fiscal year retained as a key",
        },
        {
            "sample": "balance_ready",
            "n": int(preferred["balance_ready"].sum()),
            "definition": "ready_for_valuation == 1",
        },
        {
            "sample": "balance_basic_plausible",
            "n": int(preferred["balance_basic_plausible"].sum()),
            "definition": "balance_ready; assets > 0; liabilities >= 0; finite leverage",
        },
        {
            "sample": "balance_ratio_sensitivity",
            "n": int(preferred["balance_ratio_sensitivity"].sum()),
            "definition": "basic plausible plus 0 <= liabilities/assets <= 10",
        },
        {
            "sample": "pl_valid",
            "n": int(preferred["pl_valid"].sum()),
            "definition": "basic plausible; pl_identity_ok == 1; PAT present; finite ROA",
        },
        {
            "sample": "pl_ratio_sensitivity",
            "n": int(preferred["pl_ratio_sensitivity"].sum()),
            "definition": "pl_valid plus -2 <= PAT/assets <= 2",
        },
    ]
    financial_samples = pd.DataFrame(sample_rows)

    plausibility_rows = []
    ready = preferred[preferred["balance_ready"]]
    checks = {
        "nonpositive_total_assets": ready["total_assets"].le(0),
        "negative_total_assets": ready["total_assets"].lt(0),
        "negative_total_liabilities": ready["total_liabilities"].lt(0),
        "negative_equity": ready["equity"].lt(0),
        "leverage_above_10": ready["leverage_assets"].gt(10),
        "absolute_roa_above_2_among_pl_valid": ready["pl_valid"]
        & ready["roa_pat"].abs().gt(2),
    }
    for name, mask in checks.items():
        plausibility_rows.append(
            {
                "check": name,
                "flagged_ready_rows": int(mask.sum()),
                "ready_rows": len(ready),
                "percent_ready": pct(mask.sum(), len(ready)),
            }
        )
    financial_plausibility = pd.DataFrame(plausibility_rows)

    both_ownership = preferred[
        preferred["stake"].notna() & preferred["shareholding_percent"].notna()
    ].copy()
    both_ownership["shareholding_minus_mapping_stake"] = (
        both_ownership["shareholding_percent"] - both_ownership["stake"]
    )
    ownership_comparison = both_ownership[
        [
            "target_id",
            "parent",
            "entity_name",
            "level",
            "fiscal_year",
            "source_type",
            "stake",
            "shareholding_percent",
            "shareholding_minus_mapping_stake",
        ]
    ].sort_values("shareholding_minus_mapping_stake", key=lambda values: values.abs(), ascending=False)
    ownership_comparison_summary = pd.DataFrame(
        [
            {
                "metric": "preferred_rows_with_shareholding_percent",
                "count": int(preferred["shareholding_percent"].notna().sum()),
                "denominator": len(preferred),
                "percent": pct(preferred["shareholding_percent"].notna().sum(), len(preferred)),
            },
            {
                "metric": "preferred_rows_with_both_ownership_measures",
                "count": len(both_ownership),
                "denominator": len(preferred),
                "percent": pct(len(both_ownership), len(preferred)),
            },
            {
                "metric": "both_measures_absolute_difference_above_1pp",
                "count": int(
                    both_ownership["shareholding_minus_mapping_stake"].abs().gt(1).sum()
                ),
                "denominator": len(both_ownership),
                "percent": pct(
                    both_ownership["shareholding_minus_mapping_stake"].abs().gt(1).sum(),
                    len(both_ownership),
                ),
            },
            {
                "metric": "zero_mapping_stake_but_positive_shareholding",
                "count": int(
                    (
                        both_ownership["stake"].eq(0)
                        & both_ownership["shareholding_percent"].gt(0)
                    ).sum()
                ),
                "denominator": len(both_ownership),
                "percent": pct(
                    (
                        both_ownership["stake"].eq(0)
                        & both_ownership["shareholding_percent"].gt(0)
                    ).sum(),
                    len(both_ownership),
                ),
            },
        ]
    )

    # Exact repeated balance-sheet signatures can be legitimate (e.g. dormant
    # affiliates), aliases, or extraction reuse.  Preserve them for review.
    signature_columns = [
        "fiscal_year",
        "currency",
        "units",
        "total_assets",
        "total_liabilities",
        "equity",
    ]
    parsed = preferred[preferred["variables_parsed"].eq(1)]
    duplicate_signatures = (
        parsed.groupby(signature_columns, dropna=False)
        .agg(
            rows=("target_id", "size"),
            targets=("target_id", "nunique"),
            parent_groups=("parent", "nunique"),
            parents=("parent", join_unique),
            entities=("entity_name", lambda values: join_unique(values, limit=12)),
            target_ids=("target_id", lambda values: join_unique(values, limit=12)),
            source_urls=("source_url", "nunique"),
        )
        .reset_index()
        .query("targets > 1")
        .sort_values(["targets", "parent_groups"], ascending=False)
    )

    anomaly_mask = (
        preferred["balance_ready"]
        & (
            preferred["total_assets"].le(0)
            | preferred["total_liabilities"].lt(0)
            | preferred["leverage_assets"].gt(10)
            | (preferred["pl_valid"] & preferred["roa_pat"].abs().gt(2))
        )
    )
    anomaly_columns = [
        "target_id",
        "parent",
        "entity_name",
        "entity_country_std",
        "level",
        "fiscal_year",
        "currency",
        "units",
        "total_assets",
        "total_liabilities",
        "equity",
        "profit_after_tax",
        "leverage_assets",
        "roa_pat",
        "data_quality_tier",
        "review_reason",
        "total_assets_evidence",
        "total_liabilities_evidence",
        "equity_evidence",
        "profit_after_tax_evidence",
        "source_url",
    ]
    financial_anomalies = preferred.loc[anomaly_mask, anomaly_columns].copy()
    for evidence in [column for column in anomaly_columns if column.endswith("_evidence")]:
        financial_anomalies[evidence] = financial_anomalies[evidence].map(
            lambda value: str(value)[:300] if not pd.isna(value) else value
        )

    depth_rows = []
    for depth in DEPTH_LABELS:
        group = preferred[preferred["depth_bin"] == depth]
        basic = group[group["balance_basic_plausible"]]
        strict = group[group["balance_ratio_sensitivity"]]
        pl = group[group["pl_valid"]]
        pl_sensitive = group[group["pl_ratio_sensitivity"]]
        cfo = basic[basic["cash_flow_operating"].notna()]
        depth_rows.append(
            {
                "depth_bin": depth,
                "preferred_target_year_rows": len(group),
                "ready_rows": int(group["balance_ready"].sum()),
                "ready_rate_percent": pct(group["balance_ready"].sum(), len(group)),
                "basic_plausible_rows": len(basic),
                "strict_balance_rows": len(strict),
                "negative_equity_rows": int(basic["negative_equity"].sum()),
                "negative_equity_rate_percent": pct(
                    basic["negative_equity"].sum(), len(basic)
                ),
                "median_leverage_basic": basic["leverage_assets"].median(),
                "median_leverage_strict": strict["leverage_assets"].median(),
                "pl_valid_rows": len(pl),
                "loss_rows": int(pl["loss_after_tax"].sum()),
                "loss_rate_percent": pct(pl["loss_after_tax"].sum(), len(pl)),
                "median_roa_pl_valid": pl["roa_pat"].median(),
                "median_roa_sensitivity": pl_sensitive["roa_pat"].median(),
                "operating_cash_flow_rows": len(cfo),
                "negative_operating_cash_flow_rate_percent": pct(
                    cfo["negative_operating_cash_flow"].sum(), len(cfo)
                ),
            }
        )
    depth_financial = pd.DataFrame(depth_rows)

    reconstructed_depth_rows = []
    complete_financial = preferred[
        preferred["path_status"].eq("complete_to_ultimate_parent")
    ]
    for depth in DEPTH_LABELS:
        group = complete_financial[
            complete_financial["reconstructed_depth_bin"] == depth
        ]
        basic = group[group["balance_basic_plausible"]]
        pl = group[group["pl_valid"]]
        reconstructed_depth_rows.append(
            {
                "reconstructed_depth_bin": depth,
                "preferred_target_year_rows_complete_paths": len(group),
                "ready_rows": int(group["balance_ready"].sum()),
                "ready_rate_percent": pct(group["balance_ready"].sum(), len(group)),
                "basic_plausible_rows": len(basic),
                "negative_equity_rate_percent": pct(
                    basic["negative_equity"].sum(), len(basic)
                ),
                "pl_valid_rows": len(pl),
                "loss_rate_percent": pct(pl["loss_after_tax"].sum(), len(pl)),
            }
        )
    reconstructed_depth_financial = pd.DataFrame(reconstructed_depth_rows)

    # Entity-level coverage removes panel-length weighting.
    entity_financial = (
        preferred.groupby("target_id")
        .agg(
            parent=("parent", "first"),
            entity_name=("entity_name", "first"),
            country=("entity_country_std", "first"),
            level=("level", "first"),
            depth_bin=("depth_bin", "first"),
            target_year_rows=("target_id", "size"),
            dated_rows=("fiscal_year", "count"),
            any_source_found=("source_found", "max"),
            any_ready=("balance_ready", "max"),
            ready_years=("balance_ready", "sum"),
            basic_plausible_years=("balance_basic_plausible", "sum"),
            pl_valid_years=("pl_valid", "sum"),
            mean_negative_equity=(
                "negative_equity",
                lambda values: values[preferred.loc[values.index, "balance_basic_plausible"]].mean(),
            ),
            mean_loss_rate=(
                "loss_after_tax",
                lambda values: values[preferred.loc[values.index, "pl_valid"]].mean(),
            ),
            median_roa=(
                "roa_pat",
                lambda values: values[preferred.loc[values.index, "pl_valid"]].median(),
            ),
        )
        .reset_index()
    )
    entity_coverage_depth = (
        entity_financial.groupby("depth_bin", dropna=False)
        .agg(
            entities=("target_id", "size"),
            entities_with_source=("any_source_found", "sum"),
            entities_with_any_ready=("any_ready", "sum"),
            mean_panel_rows=("target_year_rows", "mean"),
        )
        .reset_index()
    )
    entity_coverage_depth["source_coverage_percent"] = (
        100
        * entity_coverage_depth["entities_with_source"]
        / entity_coverage_depth["entities"]
    )
    entity_coverage_depth["any_ready_percent"] = (
        100
        * entity_coverage_depth["entities_with_any_ready"]
        / entity_coverage_depth["entities"]
    )

    parent_financial = (
        preferred.groupby("parent")
        .agg(
            preferred_target_year_rows=("target_id", "size"),
            ready_target_year_rows=("balance_ready", "sum"),
            basic_plausible_rows=("balance_basic_plausible", "sum"),
            pl_valid_rows=("pl_valid", "sum"),
        )
        .join(
            entity_financial.groupby("parent").agg(
                entities=("target_id", "size"),
                entities_with_any_ready=("any_ready", "sum"),
                mean_panel_rows=("target_year_rows", "mean"),
            )
        )
        .reset_index()
    )
    parent_financial["target_year_ready_rate_percent"] = (
        100
        * parent_financial["ready_target_year_rows"]
        / parent_financial["preferred_target_year_rows"]
    )
    parent_financial["entity_any_ready_rate_percent"] = (
        100
        * parent_financial["entities_with_any_ready"]
        / parent_financial["entities"]
    )
    parent_financial = parent_financial.sort_values(
        "entity_any_ready_rate_percent", ascending=False
    )

    geography_rows = []
    for country, group in preferred.groupby("entity_country_std"):
        basic = group[group["balance_basic_plausible"]]
        pl = group[group["pl_valid"]]
        geography_rows.append(
            {
                "jurisdiction": country,
                "preferred_target_year_rows": len(group),
                "parent_groups": group["parent"].nunique(),
                "ready_rows": int(group["balance_ready"].sum()),
                "ready_rate_percent": pct(group["balance_ready"].sum(), len(group)),
                "basic_plausible_rows": len(basic),
                "negative_equity_rate_percent": pct(
                    basic["negative_equity"].sum(), len(basic)
                ),
                "pl_valid_rows": len(pl),
                "loss_rate_percent": pct(pl["loss_after_tax"].sum(), len(pl)),
                "median_roa": pl["roa_pat"].median(),
            }
        )
    financial_geography = pd.DataFrame(geography_rows).sort_values(
        "basic_plausible_rows", ascending=False
    )

    temporal = (
        preferred.groupby("fiscal_year", dropna=False)
        .agg(
            preferred_target_year_rows=("target_id", "size"),
            entities=("target_id", "nunique"),
            parent_groups=("parent", "nunique"),
            ready_rows=("balance_ready", "sum"),
            basic_plausible_rows=("balance_basic_plausible", "sum"),
            pl_valid_rows=("pl_valid", "sum"),
        )
        .reset_index()
    )
    temporal["ready_rate_percent"] = (
        100 * temporal["ready_rows"] / temporal["preferred_target_year_rows"]
    )
    # Identify parent dominance by year.
    year_parent = (
        preferred.groupby(["fiscal_year", "parent"], dropna=False)
        .size()
        .rename("n")
        .reset_index()
    )
    dominant_year = year_parent.sort_values("n", ascending=False).drop_duplicates(
        "fiscal_year"
    )
    temporal = temporal.merge(
        dominant_year.rename(
            columns={"parent": "dominant_parent", "n": "dominant_parent_rows"}
        ),
        on="fiscal_year",
        how="left",
    )
    temporal["dominant_parent_share_percent"] = (
        100
        * temporal["dominant_parent_rows"]
        / temporal["preferred_target_year_rows"]
    )

    # Linear probability specifications are descriptive, not causal. Clustered
    # standard errors are used when enough parent groups are present.
    model_rows: list[dict[str, Any]] = []

    def fit_model(
        name: str,
        data: pd.DataFrame,
        formula: str,
        coefficient: str,
        weight_column: str | None = None,
    ) -> None:
        model_data = data.copy()
        outcome = formula.split("~", 1)[0].strip()
        if pd.api.types.is_bool_dtype(model_data[outcome]):
            model_data[outcome] = model_data[outcome].astype(float)
        try:
            if weight_column:
                model = smf.wls(formula, data=model_data, weights=model_data[weight_column])
            else:
                model = smf.ols(formula, data=model_data)
            fitted = model.fit()
            n_groups = model_data["parent"].nunique() if "parent" in model_data else 0
            if n_groups >= 10:
                fitted = fitted.get_robustcov_results(
                    cov_type="cluster", groups=model_data["parent"]
                )
                names = list(model.exog_names)
                index = names.index(coefficient)
                coef_value = float(fitted.params[index])
                se_value = float(fitted.bse[index])
                p_value = float(fitted.pvalues[index])
            else:
                coef_value = float(fitted.params[coefficient])
                se_value = float(fitted.bse[coefficient])
                p_value = float(fitted.pvalues[coefficient])
            model_rows.append(
                {
                    "model": name,
                    "formula": formula,
                    "coefficient": coefficient,
                    "estimate": coef_value,
                    "standard_error": se_value,
                    "p_value": p_value,
                    "n": int(fitted.nobs),
                    "parent_groups": n_groups,
                    "r_squared": float(fitted.rsquared),
                    "interpretation": "linear probability/continuous descriptive association; not causal",
                }
            )
        except Exception as error:  # keep pipeline auditable even for sparse cells
            model_rows.append(
                {
                    "model": name,
                    "formula": formula,
                    "coefficient": coefficient,
                    "estimate": np.nan,
                    "standard_error": np.nan,
                    "p_value": np.nan,
                    "n": len(model_data),
                    "parent_groups": model_data["parent"].nunique(),
                    "r_squared": np.nan,
                    "interpretation": f"model failed: {type(error).__name__}: {error}",
                }
            )

    entity_financial["deep_2plus"] = entity_financial["level"].ge(2).astype(int)
    parent_entity_counts = entity_financial.groupby("parent")["target_id"].transform("size")
    entity_financial["equal_parent_weight"] = 1 / parent_entity_counts
    fit_model(
        "entity_any_ready_pooled",
        entity_financial,
        "any_ready ~ deep_2plus",
        "deep_2plus",
    )
    fit_model(
        "entity_any_ready_parent_fixed_effects",
        entity_financial,
        "any_ready ~ deep_2plus + C(parent)",
        "deep_2plus",
    )
    fit_model(
        "entity_any_ready_equal_parent_weight",
        entity_financial,
        "any_ready ~ deep_2plus",
        "deep_2plus",
        "equal_parent_weight",
    )

    basic = preferred[preferred["balance_basic_plausible"]].copy()
    basic["deep_2plus"] = basic["level"].ge(2).astype(int)
    if len(basic):
        fit_model(
            "negative_equity_pooled",
            basic,
            "negative_equity ~ deep_2plus",
            "deep_2plus",
        )
        fit_model(
            "negative_equity_parent_year_fixed_effects",
            basic,
            "negative_equity ~ deep_2plus + C(parent) + C(fiscal_year)",
            "deep_2plus",
        )
    pl = preferred[preferred["pl_valid"]].copy()
    pl["deep_2plus"] = pl["level"].ge(2).astype(int)
    if len(pl):
        fit_model(
            "loss_rate_pooled",
            pl,
            "loss_after_tax ~ deep_2plus",
            "deep_2plus",
        )
        fit_model(
            "loss_rate_parent_fixed_effects",
            pl,
            "loss_after_tax ~ deep_2plus + C(parent)",
            "deep_2plus",
        )
    financial_models = pd.DataFrame(model_rows)

    # Denominator/weighting sensitivity for headline rates.
    sensitivity_rows = []

    def weighted_rates(
        metric: str,
        sample: pd.DataFrame,
        value: str,
        eligible: str | None = None,
    ) -> None:
        work = sample[sample[eligible]] if eligible else sample.copy()
        pooled = work[value].mean()
        entity_means = work.groupby("target_id")[value].mean()
        entity_rate = entity_means.mean()
        parent_rates = work.groupby("parent")[value].mean()
        parent_rate = parent_rates.mean()
        sensitivity_rows.extend(
            [
                {
                    "metric": metric,
                    "weighting": "target-year pooled",
                    "estimate_percent": 100 * pooled,
                    "observations": len(work),
                    "units": work["target_id"].nunique(),
                    "parent_groups": work["parent"].nunique(),
                },
                {
                    "metric": metric,
                    "weighting": "entity mean",
                    "estimate_percent": 100 * entity_rate,
                    "observations": len(work),
                    "units": len(entity_means),
                    "parent_groups": work["parent"].nunique(),
                },
                {
                    "metric": metric,
                    "weighting": "equal parent mean",
                    "estimate_percent": 100 * parent_rate,
                    "observations": len(work),
                    "units": len(parent_rates),
                    "parent_groups": len(parent_rates),
                },
            ]
        )

    weighted_rates("ready_for_valuation", preferred, "balance_ready")
    weighted_rates(
        "negative_equity", preferred, "negative_equity", "balance_basic_plausible"
    )
    weighted_rates("loss_after_tax", preferred, "loss_after_tax", "pl_valid")
    weighting_sensitivity = pd.DataFrame(sensitivity_rows)

    loo_rows = []
    for omitted in sorted(preferred["parent"].unique()):
        retained = preferred[preferred["parent"] != omitted]
        for metric, eligible, value in [
            ("ready_for_valuation", pd.Series(True, index=retained.index), "balance_ready"),
            ("negative_equity", retained["balance_basic_plausible"], "negative_equity"),
            ("loss_after_tax", retained["pl_valid"], "loss_after_tax"),
        ]:
            sample = retained[eligible]
            loo_rows.append(
                {
                    "omitted_parent": omitted,
                    "metric": metric,
                    "numerator": int(sample[value].sum()),
                    "denominator": len(sample),
                    "estimate_percent": pct(sample[value].sum(), len(sample)),
                }
            )
    financial_loo = pd.DataFrame(loo_rows)

    return {
        "financial_sample_definitions": financial_samples,
        "financial_plausibility": financial_plausibility,
        "ownership_measure_comparison": ownership_comparison,
        "ownership_measure_comparison_summary": ownership_comparison_summary,
        "duplicate_financial_signatures": duplicate_signatures,
        "financial_anomalies_for_review": financial_anomalies,
        "financial_by_depth": depth_financial,
        "financial_by_reconstructed_depth": reconstructed_depth_financial,
        "entity_financial_coverage_by_depth": entity_coverage_depth,
        "parent_financial_coverage": parent_financial,
        "financial_by_jurisdiction": financial_geography,
        "temporal_coverage": temporal,
        "financial_models": financial_models,
        "financial_weighting_sensitivity": weighting_sensitivity,
        "financial_leave_one_parent_out": financial_loo,
        "entity_financial_summary": entity_financial,
    }


def structural_exploration_tables(
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    edges: pd.DataFrame,
    parent_table: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    level_distribution = (
        occurrences.groupby("level")
        .agg(
            target_occurrences=("target_id", "size"),
            group_entities=("group_entity_id", "nunique"),
            parent_groups=("parent", "nunique"),
            jurisdictions=("entity_country_std", "nunique"),
        )
        .reset_index()
    )
    level_distribution["target_share_percent"] = (
        100 * level_distribution["target_occurrences"] / len(occurrences)
    )

    uin_multiplicity = (
        occurrences.groupby("uin")
        .agg(
            target_occurrences=("target_id", "size"),
            group_entities=("group_entity_id", "nunique"),
            parent=("parent", "first"),
            jurisdictions=("entity_country_std", "nunique"),
            minimum_level=("level", "min"),
            maximum_level=("level", "max"),
            sectors=("sector_code", "nunique"),
        )
        .reset_index()
        .sort_values("target_occurrences", ascending=False)
    )

    stake_parent = (
        edges[edges["reported_level"] > 0]
        .groupby("parent")
        .agg(
            nonroot_edges=("child_target_id", "size"),
            missing_stake=("stake", lambda values: int(values.isna().sum())),
            zero_stake=("stake", lambda values: int(values.eq(0).sum())),
            minority_positive=(
                "stake",
                lambda values: int(values.between(0, 50, inclusive="right").sum()),
            ),
            majority_below_100=(
                "stake",
                lambda values: int(values.between(50, 100, inclusive="neither").sum()),
            ),
            full_100=("stake", lambda values: int(values.eq(100).sum())),
        )
        .reset_index()
    )
    stake_parent["zero_share_percent"] = (
        100 * stake_parent["zero_stake"] / stake_parent["nonroot_edges"]
    )

    sector_depth = pd.crosstab(occurrences["sector_code"], occurrences["depth_bin"])
    sector_depth = sector_depth.reindex(columns=DEPTH_LABELS, fill_value=0).reset_index()
    sector_depth["total"] = sector_depth[DEPTH_LABELS].sum(axis=1)
    sector_depth["level_5plus_share_percent"] = (
        100 * sector_depth["5+"] / sector_depth["total"]
    )
    sector_depth["level_3plus_share_percent"] = (
        100 * (sector_depth["3-4"] + sector_depth["5+"]) / sector_depth["total"]
    )

    # Leave-one-parent-out robustness for deep manufacturing concentration.
    sector_loo_rows = []
    for omitted in sorted(occurrences["parent"].unique()):
        retained = occurrences[occurrences["parent"] != omitted]
        for sector in sorted(retained["sector_code"].dropna().unique()):
            sample = retained[retained["sector_code"] == sector]
            sector_loo_rows.append(
                {
                    "omitted_parent": omitted,
                    "sector_code": sector,
                    "entities": len(sample),
                    "level_5plus": int(sample["level"].ge(5).sum()),
                    "level_5plus_share_percent": pct(
                        sample["level"].ge(5).sum(), len(sample)
                    ),
                }
            )
    sector_depth_loo = pd.DataFrame(sector_loo_rows)

    concentration = parent_table[
        ["parent", "normalized_group_entities", "pooled_entity_share_percent"]
    ].copy()
    concentration["cumulative_entity_share_percent"] = concentration[
        "pooled_entity_share_percent"
    ].cumsum()
    concentration["squared_share"] = np.square(
        concentration["pooled_entity_share_percent"] / 100
    )

    nonroot_edges = edges[edges["reported_level"] > 0]
    parent_deep_rates = occurrences.groupby("parent")["level"].apply(
        lambda values: values.ge(5).mean()
    )
    parent_cross_rates = nonroot_edges.groupby("parent")["cross_border_edge"].mean()
    structural_sensitivity = pd.DataFrame(
        [
            {
                "metric": "reported_level_5plus",
                "weighting": "pooled target occurrences",
                "numerator": int(occurrences["level"].ge(5).sum()),
                "denominator": len(occurrences),
                "estimate_percent": pct(occurrences["level"].ge(5).sum(), len(occurrences)),
            },
            {
                "metric": "reported_level_5plus",
                "weighting": "equal parent mean",
                "numerator": np.nan,
                "denominator": len(parent_deep_rates),
                "estimate_percent": 100 * parent_deep_rates.mean(),
            },
            {
                "metric": "nonroot_cross_border_edge",
                "weighting": "pooled edge occurrences",
                "numerator": int(nonroot_edges["cross_border_edge"].sum()),
                "denominator": len(nonroot_edges),
                "estimate_percent": pct(
                    nonroot_edges["cross_border_edge"].sum(), len(nonroot_edges)
                ),
            },
            {
                "metric": "nonroot_cross_border_edge",
                "weighting": "equal parent mean",
                "numerator": np.nan,
                "denominator": len(parent_cross_rates),
                "estimate_percent": 100 * parent_cross_rates.mean(),
            },
        ]
    )
    structural_loo_rows = []
    for omitted in sorted(occurrences["parent"].unique()):
        retained_occurrences = occurrences[occurrences["parent"] != omitted]
        retained_edges = nonroot_edges[nonroot_edges["parent"] != omitted]
        structural_loo_rows.extend(
            [
                {
                    "omitted_parent": omitted,
                    "metric": "reported_level_5plus",
                    "numerator": int(retained_occurrences["level"].ge(5).sum()),
                    "denominator": len(retained_occurrences),
                    "estimate_percent": pct(
                        retained_occurrences["level"].ge(5).sum(),
                        len(retained_occurrences),
                    ),
                },
                {
                    "omitted_parent": omitted,
                    "metric": "nonroot_cross_border_edge",
                    "numerator": int(retained_edges["cross_border_edge"].sum()),
                    "denominator": len(retained_edges),
                    "estimate_percent": pct(
                        retained_edges["cross_border_edge"].sum(), len(retained_edges)
                    ),
                },
            ]
        )
    structural_loo = pd.DataFrame(structural_loo_rows)
    return {
        "level_distribution": level_distribution,
        "uin_multiplicity": uin_multiplicity,
        "stake_by_parent": stake_parent,
        "sector_depth": sector_depth,
        "sector_depth_leave_one_parent_out": sector_depth_loo,
        "parent_size_concentration": concentration,
        "structural_weighting_sensitivity": structural_sensitivity,
        "structural_leave_one_parent_out": structural_loo,
    }


def make_figures(
    figures_dir: Path,
    parent_table: pd.DataFrame,
    parent_depth: pd.DataFrame,
    geography: dict[str, pd.DataFrame],
    finance: dict[str, pd.DataFrame],
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    # Structural landscape: size, depth, and jurisdictional breadth.
    fig, ax = plt.subplots(figsize=(12, 8))
    sizes = 40 + 16 * parent_table["effective_jurisdictions"]
    scatter = ax.scatter(
        parent_table["normalized_group_entities"],
        parent_table["maximum_reported_level"],
        s=sizes,
        c=parent_table["country_hhi"],
        cmap="viridis_r",
        alpha=0.82,
        edgecolor="black",
        linewidth=0.5,
    )
    short_names = {
        "SAMVARDHANA MOTHERSON INTERNATI": "Motherson",
        "HINDALCO INDUSTRIES LIMITED": "Hindalco",
        "WIPRO LTD": "Wipro",
        "TATA CHEMICALS LIMITED": "Tata Chemicals",
        "UPL LIMITED": "UPL",
        "JINDAL STEEL AND POWER LTD": "Jindal Steel",
        "BHARTI AIRTEL LIMITED": "Bharti Airtel",
        "RELIANCE INDUSTRIES LTD": "Reliance Industries",
        "TATA COMMUNICATIONS LIMITED": "Tata Communications",
    }
    label_parents = set(short_names)
    offsets = {
        "Motherson": (-70, 8),
        "Hindalco": (7, 8),
        "Wipro": (7, 8),
        "Tata Chemicals": (7, 8),
        "UPL": (-28, 9),
        "Jindal Steel": (8, 8),
        "Bharti Airtel": (8, -13),
        "Reliance Industries": (7, 8),
        "Tata Communications": (7, 8),
    }
    for row in parent_table.itertuples():
        if row.parent in label_parents:
            label = short_names[row.parent]
            ax.annotate(
                label,
                (row.normalized_group_entities, row.maximum_reported_level),
                xytext=offsets[label],
                textcoords="offset points",
                fontsize=9,
            )
    ax.set_xscale("log")
    ax.set_xlabel("Punctuation-normalized entities within parent (log scale)")
    ax.set_ylabel("Maximum reported ownership level")
    ax.set_xlim(7, 420)
    ax.set_title("Parent groups differ sharply in size and ownership depth")
    colorbar = fig.colorbar(scatter, ax=ax)
    colorbar.set_label("Jurisdiction HHI (higher = more concentrated)")
    fig.tight_layout()
    fig.savefig(figures_dir / "parent_structure_landscape.png", dpi=220)
    plt.close(fig)

    # Parent-by-depth composition heatmap.
    heat = parent_depth.set_index("parent")[[f"share_{x}_percent" for x in DEPTH_LABELS]]
    order = parent_table.sort_values(
        ["maximum_reported_level", "normalized_group_entities"], ascending=False
    )["parent"]
    heat = heat.reindex(order)
    heat.columns = DEPTH_LABELS
    fig, ax = plt.subplots(figsize=(10, 13))
    sns.heatmap(heat, cmap="mako", annot=True, fmt=".0f", cbar_kws={"label": "% of targets"}, ax=ax)
    ax.set_xlabel("Reported ownership level")
    ax.set_ylabel("")
    ax.set_title("Ownership-depth composition by ultimate parent")
    fig.tight_layout()
    fig.savefig(figures_dir / "parent_depth_heatmap.png", dpi=220)
    plt.close(fig)

    # Reported levels versus distances reconstructable from observed parent links.
    depth_compare = parent_table.sort_values(
        ["maximum_reported_level", "normalized_group_entities"], ascending=True
    )
    y_positions = np.arange(len(depth_compare))
    fig, ax = plt.subplots(figsize=(11, 13))
    for position, row in zip(y_positions, depth_compare.itertuples()):
        reconstructed = row.maximum_reconstructed_level_complete
        if pd.isna(reconstructed):
            continue
        ax.plot(
            [reconstructed, row.maximum_reported_level],
            [position, position],
            color="0.75",
            linewidth=2,
            zorder=1,
        )
    ax.scatter(
        depth_compare["maximum_reported_level"],
        y_positions,
        label="Maximum reported level",
        color="#4c72b0",
        s=55,
        zorder=2,
    )
    ax.scatter(
        depth_compare["maximum_reconstructed_level_complete"],
        y_positions,
        label="Maximum graph distance (complete paths)",
        color="#dd8452",
        s=55,
        zorder=3,
    )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(depth_compare["parent"], fontsize=9)
    ax.set_xlabel("Ownership level")
    ax.set_ylabel("")
    ax.set_title("Reported depth can exceed depth reconstructable from observed links")
    ax.legend(loc="lower right", fontsize=10)
    fig.tight_layout()
    fig.savefig(figures_dir / "reported_vs_reconstructed_parent_depth.png", dpi=220)
    plt.close(fig)

    # Denominator sensitivity for major jurisdictions.
    countries = geography["jurisdiction_counts"].head(15).copy()
    long = countries.melt(
        id_vars="jurisdiction",
        value_vars=[
            "pooled_group_entity_share_percent",
            "raw_row_share_percent",
            "equal_parent_mean_share_percent",
            "complete_path_ancestry_share_percent",
        ],
        var_name="denominator",
        value_name="share_percent",
    )
    labels = {
        "pooled_group_entity_share_percent": "Group-entity pooled",
        "raw_row_share_percent": "Raw source rows",
        "equal_parent_mean_share_percent": "Equal-parent mean",
        "complete_path_ancestry_share_percent": "Path ancestry appearances",
    }
    long["denominator"] = long["denominator"].map(labels)
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(
        data=long,
        x="jurisdiction",
        y="share_percent",
        hue="denominator",
        ax=ax,
    )
    ax.tick_params(axis="x", rotation=55, labelsize=9)
    ax.set_xlabel("")
    ax.set_ylabel("Share (%)")
    ax.set_title("Jurisdiction rankings depend on the counting denominator")
    ax.legend(title="", fontsize=9)
    fig.tight_layout()
    fig.savefig(figures_dir / "jurisdiction_denominator_sensitivity.png", dpi=220)
    plt.close(fig)

    # Transition matrix for the most common source/destination jurisdictions.
    transitions = geography["country_transitions"].copy()
    top_sources = (
        transitions.groupby("source_jurisdiction")["logical_edges"]
        .sum()
        .nlargest(12)
        .index
    )
    top_destinations = (
        transitions.groupby("destination_jurisdiction")["logical_edges"]
        .sum()
        .nlargest(12)
        .index
    )
    matrix = (
        transitions[
            transitions["source_jurisdiction"].isin(top_sources)
            & transitions["destination_jurisdiction"].isin(top_destinations)
        ]
        .pivot_table(
            index="source_jurisdiction",
            columns="destination_jurisdiction",
            values="logical_edges",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(index=top_sources, columns=top_destinations, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(13, 10))
    sns.heatmap(
        matrix,
        cmap="rocket_r",
        annot=True,
        fmt="g",
        linewidths=0.2,
        cbar_kws={"label": "Logical edges"},
        ax=ax,
    )
    ax.set_xlabel("Child jurisdiction")
    ax.set_ylabel("Immediate-parent jurisdiction")
    ax.set_title("Most frequent country-to-country ownership transitions")
    fig.tight_layout()
    fig.savefig(figures_dir / "country_transition_heatmap.png", dpi=220)
    plt.close(fig)

    # Panel versus entity-level financial coverage.
    coverage = finance["parent_financial_coverage"].sort_values(
        "entity_any_ready_rate_percent"
    )
    long = coverage.melt(
        id_vars="parent",
        value_vars=[
            "target_year_ready_rate_percent",
            "entity_any_ready_rate_percent",
        ],
        var_name="metric",
        value_name="percent",
    )
    long["metric"] = long["metric"].map(
        {
            "target_year_ready_rate_percent": "Target-year ready rate",
            "entity_any_ready_rate_percent": "Entities ever ready",
        }
    )
    fig, ax = plt.subplots(figsize=(12, 13))
    sns.barplot(data=long, y="parent", x="percent", hue="metric", ax=ax)
    ax.set_xlabel("Coverage (%)")
    ax.set_ylabel("")
    ax.set_title("Financial coverage is highly uneven across parent groups")
    ax.legend(title="", fontsize=10)
    fig.tight_layout()
    fig.savefig(figures_dir / "financial_coverage_by_parent.png", dpi=220)
    plt.close(fig)

    # Different financial outcomes by depth, with explicit distinct denominators.
    depth = finance["financial_by_depth"].copy()
    long = depth.melt(
        id_vars="depth_bin",
        value_vars=[
            "ready_rate_percent",
            "negative_equity_rate_percent",
            "loss_rate_percent",
        ],
        var_name="metric",
        value_name="percent",
    )
    long["metric"] = long["metric"].map(
        {
            "ready_rate_percent": "Ready / preferred target-years",
            "negative_equity_rate_percent": "Negative equity / basic-plausible",
            "loss_rate_percent": "Loss / P&L-valid",
        }
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=long, x="depth_bin", y="percent", hue="metric", ax=ax)
    ax.set_xlabel("Reported ownership level")
    ax.set_ylabel("Percent")
    ax.set_title("Financial patterns by depth use different audited denominators")
    ax.legend(title="", fontsize=9)
    fig.tight_layout()
    fig.savefig(figures_dir / "financial_patterns_by_depth.png", dpi=220)
    plt.close(fig)


def write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        frame.to_csv(path, index=False)


def write_outputs(
    output_dir: Path,
    df: pd.DataFrame,
    preferred: pd.DataFrame,
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    global_entities: pd.DataFrame,
    duplicate_clusters: pd.DataFrame,
    fuzzy_duplicates: pd.DataFrame,
    edges: pd.DataFrame,
    paths: pd.DataFrame,
    path_steps: pd.DataFrame,
    logical_edges: pd.DataFrame,
    multiple_parent_entities: pd.DataFrame,
    branch_hubs: pd.DataFrame,
    parent_table: pd.DataFrame,
    parent_jurisdiction: pd.DataFrame,
    parent_depth: pd.DataFrame,
    audits: dict[str, pd.DataFrame],
    geography: dict[str, pd.DataFrame],
    finance: dict[str, pd.DataFrame],
    structural: dict[str, pd.DataFrame],
) -> None:
    data_dir = output_dir / "data"
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    for directory in (data_dir, tables_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    core_data = {
        "entity_occurrences.csv": occurrences,
        "unique_entities_parent_scoped.csv": group_entities,
        "unique_entities_global.csv": global_entities,
        "parent_child_edge_occurrences.csv": edges,
        "parent_child_edges.csv": logical_edges,
        "ownership_paths.csv": paths,
        "ownership_path_steps.csv": path_steps,
        "parent_jurisdiction.csv": parent_jurisdiction,
        "ultimate_parent_analytical.csv": parent_table,
        "preferred_financial_panel.csv": preferred.drop(
            columns=EVIDENCE_COLUMNS, errors="ignore"
        ),
    }
    for filename, frame in core_data.items():
        write_table(frame, data_dir / filename)

    static_tables = {
        "entity_duplicate_clusters.csv": duplicate_clusters,
        "fuzzy_entity_duplicate_candidates.csv": fuzzy_duplicates,
        "entities_with_multiple_parent_nodes.csv": multiple_parent_entities,
        "branch_hubs.csv": branch_hubs,
        "ultimate_parent_analytical.csv": parent_table,
        "parent_jurisdiction.csv": parent_jurisdiction,
        "parent_depth_distribution.csv": parent_depth,
    }
    for filename, frame in {
        **static_tables,
        **{f"{name}.csv": frame for name, frame in audits.items()},
        **{f"{name}.csv": frame for name, frame in geography.items()},
        **{f"{name}.csv": frame for name, frame in finance.items()},
        **{f"{name}.csv": frame for name, frame in structural.items()},
    }.items():
        write_table(frame, tables_dir / filename)

    make_figures(figures_dir, parent_table, parent_depth, geography, finance)


def key_metrics(
    df: pd.DataFrame,
    preferred: pd.DataFrame,
    occurrences: pd.DataFrame,
    group_entities: pd.DataFrame,
    global_entities: pd.DataFrame,
    edges: pd.DataFrame,
    paths: pd.DataFrame,
    parent_table: pd.DataFrame,
    audits: dict[str, pd.DataFrame],
    geography: dict[str, pd.DataFrame],
    finance: dict[str, pd.DataFrame],
    structural: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    country = geography["jurisdiction_counts"].set_index("jurisdiction")
    fin_sens = finance["financial_weighting_sensitivity"].set_index(
        ["metric", "weighting"]
    )
    fin_loo = finance["financial_leave_one_parent_out"]
    manufacturing = structural["sector_depth"].set_index("sector_code").loc["MFG"]
    mfg_loo = structural["sector_depth_leave_one_parent_out"].query(
        "sector_code == 'MFG'"
    )
    structure_sensitivity = structural["structural_weighting_sensitivity"].set_index(
        ["metric", "weighting"]
    )
    structure_loo = structural["structural_leave_one_parent_out"]
    top4_share = parent_table.head(4)["pooled_entity_share_percent"].sum()
    max_uin = structural["uin_multiplicity"].iloc[0]
    nonroot = edges[edges["reported_level"] > 0]
    link_expected = nonroot["link_status"].isin(
        ["exact_expected_level", "normalized_expected_level", "fuzzy_expected_level"]
    )
    metrics: dict[str, Any] = {
        "counts": {
            "source_rows": len(df),
            "preferred_target_year_rows": len(preferred),
            "target_occurrences": len(occurrences),
            "parent_scoped_normalized_entities": len(group_entities),
            "global_normalized_entities": len(global_entities),
            "ultimate_parents": occurrences["parent"].nunique(),
            "uins": occurrences["uin"].nunique(),
            "complete_paths": int(paths["path_status"].eq("complete_to_ultimate_parent").sum()),
        },
        "hierarchy": {
            "max_reported_level": int(occurrences["level"].max()),
            "nonroot_edges": len(nonroot),
            "expected_level_links": int(link_expected.sum()),
            "expected_level_link_percent": pct(link_expected.sum(), len(nonroot)),
            "unobserved_parent_edges": int(nonroot["link_status"].eq("unobserved_parent").sum()),
            "complete_path_percent": pct(
                paths["path_status"].eq("complete_to_ultimate_parent").sum(), len(paths)
            ),
            "complete_paths_with_reported_depth_mismatch": int(
                paths["reported_level_matches_reconstruction"].eq(0).sum()
            ),
            "complete_depth_mismatch_percent": pct(
                paths["reported_level_matches_reconstruction"].eq(0).sum(),
                paths["path_status"].eq("complete_to_ultimate_parent").sum(),
            ),
            "zero_stake_nonroot": int(nonroot["stake"].eq(0).sum()),
            "zero_stake_nonroot_percent": pct(nonroot["stake"].eq(0).sum(), len(nonroot)),
            "reported_level5plus_pooled_percent": float(
                structure_sensitivity.loc[
                    ("reported_level_5plus", "pooled target occurrences"),
                    "estimate_percent",
                ]
            ),
            "reported_level5plus_equal_parent_percent": float(
                structure_sensitivity.loc[
                    ("reported_level_5plus", "equal parent mean"),
                    "estimate_percent",
                ]
            ),
            "reported_level5plus_loo_min_percent": float(
                structure_loo.query("metric == 'reported_level_5plus'")[
                    "estimate_percent"
                ].min()
            ),
            "reported_level5plus_loo_max_percent": float(
                structure_loo.query("metric == 'reported_level_5plus'")[
                    "estimate_percent"
                ].max()
            ),
            "nonroot_crossborder_pooled_percent": float(
                structure_sensitivity.loc[
                    ("nonroot_cross_border_edge", "pooled edge occurrences"),
                    "estimate_percent",
                ]
            ),
            "nonroot_crossborder_equal_parent_percent": float(
                structure_sensitivity.loc[
                    ("nonroot_cross_border_edge", "equal parent mean"),
                    "estimate_percent",
                ]
            ),
            "nonroot_crossborder_loo_min_percent": float(
                structure_loo.query("metric == 'nonroot_cross_border_edge'")[
                    "estimate_percent"
                ].min()
            ),
            "nonroot_crossborder_loo_max_percent": float(
                structure_loo.query("metric == 'nonroot_cross_border_edge'")[
                    "estimate_percent"
                ].max()
            ),
        },
        "duplication": {
            "global_repeated_clusters": int(
                (global_entities["target_occurrences"] > 1).sum()
            ),
            "cross_parent_repeated_clusters": int(
                global_entities["repeated_across_parent_groups"].sum()
            ),
            "within_parent_repeated_entities": int(
                group_entities["repeated_within_parent"].sum()
            ),
            "target_year_keys_with_multiple_sources": len(
                audits["duplicate_target_years"]
            ),
        },
        "parent_concentration": {
            "top4_entity_share_percent": float(top4_share),
            "parent_entity_hhi": float(
                np.square(parent_table["pooled_entity_share_percent"] / 100).sum()
            ),
            "largest_parent": parent_table.iloc[0]["parent"],
            "largest_parent_entities": int(
                parent_table.iloc[0]["normalized_group_entities"]
            ),
        },
        "uin": {
            "largest_uin": max_uin["uin"],
            "largest_uin_target_occurrences": int(max_uin["target_occurrences"]),
            "median_entities_per_uin": float(
                structural["uin_multiplicity"]["group_entities"].median()
            ),
        },
        "geography": {},
        "financial": {
            "balance_ready_rows": int(preferred["balance_ready"].sum()),
            "balance_ready_percent": pct(preferred["balance_ready"].sum(), len(preferred)),
            "basic_plausible_rows": int(preferred["balance_basic_plausible"].sum()),
            "pl_valid_rows": int(preferred["pl_valid"].sum()),
            "entities_with_any_ready": int(
                preferred.groupby("target_id")["balance_ready"].max().sum()
            ),
            "entities_with_any_ready_percent": pct(
                preferred.groupby("target_id")["balance_ready"].max().sum(),
                preferred["target_id"].nunique(),
            ),
            "ready_rows_failing_basic_sign_plausibility": int(
                preferred["balance_ready"].sum()
                - preferred["balance_basic_plausible"].sum()
            ),
            "ready_pooled_percent": float(
                fin_sens.loc[("ready_for_valuation", "target-year pooled"), "estimate_percent"]
            ),
            "ready_entity_percent": float(
                fin_sens.loc[("ready_for_valuation", "entity mean"), "estimate_percent"]
            ),
            "ready_equal_parent_percent": float(
                fin_sens.loc[("ready_for_valuation", "equal parent mean"), "estimate_percent"]
            ),
            "negative_equity_pooled_percent": float(
                fin_sens.loc[("negative_equity", "target-year pooled"), "estimate_percent"]
            ),
            "negative_equity_equal_parent_percent": float(
                fin_sens.loc[("negative_equity", "equal parent mean"), "estimate_percent"]
            ),
            "loss_pooled_percent": float(
                fin_sens.loc[("loss_after_tax", "target-year pooled"), "estimate_percent"]
            ),
            "loss_equal_parent_percent": float(
                fin_sens.loc[("loss_after_tax", "equal parent mean"), "estimate_percent"]
            ),
            "ready_loo_min_percent": float(
                fin_loo.query("metric == 'ready_for_valuation'")["estimate_percent"].min()
            ),
            "ready_loo_max_percent": float(
                fin_loo.query("metric == 'ready_for_valuation'")["estimate_percent"].max()
            ),
            "ownership_rows_both_measures": int(
                (
                    preferred["stake"].notna()
                    & preferred["shareholding_percent"].notna()
                ).sum()
            ),
            "zero_stake_positive_shareholding_rows": int(
                (
                    preferred["stake"].eq(0)
                    & preferred["shareholding_percent"].gt(0)
                ).sum()
            ),
        },
        "dates": {
            "blank_fiscal_year_preferred": int(preferred["fiscal_year"].isna().sum()),
            "blank_period_end_preferred": int(preferred["period_end_date"].isna().sum()),
            "date_fiscal_year_comparable": int(
                preferred["period_date_within_fiscal_window"].notna().sum()
            ),
            "period_end_outside_fiscal_window": int(
                preferred["period_date_within_fiscal_window"].eq(0).sum()
            ),
        },
        "foreign_domestic_labels": {
            str(row.jurisdiction_category): int(row.target_occurrences)
            for row in geography["foreign_domestic_summary"].itertuples()
        },
        "sector": {
            "manufacturing_entities": int(manufacturing["total"]),
            "manufacturing_level5plus_percent": float(
                manufacturing["level_5plus_share_percent"]
            ),
            "manufacturing_level5plus_loo_min_percent": float(
                mfg_loo["level_5plus_share_percent"].min()
            ),
            "manufacturing_level5plus_loo_max_percent": float(
                mfg_loo["level_5plus_share_percent"].max()
            ),
        },
    }
    for name in [
        "UNITED STATES OF AMERICA",
        "NETHERLANDS",
        "MAURITIUS",
        "UNITED KINGDOM",
    ]:
        if name in country.index:
            metrics["geography"][name] = {
                key: float(country.loc[name, key])
                for key in [
                    "normalized_group_entities",
                    "pooled_group_entity_share_percent",
                    "global_unique_entities",
                    "raw_row_share_percent",
                    "equal_parent_mean_share_percent",
                    "complete_path_ancestry_share_percent",
                    "equal_parent_ancestry_share_percent",
                    "leave_one_parent_out_min_share_percent",
                    "leave_one_parent_out_max_share_percent",
                ]
            }
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.is_file() or not args.dictionary.is_file():
        raise FileNotFoundError("Input Stata file or dictionary not found")

    df, variable_labels = read_input(args.input)
    occurrences, invariance = prepare_occurrences(df)
    group_entities, global_entities, duplicate_clusters = aggregate_entities(
        occurrences
    )
    fuzzy_duplicates = fuzzy_duplicate_candidates(occurrences)
    edges = build_edges(occurrences)
    paths, path_steps = build_paths(occurrences, edges)
    logical_edges, multiple_parent_entities, branch_hubs, leaf_nodes = graph_tables(
        occurrences, group_entities, edges
    )
    preferred = add_financial_fields(df, occurrences, paths)
    audits = audit_tables(
        df,
        preferred,
        occurrences,
        group_entities,
        global_entities,
        invariance,
        edges,
        paths,
    )
    parent_table, parent_jurisdiction, parent_depth = parent_analytics(
        df,
        preferred,
        occurrences,
        group_entities,
        edges,
        paths,
        logical_edges,
        leaf_nodes,
    )
    geography = geography_tables(
        df,
        occurrences,
        group_entities,
        global_entities,
        edges,
        paths,
        path_steps,
        logical_edges,
        leaf_nodes,
    )
    finance = financial_tables(df, preferred, occurrences)
    structural = structural_exploration_tables(
        occurrences, group_entities, edges, parent_table
    )
    write_outputs(
        args.output,
        df,
        preferred,
        occurrences,
        group_entities,
        global_entities,
        duplicate_clusters,
        fuzzy_duplicates,
        edges,
        paths,
        path_steps,
        logical_edges,
        multiple_parent_entities,
        branch_hubs,
        parent_table,
        parent_jurisdiction,
        parent_depth,
        audits,
        geography,
        finance,
        structural,
    )

    metrics = key_metrics(
        df,
        preferred,
        occurrences,
        group_entities,
        global_entities,
        edges,
        paths,
        parent_table,
        audits,
        geography,
        finance,
        structural,
    )
    manifest = {
        "pipeline": str(Path(__file__).resolve().relative_to(ROOT)),
        "python": sys.version,
        "pandas": pd.__version__,
        "networkx": nx.__version__,
        "input_path": str(args.input),
        "input_sha256": sha256_file(args.input),
        "dictionary_path": str(args.dictionary),
        "dictionary_sha256": sha256_file(args.dictionary),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "variable_count": len(df.columns),
        "variable_labels": variable_labels,
        "metrics": metrics,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (args.output / "key_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
