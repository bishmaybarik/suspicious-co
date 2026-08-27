"""Produce the figures for Claude's blind-discovery increment.

Each figure corresponds to one candidate finding in research/claude/FINDINGS.md
and is saved as a 200-dpi PNG in outputs/claude/figures/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import derived_path, fig_path

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 200, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "-",
    "axes.axisbelow": True, "figure.facecolor": "white",
})

ink = "#1f2933"
accent = "#c0392b"
muted = "#7f8c8d"

df_entity = pd.read_parquet(derived_path / "entity_enriched.parquet")
df_parent = pd.read_parquet(derived_path / "parent.parquet")


def save(fig, name):
    """Write a figure to the claude figures directory and close it."""

    # tight bounding box keeps the panels usable inside a paper draft
    fig.savefig(fig_path / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


# GOAL: FIGURE 1 - HOW FAR THE STRUCTURE RUNS BEYOND THE REGISTERED INVESTMENT

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.6))

s_level = df_entity.level.value_counts().sort_index()
ax1.bar(s_level.index, s_level.values, color=ink, width=0.7)
ax1.set_xlabel("ownership level below the Indian parent")
ax1.set_ylabel("foreign entities")
ax1.set_title("a. nearly half sit two or more layers below the parent", loc="left", fontsize=9)
ax1.annotate(
    f"{round(100 * (df_entity.level >= 2).mean())}% at level 2 or deeper",
    xy=(4, 400), color=accent, fontsize=8.5,
)

s_uin = df_entity.groupby("uin").size().sort_values(ascending=False)
ax2.plot(range(1, len(s_uin) + 1), s_uin.cumsum() / s_uin.sum() * 100, color=ink, lw=1.8)
ax2.axhline(50, color=muted, lw=0.8, ls="--")
ax2.set_xlabel("registered outward investments (UINs), ranked")
ax2.set_ylabel("cumulative % of foreign entities")
ax2.set_title("b. 10 of 186 registrations carry half the network", loc="left", fontsize=9)
ax2.annotate("10 UINs", xy=(10, 49.2), xytext=(35, 35), color=accent, fontsize=8.5,
             arrowprops=dict(arrowstyle="->", color=accent, lw=0.8))
save(fig, "fig01_depth_and_uin_concentration")


# GOAL: FIGURE 2 - GATEWAY AMPLIFICATION BY FIRST-HOP JURISDICTION

df_gate = df_entity[df_entity.level == 0]
df_amp = df_gate.groupby("entity_country").agg(
    n=("target_id", "size"), total=("n_descendants", "sum"),
    med=("n_descendants", "median")).reset_index()
df_amp = df_amp[df_amp.n >= 3].copy()
df_amp["per_gateway"] = df_amp.total / df_amp.n
df_amp = df_amp.sort_values("per_gateway")

fig, ax = plt.subplots(figsize=(7.2, 5.2))
y = np.arange(len(df_amp))
ax.barh(y, df_amp.per_gateway, color=[accent if v > 12 else ink for v in df_amp.per_gateway], height=0.62)
ax.scatter(df_amp.med, y, color="white", edgecolor=ink, zorder=3, s=22, linewidth=0.9)
ax.set_yticks(y)
ax.set_yticklabels([f"{c.title()} (n={n})" for c, n in zip(df_amp.entity_country, df_amp.n)])
ax.set_xlabel("downstream entities per directly held foreign entity")
ax.set_title("Where the first foreign hop lands decides how much structure follows\n"
             "bars = mean descendants per gateway; dots = median", loc="left", fontsize=9.5)
save(fig, "fig02_gateway_amplification")


# GOAL: FIGURE 3 - WHERE EACH JURISDICTION SITS IN THE CHAIN

df_role = df_entity.groupby("entity_country").agg(
    n=("target_id", "size"), mean_level=("level", "mean"),
    pct_nonleaf=("is_leaf", lambda s: 100 * (1 - s.mean()))).reset_index()
df_role = df_role[df_role.n >= 15].sort_values("mean_level")

# the depth profile of a jurisdiction is its position in the chain, in full
df_entity["level_bin"] = pd.cut(df_entity.level, [-1, 0, 1, 2, 4, 20],
                                labels=["level 0", "level 1", "level 2", "level 3-4", "level 5+"])
df_prof = pd.crosstab(df_entity.entity_country, df_entity.level_bin, normalize="index") * 100
df_prof = df_prof.loc[df_role.entity_country]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True,
                               gridspec_kw={"width_ratios": [2.4, 1]})
shade_list = ["#0f2233", "#33566e", "#7794a8", "#b3c4cf", "#e2e8ec"]
left = np.zeros(len(df_prof))
y = np.arange(len(df_prof))
for col, shade in zip(df_prof.columns, shade_list):
    ax1.barh(y, df_prof[col], left=left, color=shade, height=0.7, label=str(col))
    left = left + df_prof[col].values
ax1.set_yticks(y)
ax1.set_yticklabels([f"{c.title()} ({n})" for c, n in zip(df_role.entity_country, df_role.n)], fontsize=8)
ax1.set_xlabel("% of the jurisdiction's entities at each ownership level")
ax1.set_xlim(0, 100)
ax1.legend(frameon=False, fontsize=7.5, ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.16))
ax1.grid(False)
ax1.set_title("a. position in the chain", loc="left", fontsize=9)

ax2.barh(y, df_role.pct_nonleaf, color=[accent if v >= 35 else ink for v in df_role.pct_nonleaf], height=0.7)
ax2.set_xlabel("% holding at least one subsidiary")
ax2.set_title("b. pass-through rate", loc="left", fontsize=9)

fig.suptitle("Singapore, Mauritius and Cyprus enter the chain early and pass ownership on;\n"
             "China, France and Mexico appear only at the bottom and terminate it",
             x=0.02, ha="left", fontsize=10)
save(fig, "fig03_jurisdiction_roles")


# GOAL: FIGURE 4 - BREADTH AND DEPTH ARE DIFFERENT CHOICES

fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.scatter(df_parent.n_entities, df_parent.max_depth, s=46, color=ink, alpha=0.55)
# groups sharing a max depth would overprint, so stagger labels within a depth
df_label = df_parent[(df_parent.n_entities > 70) | (df_parent.max_depth >= 6)].copy()
df_label["rank_in_depth"] = df_label.groupby("max_depth").n_entities.rank(method="first")
for row in df_label.itertuples():
    on_right = row.rank_in_depth % 2 == 1
    ax.annotate(row.parent.title()[:26], (row.n_entities, row.max_depth),
                fontsize=7.5, color=ink,
                xytext=(7, 3) if on_right else (-7, -11),
                textcoords="offset points",
                ha="left" if on_right else "right")
ax.set_xscale("log")
ax.set_xlim(7, 900)
ax.set_xlabel("foreign entities recorded for the group (log scale)")
ax.set_ylabel("deepest ownership level observed")
ax.set_title("Comparable footprints, opposite architectures:\n"
             "Reliance is wide and flat, Hindalco is narrow and twelve layers deep",
             loc="left", fontsize=9.5)
save(fig, "fig04_breadth_vs_depth")


# GOAL: FIGURE 5 - CONDUIT EXPOSURE VARIES ENORMOUSLY ACROSS GROUPS

df_exp = df_entity.groupby("parent").agg(
    n=("target_id", "size"),
    pct=("reached_through_centre", lambda s: 100 * s.mean())).reset_index()
df_exp = df_exp.sort_values("pct")

fig, ax = plt.subplots(figsize=(7.2, 6.2))
y = np.arange(len(df_exp))
ax.barh(y, df_exp.pct, color=ink, height=0.65)
ax.axvline(100 * df_entity.reached_through_centre.mean(), color=accent, lw=1.2, ls="--")
ax.set_yticks(y)
ax.set_yticklabels([f"{p.title()[:30]} ({n})" for p, n in zip(df_exp.parent, df_exp.n)], fontsize=7.5)
ax.set_xlabel("% of the group's foreign entities held through a financial-centre jurisdiction")
ax.set_title("Reliance reaches 11% of its foreign entities through a financial centre;\n"
             "Jindal Steel & Power reaches 97%", loc="left", fontsize=9.5)
ax.annotate(f"all-entity mean {round(100 * df_entity.reached_through_centre.mean(), 1)}%",
            xy=(100 * df_entity.reached_through_centre.mean(), 1.5),
            xytext=(6, 0), textcoords="offset points", color=accent, fontsize=8)

# Reliance's low share is partly a denominator effect, so say so on the figure
ax.annotate("Reliance's 11% is partly a denominator effect: 109 of its 196 entities are\n"
            "venture-fund portfolio companies held directly in the US. Excluding them, 25.3%.",
            xy=(0.0, -0.115), xycoords="axes fraction", fontsize=7.5, color=muted)
save(fig, "fig05_conduit_exposure_by_parent")


# GOAL: FIGURE 6 - THE FIRST-HOP JURISDICTION MIX SHIFTS ACROSS VINTAGES

df_gate = df_gate.copy()
df_gate["vintage"] = pd.cut(df_gate.uin_year, [1988, 2010, 2015, 2020, 2026],
                            labels=["<=2010", "2011-15", "2016-20", "2021-25"])
show_list = ["MAURITIUS", "SINGAPORE", "NETHERLANDS", "IFSC GIFT CITY"]
df_share = pd.crosstab(df_gate.vintage, df_gate.entity_country, normalize="index") * 100

fig, ax = plt.subplots(figsize=(7.0, 4.2))
for country, colour in zip(show_list, [accent, "#2c7fb8", "#31a354", "#e08214"]):
    if country in df_share.columns:
        ax.plot(range(len(df_share)), df_share[country], marker="o", label=country.title(),
                color=colour, lw=1.8, ms=5)
ax.set_xticks(range(len(df_share)))
s_bin_n = df_gate.vintage.value_counts().sort_index()
ax.set_xticklabels([f"{v}\n(n={s_bin_n[v]})" for v in df_share.index])
ax.set_xlabel("registration vintage of the outward investment (decoded from the UIN)")
ax.set_ylabel("% of new first-hop entities")
ax.legend(frameon=False, fontsize=8)
ax.set_title("Mauritius fades, Singapore and GIFT City arrive\n"
             "shares of the 184 directly held foreign entities, by registration vintage",
             loc="left", fontsize=9.5)
save(fig, "fig06_gateway_vintage_shift")


# GOAL: FIGURE 7 - A FEW NODES CARRY ALMOST ALL OF THE OWNERSHIP EDGES

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.4),
                               gridspec_kw={"width_ratios": [1, 1.5], "wspace": 0.62})

s_child = df_entity.n_children.value_counts().sort_index()
s_plot = s_child[s_child.index <= 10]
ax1.bar(s_plot.index, s_plot.values, color=ink, width=0.7)
ax1.set_yscale("log")
ax1.set_xlabel("directly held subsidiaries")
ax1.set_ylabel("entities (log scale)")
frac_one = 100 * (df_entity[df_entity.n_children > 0].n_children == 1).mean()
ax1.set_title(f"a. 78% hold nothing; of the 404 that do,\n{frac_one:.0f}% hold exactly one entity",
              loc="left", fontsize=9)

df_hub = df_entity.nlargest(12, "n_children").sort_values("n_children")
y = np.arange(len(df_hub))
ax2.barh(y, df_hub.n_children, color=ink, height=0.66)
ax2.set_yticks(y)
# the two Breakthrough vehicles are venture funds, so mark them explicitly
ax2.set_yticklabels(
    [f"{n.title()[:34]} [{c.title()[:11]}]" + (" *" if "BREAKTHROUGH" in n.upper() else "")
     for n, c in zip(df_hub.entity_name, df_hub.entity_country)],
    fontsize=7.5)
ax2.annotate("* venture-fund vehicles: their 'subsidiaries' are portfolio\n"
             "  companies held at stakes near zero, not controlled entities",
             xy=(0.02, -0.30), xycoords="axes fraction", fontsize=7.5, color=muted)
ax2.set_xlabel("directly held subsidiaries")
share_top20 = 100 * df_entity.nlargest(20, "n_children").n_children.sum() / df_entity.n_children.sum()
ax2.set_title(f"b. the 20 largest holding nodes carry {share_top20:.0f}% of all ownership links",
              loc="left", fontsize=9)
save(fig, "fig07_branching_concentration")


# GOAL: FIGURE 8 - COVERAGE OF THE FINANCIAL LAYER

df_cov = df_entity.groupby("level").agg(
    n=("target_id", "size"),
    src=("any_source_found", "mean"),
    ready=("any_ready_for_valuation", "mean")).reset_index()

fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.bar(df_cov.level - 0.2, 100 * df_cov.src, width=0.4, color=muted, label="any source located")
ax.bar(df_cov.level + 0.2, 100 * df_cov.ready, width=0.4, color=accent, label="valuation-ready")
ax.set_xticks(df_cov.level)
ax.set_xlabel("ownership level")
ax.set_ylabel("% of entities at that level")
ax.legend(frameon=False, fontsize=8)
ax.set_title("Only 14.4% of the 1,834 foreign entities ever yield a usable balance sheet\n"
             "(the level gradient is a between-group composition effect, not a depth effect)",
             loc="left", fontsize=9.5)
save(fig, "fig08_coverage_by_level")

print("figures written to", fig_path)
