import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.lines import Line2D

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
TEAL, PINK, CONNECTOR = ("#0E8B7E", "#E0577F", "#C9C9C9")
INK, MUTED = ("#222222", "#6B6B6B")
TITLE_FS, SUBTITLE_FS, LABEL_FS, TICK_FS, LEGEND_FS, COLUMN_FS = (
    21,
    15,
    18,
    17,
    17,
    16,
)
COLUMN_X = {"change": 1.1, "journals": 1.51, "n": 1.71}
SHORT_LABELS = {
    "Multidisciplinary Digital Publishing Institute (MDPI)": "MDPI",
    "American Association for the Advancement of Science": "AAAS",
}
BASELINE_LABEL = "2019–2022"
COMPARISON_LABEL = "2026 (partial year)"


def short_label(name, width=56):
    name = SHORT_LABELS.get(name, name)
    return name if len(name) <= width else name[: width - 1].rstrip() + "…"


def draw(data, path):
    style()
    publishers = data.sort_values(["pct_baseline", "change_pp"]).reset_index(drop=True)
    y = range(len(publishers))
    sns.set_theme(style="ticks", context="paper")
    plt.rcParams.update({"font.family": FONT_FAMILY, "figure.dpi": 150})
    fig, ax = plt.subplots(figsize=(12.4, max(4.5, 0.42 * len(publishers))))
    fig.subplots_adjust(left=0.24, right=0.77, top=0.76)
    ax.hlines(
        y,
        publishers["pct_baseline"],
        publishers["pct_comparison"],
        color=CONNECTOR,
        lw=3.8,
        zorder=1,
    )
    for column, colour in (("baseline", TEAL), ("comparison", PINK)):
        centre = publishers[f"pct_{column}"]
        xerr_lo = (centre - publishers[f"pct_{column}_lo"]).clip(lower=0)
        xerr_hi = (publishers[f"pct_{column}_hi"] - centre).clip(lower=0)
        ax.errorbar(
            centre,
            y,
            xerr=[xerr_lo, xerr_hi],
            fmt="none",
            ecolor=colour,
            elinewidth=2.8,
            capsize=4.5,
            capthick=2.8,
            alpha=0.9,
            zorder=2,
        )
        ax.scatter(
            centre, y, s=170, color=colour, zorder=3, edgecolor="white", linewidth=1.3
        )
    upper = max(
        publishers["pct_baseline_hi"].max(), publishers["pct_comparison_hi"].max()
    )
    ax.set_yticks(list(y))
    ax.set_yticklabels(
        [short_label(name) for name in publishers["publisher"]], fontsize=TICK_FS
    )
    ax.set_ylim(len(publishers) - 0.4, -0.6)
    ax.set_xlim(-1, upper * 1.02)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.tick_params(axis="x", labelsize=TICK_FS)
    ax.set_xlabel("Abstracts containing an em dash (%)", fontsize=LABEL_FS, labelpad=8)
    ax.grid(axis="x", color="#D8D8D8", lw=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    text_kw = {
        "xycoords": ("axes fraction", "data"),
        "annotation_clip": False,
        "fontsize": COLUMN_FS,
        "va": "center",
    }
    for key, header, align in (
        ("change", "Change, pp (95% CI)", "left"),
        ("journals", "Journals", "center"),
        ("n", "n (base, 2026)", "center"),
    ):
        ax.annotate(
            header,
            xy=(COLUMN_X[key], -0.78),
            ha=align,
            va="bottom",
            fontweight="bold",
            color=INK,
            linespacing=1.4,
            **{k: v for k, v in text_kw.items() if k != "va"},
        )
    for row, publisher in publishers.iterrows():
        ax.annotate(
            f"{publisher['change_pp']:+.2f} ({publisher['change_pp_lo']:+.2f}, {publisher['change_pp_hi']:+.2f})",
            xy=(COLUMN_X["change"], row),
            ha="left",
            color=INK,
            **text_kw,
        )
        ax.annotate(
            f"{publisher['n_journals']:.0f}",
            xy=(COLUMN_X["journals"], row),
            ha="center",
            color=INK,
            **text_kw,
        )
        ax.annotate(
            f"{publisher['n_baseline']:.0f}, {publisher['n_comparison']:.0f}",
            xy=(COLUMN_X["n"], row),
            ha="center",
            color=INK,
            **text_kw,
        )
    handles = [
        Line2D(
            [],
            [],
            marker="o",
            ls="none",
            color=TEAL,
            ms=10,
            mec="white",
            label=f"{BASELINE_LABEL} baseline",
        ),
        Line2D(
            [],
            [],
            marker="o",
            ls="none",
            color=PINK,
            ms=10,
            mec="white",
            label=COMPARISON_LABEL,
        ),
        Line2D([], [], color=MUTED, lw=1.5, label="95% Wilson interval"),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0, 1.04),
        frameon=False,
        fontsize=LEGEND_FS,
        handlelength=1.4,
        borderaxespad=0.3,
        labelspacing=0.3,
    )
    sns.despine(ax=ax, left=True)
    ax.tick_params(axis="y", length=0)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
