import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from utils.figure_style import style

FONT_FAMILY = "TeX Gyre Pagella"
TEAL, TEAL_B, TEAL_F = "#106870", "#609898", "#edf4f3"
RUST, RUST_B, RUST_F = "#985038", "#b89078", "#faf1ec"
BLUE, BLUE_B, BLUE_F = "#205888", "#7898b0", "#f0f4f8"
GREY, TEXT = "#6b7b8c", "#222222"


def box(
    ax,
    x,
    y,
    w,
    h,
    title,
    body,
    fill,
    border,
    title_color,
    dashed=False,
    body_size=7.3,
    title_size=8.4,
    wrap=23,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=0.9,
        edgecolor=border,
        facecolor=fill,
        linestyle=(0, (3, 2)) if dashed else "solid",
    )
    ax.add_patch(patch)
    ax.text(
        x + 1.1,
        y + h - 1.3,
        title,
        fontsize=title_size,
        fontweight="bold",
        color=title_color,
        va="top",
        ha="left",
    )
    lines = []
    for para in body.split("\n"):
        lines += textwrap.wrap(para, wrap) or [""]
    ax.text(
        x + 1.1,
        y + h - 4.4,
        "\n".join(lines),
        fontsize=body_size,
        color=TEXT,
        va="top",
        ha="left",
        linespacing=1.18,
    )


def arrow(ax, x1, y1, x2, y2, color=GREY, style="-|>", lw=0.9, ls="solid"):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle=style,
            mutation_scale=8,
            color=color,
            linewidth=lw,
            linestyle=ls,
            shrinkA=0,
            shrinkB=0,
        )
    )


def header(ax, x, y, label, color, width):
    ax.text(x, y, label, fontsize=10.5, fontweight="bold", color=color, va="bottom", ha="left")
    ax.plot([x, x + width], [y - 0.6, y - 0.6], color=color, linewidth=0.9)


