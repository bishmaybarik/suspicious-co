"""Figures for increment 2: chokepoints, criticality and name morphology."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import derived_path, fig_path, tab_path

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
df_choke = pd.read_csv(tab_path / "chokepoint_single_node.csv")
df_crit = pd.read_csv(tab_path / "jurisdiction_criticality.csv")
df_cover = pd.read_csv(tab_path / "jurisdiction_greedy_cover.csv")


def save(fig, name):
    """Write a figure to the claude figures directory and close it."""

    fig.savefig(fig_path / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


# GOAL: FIGURE 9 - HOW MUCH OF EACH GROUP HANGS BELOW ONE FOREIGN ENTITY

df_plot = df_choke.sort_values("pct_below_one_node")
centre_list = ["MAURITIUS", "NETHERLANDS", "SINGAPORE", "SWITZERLAND", "CYPRUS",
               "CHANNEL ISLAND", "JERSEY", "LUXEMBOURG"]
colour_list = [accent if c in centre_list else ink for c in df_plot.chokepoint_country]

fig, ax = plt.subplots(figsize=(8.6, 6.4))
y = np.arange(len(df_plot))
ax.barh(y, df_plot.pct_below_one_node, color=colour_list, height=0.66)
ax.set_yticks(y)
ax.set_yticklabels(
    [f"{p.title()[:28]} ({n})" for p, n in zip(df_plot.parent, df_plot.n_entities)],
    fontsize=7.5)
ax.set_xlabel("% of the group's foreign network sitting below its single largest node")
ax.axvline(df_plot.pct_below_one_node.median(), color=muted, lw=1, ls="--")
ax.annotate(f"median {df_plot.pct_below_one_node.median():.0f}%",
            xy=(df_plot.pct_below_one_node.median(), len(df_plot) - 0.2),
            xytext=(4, 0), textcoords="offset points", color=muted, fontsize=8)

# name the chokepoint entity beside each bar so the claim is inspectable
for i, row in enumerate(df_plot.itertuples()):
    ax.annotate(f"{row.chokepoint_entity.title()[:34]} [{row.chokepoint_country.title()[:11]}]",
                xy=(row.pct_below_one_node, i), xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=6.4, color=muted)
ax.set_xlim(0, 150)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_title("Half of all large Indian groups route more than 43% of their foreign\n"
             "network through a single company; ten route more than 60%\n"
             "red = that company sits in a holding jurisdiction; groups with 15+ entities",
             loc="left", fontsize=9.5)
save(fig, "fig09_single_node_chokepoints")


# GOAL: FIGURE 10 - JURISDICTIONAL CRITICALITY AND THE GREEDY COVER

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6),
                               gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.3})

df_top = df_crit.nlargest(12, "n_entities_below").sort_values("pct_of_all_entities")
y = np.arange(len(df_top))
ax1.barh(y, df_top.pct_of_all_entities, color=ink, height=0.62, label="pooled")
ax1.scatter(df_top.equal_parent_pct, y, color="white", edgecolor=accent, zorder=3,
            s=30, linewidth=1.2, label="equal-parent")

# leave-one-out bars show how far any single group can move the estimate
ax1.hlines(y, df_top.loo_min_pct, df_top.loo_max_pct, color=muted, lw=1.4, zorder=2)
ax1.set_yticks(y)
ax1.set_yticklabels(
    [f"{c.title()[:22]} ({n}p)" for c, n in zip(df_top.jurisdiction, df_top.n_parents_affected)],
    fontsize=8)
ax1.set_xlabel("% of all 1,834 foreign entities held *below* this jurisdiction")
ax1.legend(frameon=False, fontsize=7.5, loc="lower right")
ax1.set_title("a. how much of the network each jurisdiction sits above\n"
              "grey line = leave-one-parent-out range; (Np) = parents affected",
              loc="left", fontsize=9)

df_all = df_cover[df_cover["sample"] == "all entities"]
df_ctl = df_cover[df_cover["sample"] == "excluding venture-fund portfolios"]
ax2.plot(df_all.step, df_all.cumulative_pct, marker="o", color=ink, lw=1.8, ms=5,
         label="all entities")
ax2.plot(df_ctl.step, df_ctl.cumulative_pct, marker="s", color=accent, lw=1.5, ms=4,
         ls="--", label="excluding fund portfolios")
for row in df_all.itertuples():
    ax2.annotate(row.jurisdiction.title()[:14], (row.step, row.cumulative_pct),
                 xytext=(4, -10), textcoords="offset points", fontsize=7, color=muted)
ax2.set_xlabel("jurisdictions removed, in greedy order")
ax2.set_ylabel("% of entities detached from their Indian parent")
ax2.set_ylim(0, 100)
ax2.legend(frameon=False, fontsize=7.5, loc="lower right")
ax2.set_title("b. three jurisdictions sit above 61% of the network", loc="left", fontsize=9)
save(fig, "fig10_jurisdiction_criticality")


# GOAL: FIGURE 11 - CORPORATE NAMES PREDICT NETWORK ROLE

df_token = pd.read_csv(tab_path / "name_tokens_vs_role.csv")
df_form = pd.read_csv(tab_path / "legal_form_vs_role.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                               gridspec_kw={"wspace": 0.42})

df_t = df_token[df_token.n_entities >= 12].sort_values("pct_holding_at_least_one")
y = np.arange(len(df_t))
base = 100 * (1 - df_entity.is_leaf.mean())
ax1.barh(y, df_t.pct_holding_at_least_one,
         color=[muted if t.startswith("(none") else ink for t in df_t.name_token], height=0.64)
ax1.axvline(base, color=accent, lw=1.2, ls="--")
ax1.set_yticks(y)
ax1.set_yticklabels([f"{t} ({n})" for t, n in zip(df_t.name_token, df_t.n_entities)],
                    fontsize=8)
ax1.set_xlabel("% of entities that hold at least one subsidiary")
ax1.annotate(f"all entities {base:.0f}%", xy=(base, 0.3), xytext=(4, 0),
             textcoords="offset points", color=accent, fontsize=7.5)
ax1.set_title("a. words in the name", loc="left", fontsize=9)

df_f = df_form.sort_values("pct_holding_at_least_one")
y2 = np.arange(len(df_f))
ax2.barh(y2, df_f.pct_holding_at_least_one, color=ink, height=0.64)
ax2.axvline(base, color=accent, lw=1.2, ls="--")
ax2.set_yticks(y2)
ax2.set_yticklabels([f"{t} ({n})" for t, n in zip(df_f.legal_form, df_f.n_entities)],
                    fontsize=8)
ax2.set_xlabel("% of entities that hold at least one subsidiary")
ax2.set_title("b. legal form suffix", loc="left", fontsize=9)

fig.suptitle("A company's name predicts its position in the ownership chain\n"
             "the holding-name gap is 23pp even within parent-by-country cells",
             x=0.02, y=1.12, ha="left", va="top", fontsize=10)
save(fig, "fig11_name_predicts_role")


# GOAL: FIGURE 12 - LAYERING DOES NOT DILUTE OWNERSHIP

df_cum = pd.read_csv(tab_path / "cumulative_ownership_by_level.csv")
df_comp = pd.read_csv(tab_path / "cumulative_ownership_completion.csv")
df_cum = df_cum[df_cum.n >= 15]

fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.bar(df_cum.level - 0.2, df_cum["median"], width=0.4, color=ink, label="median")
ax.bar(df_cum.level + 0.2, df_cum["mean"], width=0.4, color=accent, label="mean")
ax.set_xticks(df_cum.level)
ax.set_xlabel("ownership level below the Indian parent")
ax.set_ylabel("cumulative ownership below the first foreign entity (%)")
ax.set_ylim(0, 118)
ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper right")

# the completion rate is the selection caveat and belongs on the figure
for row in df_cum.itertuples():
    n_at_level = int(df_comp.loc[df_comp.level == row.level, "n_entities"].iloc[0])
    ax.annotate(f"{row.n}/{n_at_level}", xy=(row.level, 2), ha="center",
                fontsize=6.8, color="white")
ax.set_title("Layers below the first foreign hop are wholly owned, not partially owned\n"
             "labels = entities with a complete positive-stake chain / entities at that level",
             loc="left", fontsize=9.5)
save(fig, "fig12_no_ownership_dilution")

print("increment-2 figures written to", fig_path)
