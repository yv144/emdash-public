import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
TEAL, PINK = ("#0E8B7E", "#E0577F")
PARTIAL_YEAR, SPLIT_YEAR = (2026, 2023)
LABEL_FS, TICK_FS, LEGEND_FS, ANNOT_FS = (15, 13, 13, 12)


def draw(data, path):
    style()
    sns.set_theme(style="ticks", context="paper")
    plt.rcParams.update({"font.family": FONT_FAMILY, "figure.dpi": 150})
    d = data.rename(columns={"pct_em": "pct"}).sort_values("year")
    y0, y1 = (int(d["year"].min()), int(d["year"].max()))
    max_pct = d["pct"].max()
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    colors = [PINK if yr >= SPLIT_YEAR else TEAL for yr in d["year"]]
    bars = ax.bar(d["year"], d["pct"], color=colors, width=0.68, zorder=3)
    bars[-1].set_hatch("////")
    bars[-1].set_edgecolor("white")
    bars[-1].set_alpha(0.75)
    for bar, pct in zip(bars, d["pct"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max_pct * 0.02,
            f"{pct:.2f}%",
            ha="center",
            va="bottom",
            fontsize=ANNOT_FS,
            color="#333333",
        )
    handles = [
        mpatches.Patch(color=TEAL, label="Before ChatGPT release"),
        mpatches.Patch(color=PINK, label="After ChatGPT release"),
        mpatches.Patch(
            facecolor=PINK,
            hatch="////",
            edgecolor="white",
            alpha=0.75,
            label=f"{PARTIAL_YEAR} (partial year)",
        ),
    ]
    ax.legend(
        handles=handles,
        fontsize=LEGEND_FS,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0, 0.9),
    )
    ax.set_xlabel("Year", labelpad=8, fontsize=LABEL_FS)
    ax.set_ylabel("Abstracts containing em dash (%)", labelpad=8, fontsize=LABEL_FS)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.tick_params(labelsize=TICK_FS)
    ax.set_xticks(range(y0, y1 + 1))
    ax.set_ylim(0, max_pct * 1.28)
    sns.despine(ax=ax, trim=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