def draw(path):
    style()
    plt.rcParams.update({"font.family": FONT_FAMILY, "figure.dpi": 300})
    width = 7.4
    fig = plt.figure(figsize=(width, width * (86 - 5.5) / 104))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 104), ylim=(5.5, 86))
    ax.set_axis_off()

    column_width, gap, left = 19.2, 1.3, 1.5
    xs = [left + i * (column_width + gap) for i in range(5)]
    row_width = xs[4] + column_width - left

    header(
        ax,
        left,
        83.0,
        "A  The classic cycle of a stigmatized form (Labov 1972; Agha 2003)",
        TEAL,
        row_width,
    )
    ax.text(
        left,
        81.7,
        (
            "Source: a speech community.   Spread: by contact.   Stigma: social standing."
            "   Correction: by the speakers themselves, over decades."
        ),
        fontsize=7.2,
        color=TEAL,
        va="top",
        ha="left",
        style="italic",
    )
    classic_y, classic_height = 66.4, 12.8
    classic = [
        ("Indicator", "Correlates with a group; below awareness; no style shifting."),
        ("Marker", "Style-shifted in careful speech; responded to, not yet named."),
        ("Stereotype", "Named and overtly commented on; often inaccurate about actual usage."),
        (
            "Correction",
            "Speakers avoid or overcorrect the form; the change runs through the community over years.",
        ),
        ("Outcome", "The form recedes or persists; the evaluation stays with the community."),
    ]
    for i, (title, body) in enumerate(classic):
        box(ax, xs[i], classic_y, column_width, classic_height, title, body, TEAL_F, TEAL_B, TEAL)
        if i < 4:
            arrow(
                ax,
                xs[i] + column_width,
                classic_y + classic_height / 2,
                xs[i + 1],
                classic_y + classic_height / 2,
            )

    departure_y, departure_height = 44.5, 18.5
    departures = [
        (
            0,
            "Departure 1: source",
            (
                "A one-to-many tool that writes into the recipient's own text; the form spreads"
                " at once, as tools spread, not by contact."
            ),
        ),
        (
            2,
            "Departure 2: stigma",
            (
                "Epistemic, not social: an inference of non-authorship. Iconization, erasure "
                "and fractal recursivity move it from the machine to fluent non-native writers."
            ),
        ),
        (
            3,
            "Departure 3: correction",
            (
                "From above, by a non-speaker: the vendor drops the emblem for every writer at "
                "once. The signal erases itself; the stereotype outlives the trait."
            ),
        ),
    ]
    for col, title, body in departures:
        box(
            ax,
            xs[col],
            departure_y,
            column_width,
            departure_height,
            title,
            body,
            BLUE_F,
            BLUE_B,
            BLUE,
            body_size=7.0,
            title_size=7.8,
        )
        cx = xs[col] + column_width / 2
        arrow(
            ax,
            cx,
            departure_y + departure_height,
            cx,
            classic_y - 0.3,
            color=BLUE_B,
            ls=(0, (2, 2)),
            style="-|>",
            lw=0.8,
        )
        arrow(ax, cx, departure_y, cx, 41.3, color=BLUE_B, ls=(0, (2, 2)), style="-|>", lw=0.8)
    ax.text(
        xs[1] + column_width / 2,
        departure_y + departure_height / 2,
        "same sequence,\ncompressed\ninto months",
        fontsize=7.0,
        color=GREY,
        ha="center",
        va="center",
        style="italic",
    )
    ax.text(
        xs[4] + column_width / 2,
        departure_y + departure_height / 2,
        "same sequence,\nthe trait is removed,\nthe stereotype stays",
        fontsize=7.0,
        color=GREY,
        ha="center",
        va="center",
        style="italic",
    )

    header(
        ax,
        left,
        38.6,
        "B  The life cycle of a machine trace: the em dash, 2022 to 2027",
        RUST,
        row_width,
    )
    ax.text(
        left,
        37.3,
        (
            "Source: a tool in general use.   Spread: simultaneous across fields.   Stigma:"
            " authorship.   Correction: by writers and by the vendor, within months."
        ),
        fontsize=7.2,
        color=RUST,
        va="top",
        ha="left",
        style="italic",
    )
    machine_y, machine_height = 16.8, 18.0
    machine = [
        (
            "Indicator (measured)",
            (
                "Silent rise in the record: the series breaks at 2024Q2, drafted about 2023; 16"
                " of 17 areas, 11 of 11 publishers (Sects. 4.2 to 4.4)."
            ),
        ),
        (
            "Marker (unobserved)",
            (
                "Compressed or skipped: a corpus of abstracts has no casual register against "
                "which style shifting could show (Sect. 2.4)."
            ),
        ),
        (
            "Stereotype (dated)",
            (
                "First documented notice 2 October 2024; named “the ChatGPT hyphen” and "
                "codified in guides during 2025 (Table 1)."
            ),
        ),
        (
            "Correction, two ends",
            (
                "Writers remove 23% of the em dashes in model drafts (Baumler et al. 2026); the"
                " vendor makes the mark suppressible on instruction, Nov 2025 (Perez 2025)."
            ),
        ),
        (
            "Outcome (specified)",
            (
                "Signal erased, practice continues, stereotype persists. Test: deceleration, "
                "plateau or reversal by 2027Q4 (Sect. 5.8)."
            ),
        ),
    ]
    for i, (title, body) in enumerate(machine):
        box(
            ax,
            xs[i],
            machine_y,
            column_width,
            machine_height,
            title,
            body,
            RUST_F,
            RUST_B,
            RUST,
            dashed=(i == 1),
            body_size=7.0,
        )
        if i < 4:
            arrow(
                ax,
                xs[i] + column_width,
                machine_y + machine_height / 2,
                xs[i + 1],
                machine_y + machine_height / 2,
            )

    ty = 12.0
    ax.plot([left, left + row_width], [ty, ty], color=GREY, linewidth=0.8)
    events = [
        (xs[0] + 1.5, left, "left", "Nov 2022\nChatGPT released"),
        (xs[0] + column_width + 0.6, xs[0] + column_width + 0.6, "center", "2024Q2\nseries breaks"),
        (
            xs[2] + column_width / 2,
            xs[2] + column_width / 2,
            "center",
            "Oct 2024 to 2025\nnoticed, named, codified",
        ),
        (xs[3] + column_width / 2, xs[3] + column_width / 2, "center", "Nov 2025\nvendor switch"),
        (xs[4] + column_width - 1.5, xs[4] + column_width, "right", "2026 to 2027\nspecified test"),
    ]
    for mx, lx, ha, lab in events:
        ax.plot([mx], [ty], marker="o", markersize=3, color=GREY)
        ax.text(lx, ty - 1.0, lab, fontsize=6.8, color=GREY, ha=ha, va="top", linespacing=1.1)

    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
