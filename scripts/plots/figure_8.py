import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
CHATGPT_X = 2022 + 11 / 12
GREY, GREY_TEXT = ("#888888", "#4A4A4A")
BAND_TOP = 14.0
FS_ANNOT, FS_SPAN, FS_LEGEND, FS_LEGEND_TITLE = (12, 11.5, 12, 12.5)


def draw(data, path):
    style()
    plot_q = data.rename(columns={"pct_em": "em_dash_rate"}).copy()
    plot_q["time"] = plot_q.year + (plot_q.quarter - 1) / 4
    plot_q["area"] = plot_q.area.replace(
        {
            "Biochemistry, Genetics and Molecular Biology": "Biochemistry & Molecular Biology"
        }
    )
    plot_q = plot_q.sort_values(["area", "time"])
    onsets = data.onset_quarter.dropna()
    dates = onsets.str[:4].astype(int) + (onsets.str[-1].astype(int) - 1) / 4
    ONSET_LO, ONSET_HI = (dates.min(), dates.max())
    months_lo = round(12 * (ONSET_LO - CHATGPT_X))
    months_hi = round(12 * (ONSET_HI - CHATGPT_X))
    ONSET_SPAN = f"{months_lo} to {months_hi} months (estimated)"
    ONSET_LABEL = (
        f"all five areas leave\ntheir baseline\n{onsets.min()} to {onsets.max()}"
    )
    sns.set_theme(style="ticks", context="paper", font_scale=1.35)
    plt.rcParams.update({"font.family": "TeX Gyre Pagella", "figure.dpi": 150})
    fig3alt, ax = plt.subplots(figsize=(10, 5.5))
    ax.fill_betweenx(
        [0, BAND_TOP], ONSET_LO, ONSET_HI, color=GREY, alpha=0.16, lw=0, zorder=0
    )
    sns.lineplot(
        data=plot_q,
        x="time",
        y="em_dash_rate",
        hue="area",
        style="area",
        markers=True,
        dashes=False,
        palette="colorblind",
        linewidth=2.4,
        markersize=5,
        ax=ax,
    )
    ax.set_xlim(2018.8, 2026.35)
    ax.set_ylim(0, plot_q["em_dash_rate"].max() * 1.55)
    y_top = ax.get_ylim()[1]
    ax.axvline(CHATGPT_X, color="#C0392B", linestyle=":", linewidth=2)
    ax.text(
        CHATGPT_X - 0.08,
        y_top * 0.99,
        "ChatGPT release\n(Nov. 2022)",
        color="#C0392B",
        fontsize=FS_ANNOT,
        ha="right",
        va="top",
    )
    ax.text(
        (ONSET_LO + ONSET_HI) / 2,
        y_top * 0.99,
        ONSET_LABEL,
        color=GREY_TEXT,
        fontsize=FS_ANNOT,
        ha="center",
        va="top",
        linespacing=1.2,
    )
    y_arrow = y_top * 0.66
    ax.annotate(
        "",
        xy=(ONSET_LO, y_arrow),
        xytext=(CHATGPT_X, y_arrow),
        arrowprops={"arrowstyle": "->", "color": GREY, "linewidth": 1.3},
    )
    ax.text(
        (CHATGPT_X + ONSET_LO) / 2,
        y_arrow * 1.03,
        ONSET_SPAN,
        color=GREY_TEXT,
        fontsize=FS_SPAN,
        ha="center",
        va="bottom",
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Abstracts containing an em dash (%)")
    ax.set_xticks(range(2019, 2027))
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda value, _: f"{value:.1f}%")
    )
    ax.legend(
        title="Research area",
        loc="upper left",
        frameon=True,
        framealpha=0.9,
        fontsize=FS_LEGEND,
        title_fontsize=FS_LEGEND_TITLE,
    )
    sns.despine(ax=ax)
    fig3alt.tight_layout()
    fig3alt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig3alt)
