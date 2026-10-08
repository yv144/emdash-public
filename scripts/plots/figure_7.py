import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
PANELS = [
    ("em", "Em dash (—)"),
    ("en_numeric", "En dash between digits (–)"),
    ("en_nonnumeric", "En dash outside digits (–)"),
    ("curly_apostrophe", "Curly apostrophe (’)"),
    ("curly_quote", "Curly quotation mark (“)"),
    ("semicolon", "Semicolon (;)"),
    ("degree_sign", "Degree sign (°)"),
    ("times_sign", "Multiplication sign (×)"),
    ("greek_alpha", "Greek alpha (α)"),
]


def draw(data, path):
    style()
    plt.rcdefaults()
    q = (
        data.pivot(index=["year", "quarter"], columns="marker", values="pct")
        .add_prefix("pct_")
        .reset_index()
    )
    summary = data.drop_duplicates("marker")
    periods = pd.DataFrame(
        [{"pct_" + row.marker: row.pre for row in summary.itertuples()}], index=["pre"]
    )
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    fig = plt.figure(figsize=(10.8, 13.5))
    outer = fig.add_gridspec(
        2,
        1,
        height_ratios=[3.3, 1.12],
        left=0.075,
        right=0.97,
        top=0.952,
        bottom=0.075,
        hspace=0.31,
    )
    top = outer[0].subgridspec(3, 3, wspace=0.47, hspace=0.52)
    blue, grey = ("#173e60", "#687680")
    fig.text(0.075, 0.976, "A", fontsize=17, fontweight="bold")
    fig.text(0.11, 0.977, "Share of abstracts containing the marker (%)", fontsize=13)
    x = q.year + (q.quarter - 1) / 4
    bp = data.iloc[0]
    for i, (name, title) in enumerate(PANELS):
        ax = fig.add_subplot(top[i // 3, i % 3])
        color = blue if name == "em" else grey
        if name == "em":
            ax.set_facecolor("#f1f5f9")
        y = q["pct_" + name]
        baseline = periods.loc["pre", "pct_" + name]
        ratio = summary.loc[summary.marker.eq(name), "post_pre_ratio"].iloc[0]
        ax.axvspan(bp.psi_lo, bp.psi_hi, color="#dce5ef", zorder=0)
        ax.axvline(2022 + 11 / 12, color="#bb6555", ls=":", lw=1.35)
        ax.axhline(baseline, color="#969da3", ls=(0, (4, 3)), lw=1.25)
        ax.plot(x, y, color=color, lw=1.7, marker="o", ms=3.5, zorder=3)
        ax.set_title(
            title,
            fontsize=11,
            pad=8,
            color=color,
            fontweight="bold" if name == "em" else "normal",
        )
        ax.text(
            0.035,
            0.94,
            f"×{ratio:.2f}",
            transform=ax.transAxes,
            color=color,
            va="top",
            fontsize=11,
            fontweight="bold" if name == "em" else "normal",
        )
        ax.set_xlim(2018.8, 2026.45)
        ax.set_ylim(0, max(y.max(), baseline) * 1.23)
        ax.set_xticks([2019, 2022, 2025])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.tick_params(labelsize=10)
        ax.grid(axis="y", alpha=0.1)
    legend_handles = [
        Line2D(
            [0],
            [0],
            color="#969da3",
            ls=(0, (4, 3)),
            lw=1.25,
            label="2019–2022 baseline",
        ),
        Line2D(
            [0],
            [0],
            color="#bb6555",
            ls=":",
            lw=1.35,
            label="ChatGPT release (Nov. 2022)",
        ),
        Patch(facecolor="#dce5ef", label="Em-dash breakpoint: 95% CI"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5225, outer[0].get_position(fig).y0 - 0.031),
        ncol=3,
        frameon=False,
        fontsize=9.3,
        handlelength=2.2,
        columnspacing=1.6,
        borderaxespad=0,
    )
    bottom = fig.add_subplot(outer[1])
    pos = bottom.get_position()
    bottom.set_position([0.285, pos.y0, 0.665, pos.height])
    fig.text(0.075, pos.y1 + 0.03, "B", fontsize=17, fontweight="bold")
    fig.text(0.11, pos.y1 + 0.031, "2026 prevalence relative to 2019–2022", fontsize=13)
    ordered = summary.sort_values("post_pre_ratio", ascending=False).reset_index(
        drop=True
    )
    for i, row in ordered.iterrows():
        ratio = row.post_pre_ratio
        color = blue if row.marker == "em" else "#8c9daa"
        bottom.barh(i, abs(ratio - 1), left=min(1, ratio), height=0.57, color=color)
        bottom.text(
            ratio + (0.025 if ratio >= 1 else -0.025),
            i,
            f"×{ratio:.2f}",
            ha="left" if ratio >= 1 else "right",
            va="center",
            color=color,
            fontweight="bold" if row.marker == "em" else "normal",
            fontsize=11,
        )
    bottom.set_yticks(range(len(ordered)), ordered.label, fontsize=10)
    for label, row in zip(bottom.get_yticklabels(), ordered.itertuples()):
        if row.marker == "em":
            label.set_color(blue)
            label.set_fontweight("bold")
    bottom.invert_yaxis()
    bottom.axvline(1, color="#969da3", ls="--", lw=1.25)
    bottom.set_xlim(
        max(0, ordered.post_pre_ratio.min() - 0.17), ordered.post_pre_ratio.max() + 0.18
    )
    bottom.xaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))
    bottom.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"×{v:.1f}"))
    bottom.set_xlabel("2026 / 2019–2022 prevalence", fontsize=11)
    bottom.spines["left"].set_visible(False)
    bottom.tick_params(axis="y", length=0, pad=8)
    bottom.grid(axis="x", alpha=0.09)
    bottom.set_axisbelow(True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
