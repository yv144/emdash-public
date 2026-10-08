import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.lines import Line2D

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
TEAL, PINK, CONNECTOR = ("#0E8B7E", "#E0577F", "#C9C9C9")
INK, MUTED = ("#222222", "#6B6B6B")
TITLE_FS, LABEL_FS, TICK_FS, LEGEND_FS, COLUMN_FS = (19, 16, 15, 15, 14)
HEADER_FS = 12
COLUMN_X = {"change": 1.03, "journals": 1.245}
SHORT_LABELS = {
    "Biochemistry, Genetics and Molecular Biology": "Biochemistry, Genetics & Mol. Biology"
}


def short_label(area):
    return SHORT_LABELS.get(area, area).replace(" and ", " & ")


def draw(data, path):
    style()
    areas = data.sort_values("pct_baseline").reset_index(drop=True)
    y = range(len(areas))
    sns.set_theme(style="ticks", context="paper")
    plt.rcParams.update({"font.family": FONT_FAMILY, "figure.dpi": 150})
    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    ax.hlines(
        y,
        areas["pct_baseline"],
        areas["pct_comparison"],
        color=CONNECTOR,
        lw=3.8,
        zorder=1,
    )
    for column, colour in (("baseline", TEAL), ("comparison", PINK)):
        centre = areas[f"pct_{column}"]
        ax.errorbar(
            centre,
            y,
            xerr=[
                centre - areas[f"pct_{column}_lo"],
                areas[f"pct_{column}_hi"] - centre,
            ],
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
    upper = max(areas["pct_baseline_hi"].max(), areas["pct_comparison_hi"].max())
    ax.set_yticks(list(y))
    ax.set_yticklabels([short_label(area) for area in areas["area"]], fontsize=TICK_FS)
    ax.set_ylim(len(areas) - 0.4, -0.6)
    ax.set_xlim(0, upper * 1.02)
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
    for key, header, align, offset in (
        ("change", "Change, pp (95% CI)", "left", 0.0),
        ("journals", "Journals", "center", 0.03),
    ):
        ax.annotate(
            header,
            xy=(COLUMN_X[key] + offset, -0.78),
            ha=align,
            va="bottom",
            fontweight="bold",
            color=INK,
            fontsize=HEADER_FS,
            **{k: v for k, v in text_kw.items() if k not in {"va", "fontsize"}},
        )
    for row, area in areas.iterrows():
        ax.annotate(
            f"{area['change_pp']:+.2f} ({area['change_pp_lo']:+.2f}, {area['change_pp_hi']:+.2f})",
            xy=(COLUMN_X["change"], row),
            ha="left",
            color=INK,
            **text_kw,
        )
        ax.annotate(
            f"{area['n_journals']:.0f}",
            xy=(COLUMN_X["journals"] + 0.03, row),
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
            label="2019–2022 baseline",
        ),
        Line2D(
            [],
            [],
            marker="o",
            ls="none",
            color=PINK,
            ms=10,
            mec="white",
            label="2026 (partial year)",
        ),
        Line2D([], [], color=MUTED, lw=1.5, label="95% Wilson interval"),
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=False,
        fontsize=LEGEND_FS,
        handlelength=1.6,
        borderaxespad=1.0,
        labelspacing=0.5,
    )
    sns.despine(ax=ax, left=True)
    ax.tick_params(axis="y", length=0)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
