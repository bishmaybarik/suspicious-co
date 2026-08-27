"""Publication figures generated only from canonical analytical tables."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/suspicious-co-matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import COUNTRY_SHORT
from .statistics import FinalResults


DARK = "#24313d"
BLUE = "#356a9a"
ORANGE = "#d36b35"
RED = "#b73c32"
TEAL = "#3e8c87"
GREY = "#89949a"
LIGHT = "#d9dfe2"


def set_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 220,
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.labelsize": 9.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#d6dadd",
            "grid.linewidth": 0.6,
            "grid.alpha": 0.75,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def save(fig: plt.Figure, directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fig.savefig(directory / f"{name}.png", bbox_inches="tight")
    fig.savefig(directory / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_denominators(results: FinalResults, directory: Path) -> None:
    sample = results.tables["01_sample_construction"].set_index("stage")
    stages = [
        "Raw source rows",
        "Preferred target-year rows",
        "Structural target occurrences",
        "Parent-scoped normalized entity candidates",
        "Global normalized entity candidates",
        "UINs",
        "Ultimate-parent buckets",
    ]
    labels = [
        "Raw source rows",
        "Preferred target-years",
        "Target occurrences",
        "Parent-scoped entities",
        "Global entities",
        "UINs",
        "Parent buckets",
    ]
    values = sample.loc[stages, "count"].astype(float).to_numpy()
    depth = results.tables["07_depth_distribution"]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2), gridspec_kw={"wspace": 0.32})
    y = np.arange(len(values))[::-1]
    axes[0].barh(y, values, color=[GREY, GREY, BLUE, BLUE, TEAL, ORANGE, DARK])
    axes[0].set_yticks(y, labels)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Count (log scale)")
    axes[0].set_title("a. The source panel contains several distinct units", loc="left")
    for pos, value in zip(y, values):
        axes[0].text(value * 1.08, pos, f"{int(value):,}", va="center", fontsize=8.5)
    axes[0].set_xlim(15, 6500)

    x = depth["level"].to_numpy()
    width = 0.38
    axes[1].bar(
        x - width / 2,
        depth["reported_target_occurrences"],
        width,
        color=BLUE,
        label="Reported level (all targets)",
    )
    axes[1].bar(
        x + width / 2,
        depth["reconstructed_complete_paths"],
        width,
        color=ORANGE,
        label="Graph distance (complete paths)",
    )
    axes[1].set_xlabel("Ownership level/distance")
    axes[1].set_ylabel("Target paths")
    axes[1].set_xticks(range(0, 13, 2))
    axes[1].set_title("b. Reported depth is not observed graph distance", loc="left")
    axes[1].legend(loc="upper right", fontsize=8)
    fig.suptitle("Analytical denominators and hierarchy depth", fontsize=13, y=1.02)
    save(fig, directory, "figure_01_denominators_and_depth")


def figure_parent_architecture(results: FinalResults, directory: Path) -> None:
    frame = results.plot_data["parent_architecture"].copy()
    fig, ax = plt.subplots(figsize=(8.5, 5.7))
    sizes = 25 + 1.8 * frame["modal_uin_target_pct"]
    scatter = ax.scatter(
        frame["normalized_entities"],
        frame["jurisdictions"],
        s=sizes,
        c=frame["maximum_reported_level"],
        cmap="viridis",
        edgecolor="white",
        linewidth=0.8,
        alpha=0.9,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Parent-scoped normalized entity candidates (log scale)")
    ax.set_ylabel("Jurisdiction labels represented")
    ax.set_title("Parent groups combine size, geographic breadth, and depth differently")
    labels = set(frame.nlargest(7, "normalized_entities")["parent_short"]) | {
        "Hindalco",
        "Tata Communications",
        "ONGC Videsh",
    }
    label_positions = {
        "Bharti Airtel": (-5, 5, "right"),
        "Hindalco": (7, 11, "left"),
        "Jindal Steel & Power": (-5, -9, "right"),
        "Motherson": (-5, 5, "right"),
        "Reliance Industries": (-8, -11, "right"),
        "Wipro": (-5, 5, "right"),
    }
    for row in frame[frame["parent_short"].isin(labels)].itertuples(index=False):
        x_offset, y_offset, alignment = label_positions.get(
            row.parent_short, (5, 5, "left")
        )
        ax.annotate(
            row.parent_short,
            (row.normalized_entities, row.jurisdictions),
            xytext=(x_offset, y_offset),
            textcoords="offset points",
            ha=alignment,
            fontsize=8,
        )
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Maximum reported level")
    ax.text(
        0.01,
        -0.17,
        "Marker area increases with the within-parent modal-UIN share.",
        transform=ax.transAxes,
        fontsize=8.5,
        color=DARK,
    )
    save(fig, directory, "figure_02_parent_architecture")


def figure_channel_concentration(results: FinalResults, directory: Path) -> None:
    frame = results.plot_data["channel_concentration"].sort_values(
        "largest_observed_subtree_entity_pct"
    )
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(9.3, 8.0))
    for pos, row in zip(y, frame.itertuples(index=False)):
        ax.plot(
            [row.strict_dag_dominator_entity_pct, row.named_node_inclusive_subtree_pct],
            [pos, pos],
            color=LIGHT,
            linewidth=2.2,
            zorder=1,
        )
    ax.scatter(
        frame["strict_dag_dominator_entity_pct"],
        y,
        marker="x",
        color=GREY,
        s=30,
        label="Strict DAG dominator",
        zorder=3,
    )
    ax.scatter(
        frame["largest_observed_subtree_entity_pct"],
        y,
        marker="s",
        color=BLUE,
        s=34,
        label="Largest observed subtree",
        zorder=4,
    )
    ax.scatter(
        frame["named_node_inclusive_subtree_pct"],
        y,
        marker="^",
        color=ORANGE,
        s=40,
        label="Including named missing nodes",
        zorder=4,
    )
    ax.scatter(
        frame["modal_uin_target_pct"],
        y,
        facecolor="none",
        edgecolor=RED,
        linewidth=1.2,
        s=43,
        label="Modal UIN channel",
        zorder=5,
    )
    ax.set_yticks(y, frame["parent_short"])
    ax.set_xlim(0, 105)
    ax.set_xlabel("Share of the parent network (%)")
    ax.set_title(
        "Dominant channels are common, but their magnitude depends on graph definition"
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8)
    ax.grid(axis="y", visible=False)
    save(fig, directory, "figure_03_channel_concentration")


def figure_gateway_amplification(results: FinalResults, directory: Path) -> None:
    points = results.plot_data["gateway_points"].copy()
    summary = results.plot_data["gateway_summary"].copy()
    focus = summary[summary["gateways"].ge(5)].sort_values(
        "median_descendants", ascending=True
    )
    countries = list(focus["gateway_country"])
    points = points[points["gateway_country"].isin(countries)]
    rng = np.random.default_rng(20260827)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for index, country in enumerate(countries):
        group = points[points["gateway_country"].eq(country)]
        jitter = rng.normal(0, 0.065, size=len(group))
        ax.scatter(
            group["descendants"],
            index + jitter,
            s=26,
            alpha=0.62,
            color=BLUE,
            edgecolor="white",
            linewidth=0.4,
        )
        median = focus.loc[
            focus["gateway_country"].eq(country), "median_descendants"
        ].iloc[0]
        ax.scatter(median, index, marker="D", s=55, color=RED, zorder=5)
    labels = [COUNTRY_SHORT.get(country, country.title()) for country in countries]
    ns = [int(focus.loc[focus["gateway_country"].eq(c), "gateways"].iloc[0]) for c in countries]
    ax.set_yticks(range(len(countries)), [f"{label} (n={n})" for label, n in zip(labels, ns)])
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xticks([0, 1, 5, 10, 25, 50, 100])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("Downstream normalized entities per observed level-0 gateway")
    ax.set_title("First-hop jurisdictions differ in downstream amplification")
    ax.scatter([], [], color=BLUE, s=26, label="One gateway")
    ax.scatter([], [], color=RED, marker="D", s=55, label="Jurisdiction median")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", visible=False)
    save(fig, directory, "figure_04_gateway_amplification")


def figure_jurisdiction_roles(results: FinalResults, directory: Path) -> None:
    frame = results.plot_data["jurisdiction_roles"].copy()
    frame = frame[
        frame["resident_entities"].gt(0) & frame["target_paths_below"].gt(0)
    ]
    fig, ax = plt.subplots(figsize=(8.0, 6.0))
    size = 20 + 8 * frame["parents_affected"]
    color = frame["unique_intermediary_pct"] / frame["resident_entity_pct"]
    scatter = ax.scatter(
        frame["resident_entities"],
        frame["target_paths_below"],
        s=size,
        c=color.clip(upper=5),
        cmap="magma_r",
        alpha=0.8,
        edgecolor="white",
        linewidth=0.6,
    )
    lower = max(1, min(frame["resident_entities"].min(), frame["target_paths_below"].min()))
    upper = max(frame["resident_entities"].max(), frame["target_paths_below"].max())
    ax.plot([lower, upper], [lower, upper], color=GREY, linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Resident parent-scoped entities (log scale)")
    ax.set_ylabel("Target paths with jurisdiction strictly upstream (log scale)")
    ax.set_title("Resident prevalence and downstream network reach are distinct")
    focus = set(frame.nlargest(10, "target_paths_below")["jurisdiction"]) | {
        "UNITED STATES OF AMERICA",
        "NETHERLANDS",
        "MAURITIUS",
        "SINGAPORE",
    }
    for row in frame[frame["jurisdiction"].isin(focus)].itertuples(index=False):
        align_right = row.resident_entities >= 200
        ax.annotate(
            COUNTRY_SHORT.get(row.jurisdiction, row.jurisdiction.title()),
            (row.resident_entities, row.target_paths_below),
            xytext=(-4 if align_right else 4, 3),
            textcoords="offset points",
            ha="right" if align_right else "left",
            fontsize=7.8,
        )
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Intermediary share / resident share (capped at 5)")
    save(fig, directory, "figure_05_jurisdiction_roles")


def figure_depth_by_parent(results: FinalResults, directory: Path) -> None:
    frame = results.plot_data["parent_architecture"].copy()
    frame = frame.sort_values("maximum_reported_level")
    y = np.arange(len(frame))
    fig, ax = plt.subplots(figsize=(8.5, 8.0))
    for pos, row in zip(y, frame.itertuples(index=False)):
        graph_value = row.maximum_reconstructed_level_complete
        ax.plot(
            [graph_value, row.maximum_reported_level],
            [pos, pos],
            color=LIGHT,
            linewidth=2,
            zorder=1,
        )
    ax.scatter(
        frame["maximum_reported_level"],
        y,
        color=BLUE,
        s=30,
        label="Maximum reported level",
        zorder=3,
    )
    ax.scatter(
        frame["maximum_reconstructed_level_complete"],
        y,
        color=ORANGE,
        s=30,
        label="Maximum graph distance, complete paths",
        zorder=3,
    )
    ax.set_yticks(y, frame["parent_short"])
    ax.set_xlabel("Maximum ownership level/distance")
    ax.set_xlim(0, 12.6)
    ax.set_title("Reported depth and reconstructable graph distance diverge")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="y", visible=False)
    save(fig, directory, "figure_06_reported_vs_graph_depth")


def figure_financial_attrition(results: FinalResults, directory: Path) -> None:
    sample = results.tables["01_sample_construction"].set_index("stage")
    target_stages = [
        "Structural target occurrences",
        "Targets with any located source",
        "Targets with parsed balance sheet",
        "Targets valuation-ready at least once",
    ]
    row_stages = [
        "Ready target-year rows",
        "Sign-plausible ready rows",
        "P&L-valid rows",
        "Ready rows unflagged by broad duplicate/sign screen",
    ]
    target_labels = ["All targets", "Source found", "Balance parsed", "Ready at least once"]
    row_labels = ["Ready rows", "Sign plausible", "P&L valid", "Broad screen unflagged"]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"wspace": 0.32})
    for ax, stages, labels, title, color in [
        (axes[0], target_stages, target_labels, "a. Target-level coverage", BLUE),
        (axes[1], row_stages, row_labels, "b. Ready-row quality screens", ORANGE),
    ]:
        values = sample.loc[stages, "count"].astype(int).to_numpy()
        positions = np.arange(len(values))[::-1]
        ax.barh(positions, values, color=color, alpha=0.9)
        ax.set_yticks(positions, labels)
        ax.set_title(title, loc="left")
        ax.set_xlabel("Count")
        for pos, value in zip(positions, values):
            ax.text(value + max(values) * 0.02, pos, f"{value:,}", va="center", fontsize=8.5)
        ax.set_xlim(0, max(values) * 1.23)
        ax.grid(axis="y", visible=False)
    fig.suptitle("Financial coverage is sparse and quality-selected", fontsize=13, y=1.02)
    save(fig, directory, "figure_07_financial_attrition")


def figure_robustness(results: FinalResults, directory: Path) -> None:
    frame = results.plot_data["robustness"].set_index("estimand")
    focus = [
        "Cross-border nonroot edges",
        "Modal UIN channel",
        "Netherlands strictly upstream",
        "Netherlands + US + Mauritius upstream",
        "Reported depth 5+",
        "Declared-centre upstream exposure",
    ]
    work = frame.loc[focus].iloc[::-1]
    y = np.arange(len(work))
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for pos, row in zip(y, work.itertuples(index=False)):
        if not pd.isna(row.loo_min):
            ax.plot([row.loo_min, row.loo_max], [pos, pos], color=GREY, linewidth=2)
    ax.scatter(
        work["pooled_or_primary"], y, color=BLUE, s=42, label="Pooled/primary", zorder=4
    )
    ax.scatter(
        work["equal_parent_or_fe"], y, color=ORANGE, marker="s", s=38, label="Equal-parent", zorder=4
    )
    alt = work["alternative"].notna()
    ax.scatter(
        work.loc[alt, "alternative"], y[alt], color=RED, marker="^", s=42, label="Alternative definition", zorder=4
    )
    ax.set_yticks(y, work.index)
    ax.set_xlabel("Percent")
    ax.set_title("Pooled estimates, parent balance, and definition sensitivity")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
    ax.grid(axis="y", visible=False)
    save(fig, directory, "figure_08_robustness_ladder")


def make_figures(results: FinalResults, directory: Path) -> None:
    set_style()
    figure_denominators(results, directory)
    figure_parent_architecture(results, directory)
    figure_channel_concentration(results, directory)
    figure_gateway_amplification(results, directory)
    figure_jurisdiction_roles(results, directory)
    figure_depth_by_parent(results, directory)
    figure_financial_attrition(results, directory)
    figure_robustness(results, directory)
