"""Canonical entity, edge, and ownership-path construction.

The source file is a panel of candidate financial-statement sources.  This
module collapses it to structural target occurrences, constructs conservative
name-country entity candidates, resolves reported parent links, and preserves
named-but-unscraped parents as country-labelled unresolved nodes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .config import COUNTRY_FIXES


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


@dataclass(frozen=True)
class AnalysisData:
    raw: pd.DataFrame
    preferred: pd.DataFrame
    occurrences: pd.DataFrame
    group_entities: pd.DataFrame
    global_entities: pd.DataFrame
    edges: pd.DataFrame
    logical_edges: pd.DataFrame
    paths: pd.DataFrame
    path_steps: pd.DataFrame
    structural_invariance: pd.DataFrame


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
    """Punctuation/spacing-insensitive key that retains legal suffixes."""

    text = ascii_text(value).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", text)


def strip_country_suffix_key(name: Any, country: Any) -> str:
    """Linkage-only alias that removes a literal trailing country phrase."""

    name_tokens = re.findall(r"[a-z0-9]+", ascii_text(name).replace("&", " and "))
    country_tokens = re.findall(
        r"[a-z0-9]+", ascii_text(country).replace("&", " and ")
    )
    if country_tokens and name_tokens[-len(country_tokens) :] == country_tokens:
        name_tokens = name_tokens[: -len(country_tokens)]
    return "".join(name_tokens)


def normalize_country(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA
    text = re.sub(r"\s+", " ", str(value).strip().upper())
    return COUNTRY_FIXES.get(text, text)


def join_unique(values: Iterable[Any]) -> str:
    return " | ".join(
        sorted({str(value) for value in values if not pd.isna(value)})
    )


def list_unique_int(values: Iterable[Any]) -> str:
    return " | ".join(map(str, sorted({int(v) for v in values if not pd.isna(v)})))


def read_input(path: Path) -> pd.DataFrame:
    frame = pd.read_stata(path, convert_categoricals=False)
    for column in frame.select_dtypes(include="object").columns:
        frame[column] = frame[column].replace(r"^\s*$", pd.NA, regex=True)
    return frame


def prepare_occurrences(
    raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    audit_rows: list[dict[str, Any]] = []
    for column in STRUCTURAL_COLUMNS:
        counts = raw.groupby("target_id", dropna=False)[column].nunique(
            dropna=False
        )
        audit_rows.append(
            {
                "variable": column,
                "targets_with_conflict": int(counts.gt(1).sum()),
                "maximum_distinct_values_within_target": int(counts.max()),
            }
        )
    invariance = pd.DataFrame(audit_rows)
    if invariance["targets_with_conflict"].sum() != 0:
        raise ValueError("structural fields vary within target_id")

    occurrence = raw.drop_duplicates("target_id", keep="first").copy()
    occurrence["entity_country_std"] = occurrence["entity_country"].map(
        normalize_country
    )
    occurrence["immediate_parent_country_std"] = occurrence[
        "immediate_parent_country"
    ].map(normalize_country)
    occurrence["entity_name_key"] = occurrence["entity_name"].map(light_name_key)
    occurrence["entity_link_alias"] = occurrence.apply(
        lambda row: strip_country_suffix_key(
            row["entity_name"], row["entity_country"]
        ),
        axis=1,
    )
    occurrence["immediate_parent_name_key"] = occurrence[
        "immediate_parent"
    ].map(light_name_key)
    occurrence["immediate_parent_link_alias"] = occurrence.apply(
        lambda row: strip_country_suffix_key(
            row["immediate_parent"], row["immediate_parent_country"]
        ),
        axis=1,
    )
    occurrence["parent_name_key"] = occurrence["parent"].map(light_name_key)
    occurrence["global_entity_id"] = occurrence.apply(
        lambda row: stable_id(
            "ge", row["entity_country_std"], row["entity_name_key"]
        ),
        axis=1,
    )
    occurrence["group_entity_id"] = occurrence.apply(
        lambda row: stable_id(
            "pe",
            row["parent"],
            row["entity_country_std"],
            row["entity_name_key"],
        ),
        axis=1,
    )
    return occurrence, invariance


def aggregate_entities(
    occurrence: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_entities = (
        occurrence.groupby("group_entity_id", dropna=False)
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
            immediate_parent_countries=(
                "immediate_parent_country_std",
                join_unique,
            ),
            uins=("uin", join_unique),
            n_uins=("uin", "nunique"),
            global_entity_id=("global_entity_id", "first"),
            n_immediate_parents=("immediate_parent_name_key", "nunique"),
            n_reported_levels=("level", "nunique"),
        )
        .reset_index()
    )
    group_entities["multiple_paths_or_versions"] = (
        group_entities["n_immediate_parents"].gt(1)
        | group_entities["n_reported_levels"].gt(1)
    )

    global_entities = (
        occurrence.groupby("global_entity_id", dropna=False)
        .agg(
            canonical_entity_name=("entity_name", "first"),
            entity_name_aliases=("entity_name", join_unique),
            entity_country=("entity_country_std", "first"),
            target_occurrences=("target_id", "size"),
            parent_count=("parent", "nunique"),
            parents=("parent", join_unique),
            group_entity_count=("group_entity_id", "nunique"),
            uins=("uin", join_unique),
            n_uins=("uin", "nunique"),
        )
        .reset_index()
    )
    return group_entities, global_entities


def build_edges(occurrence: pd.DataFrame) -> pd.DataFrame:
    """Resolve each reported immediate-parent relation conservatively."""

    records = occurrence.set_index("target_id", drop=False).to_dict("index")
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
        ambiguity_count = 0

        if root_match:
            status = (
                "ultimate_parent_root"
                if child["level"] == 0
                else "root_level_mismatch"
            )
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
                return (
                    int(candidate["level"] == child["level"] - 1),
                    int(
                        candidate["entity_country_std"]
                        == child["immediate_parent_country_std"]
                    ),
                    int(candidate["entity_name"] == child["immediate_parent"]),
                    int(candidate["uin"] == child["uin"]),
                )

            if candidate_ids:
                scored = [(candidate_score(cid), cid) for cid in candidate_ids]
                best_score = max(score for score, _ in scored)
                best_ids = sorted(cid for score, cid in scored if score == best_score)
                ambiguity_count = len(best_ids)
                if len(best_ids) == 1:
                    chosen_id = best_ids[0]
                    expected, country_match, exact, _ = best_score
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
            else:
                status = "unobserved_parent"

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
    occurrence: pd.DataFrame, edges: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    occurrence_records = occurrence.set_index("target_id", drop=False).to_dict(
        "index"
    )
    edge_records = edges.set_index("child_target_id", drop=False).to_dict("index")
    paths: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []

    for target_id in occurrence["target_id"]:
        chain: list[dict[str, Any]] = []
        seen: set[str] = set()
        current_id: str | None = target_id
        status = ""

        while current_id is not None:
            if current_id in seen:
                status = "cycle_detected"
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
                status = "complete_to_ultimate_parent"
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
            status = (
                "truncated_ambiguous_parent"
                if edge["parent_node_type"] == "ambiguous_entity"
                else "truncated_unobserved_parent"
            )
            break

        ordered = list(reversed(chain))
        observed_count = sum(
            step["node_kind"] == "observed_entity" for step in ordered
        )
        reconstructed_level = (
            observed_count - 1
            if status == "complete_to_ultimate_parent"
            else np.nan
        )
        current = occurrence_records[target_id]
        paths.append(
            {
                "target_id": target_id,
                "parent": current["parent"],
                "group_entity_id": current["group_entity_id"],
                "global_entity_id": current["global_entity_id"],
                "entity_name": current["entity_name"],
                "entity_country": current["entity_country_std"],
                "reported_level": current["level"],
                "path_status": status,
                "observed_entities_in_path": observed_count,
                "reconstructed_level": reconstructed_level,
                "reported_level_matches_reconstruction": (
                    int(reconstructed_level == current["level"])
                    if not pd.isna(reconstructed_level)
                    else pd.NA
                ),
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
            steps.append(
                {
                    "terminal_target_id": target_id,
                    "parent": current["parent"],
                    "path_status": status,
                    "step_from_upstream": position,
                    "step_from_terminal": len(ordered) - position - 1,
                    **step,
                }
            )
    return pd.DataFrame(paths), pd.DataFrame(steps)


def build_logical_edges(edges: pd.DataFrame) -> pd.DataFrame:
    logical = (
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
        )
        .reset_index()
    )
    logical["logical_edge_id"] = logical.apply(
        lambda row: stable_id(
            "ledge",
            row["parent"],
            row["parent_node_id"],
            row["child_group_entity_id"],
        ),
        axis=1,
    )
    return logical


def build_analysis_data(path: Path) -> AnalysisData:
    raw = read_input(path)
    preferred = raw[raw["preferred_for_target_year"].eq(1)].copy()
    occurrence, invariance = prepare_occurrences(raw)
    group_entities, global_entities = aggregate_entities(occurrence)
    edges = build_edges(occurrence)
    paths, path_steps = build_paths(occurrence, edges)
    logical_edges = build_logical_edges(edges)
    return AnalysisData(
        raw=raw,
        preferred=preferred,
        occurrences=occurrence,
        group_entities=group_entities,
        global_entities=global_entities,
        edges=edges,
        logical_edges=logical_edges,
        paths=paths,
        path_steps=path_steps,
        structural_invariance=invariance,
    )
