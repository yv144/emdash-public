import pandas as pd

from config import RESULTS, MARKERS
from utils.data import (
    aggregate,
    comparison_periods,
    write_csv,
)


def run(counts):
    output = RESULTS / "markers"
    quarters = aggregate(counts, ["year", "quarter", "year_quarter"])
    write_csv(quarters, output / "quarterly.csv")
    periods = aggregate(comparison_periods(counts), ["period"]).set_index("period")
    write_csv(periods.reset_index(), output / "periods.csv")
    rows = []
    for marker, label in MARKERS.items():
        base, comp = periods.loc["baseline"], periods.loc["comparison"]
        rows.append(
            {
                "marker": marker,
                "label": label,
                "n_baseline": int(base.n_abstracts),
                "k_baseline": int(base["hits_" + marker]),
                "n_comparison": int(comp.n_abstracts),
                "k_comparison": int(comp["hits_" + marker]),
                "pre": base["pct_" + marker],
                "post": comp["pct_" + marker],
                "change_pp": comp["pct_" + marker] - base["pct_" + marker],
                "post_pre_ratio": comp["pct_" + marker] / base["pct_" + marker],
            }
        )
    write_csv(pd.DataFrame(rows), output / "ratios.csv")
    long = quarters.melt(
        id_vars=["year", "quarter", "n_abstracts"],
        value_vars=["hits_" + m for m in MARKERS],
        var_name="marker",
        value_name="n_with_marker",
    )
    long["marker"] = long.marker.str.removeprefix("hits_")
    write_csv(long, output / "quarterly_markers.csv")
