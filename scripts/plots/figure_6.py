import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.lines import Line2D

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
NAVY, RED, GREY = ("#1B3A5C", "#C0392B", "#888888")
CHATGPT_X = 2022 + 11 / 12
LABEL_FS = 16
TICK_FS = 14
LEGEND_FS = 14
ANNOT_FS = 13


def draw(data, path):
    style()
    d = data.sort_values("decimal_year")
    m = d.iloc[0].copy()
    m["fitted_end"] = d.iloc[-1].fitted
    m["cf_end"] = d.iloc[-1].counterfactual
    m["effect_pp"] = m.fitted_end - m.cf_end
    m["effect_pct"] = 100 * m.effect_pp / m.cf_end
    sns.set_theme(style="ticks", context="paper")
    plt.rcParams.update({"font.family": FONT_FAMILY, "figure.dpi": 150})
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.axvspan(m.psi_lo, m.psi_hi, color=NAVY, alpha=0.1, lw=0, zorder=0)
    ax.axvline(CHATGPT_X, color=RED, ls=":", lw=2.0)
    post = d[d.post == 1]
    ax.fill_between(
        post.decimal_year, post.cf_lo, post.cf_hi, color=GREY, alpha=0.22, lw=0
    )
    ax.plot(post.decimal_year, post.counterfactual, color=GREY, ls="--", lw=2.0)
    ax.scatter(
        d.decimal_year,
        d.observed,
        s=22,
        color=NAVY,
        zorder=3,
        alpha=0.75,
        edgecolor="none",
    )
    for _, seg in d.groupby("post"):
        ax.plot(seg.decimal_year, seg.fitted, color=NAVY, lw=2.8, zorder=2)
    ax.set_xlim(2018.8, 2026.3)
    ax.set_ylim(0, 1.08 * max(d.observed.max(), d.fitted.max(), d.cf_hi.max()))
    ax.set_xticks(range(2019, 2027))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.tick_params(labelsize=TICK_FS)
    ax.set_xlabel("Year", fontsize=LABEL_FS, labelpad=8)
    ax.set_ylabel("Abstracts containing an em dash (%)", fontsize=LABEL_FS, labelpad=8)
    kw = {"xycoords": ("data", "axes fraction"), "annotation_clip": False}
    ax.annotate(
        "ChatGPT released\nNovember 2022",
        xy=(CHATGPT_X - 0.07, 1.13),
        ha="right",
        va="top",
        color=RED,
        fontsize=ANNOT_FS,
        **kw,
    )
    ax.annotate(
        f"Breakpoint {m.psi:.2f}\n95% CI {m.psi_lo:.2f} to {m.psi_hi:.2f}",
        xy=(m.psi, 1.13),
        ha="center",
        va="top",
        color=NAVY,
        fontsize=ANNOT_FS,
        **kw,
    )
    x_end = d.decimal_year.max()
    ax.annotate(
        "",
        xy=(x_end + 0.1, m.fitted_end),
        xytext=(x_end + 0.1, m.cf_end),
        arrowprops={"arrowstyle": "<->", "color": "black", "lw": 1.2},
    )
    ax.text(
        x_end + 0.2,
        (m.fitted_end + m.cf_end) / 2,
        f"{m.effect_pp:+.2f} points\n({m.effect_pct:+.0f}%)",
        fontsize=ANNOT_FS,
        va="center",
        ha="left",
    )
    handles = [
        Line2D(
            [],
            [],
            marker="o",
            ls="none",
            color=NAVY,
            ms=6,
            label="Observed quarterly rate",
        ),
        Line2D([], [], color=NAVY, lw=2.8, label="Fitted trend"),
        Line2D(
            [], [], color=GREY, ls="--", lw=2.0, label="Counterfactual, with 95% CI"
        ),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        frameon=False,
        fontsize=LEGEND_FS,
        handlelength=2.2,
        borderaxespad=0.8,
        labelspacing=0.5,
    )
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
