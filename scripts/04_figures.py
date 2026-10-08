import pandas as pd

from config import FIGURES, MARKERS, RESULTS
from plots import figure_1, figure_2, figure_3, figure_4, figure_5, figure_6, figure_7, figure_8
from utils.data import write_csv


def read(folder, name):
    return pd.read_csv(RESULTS / folder / (name + ".csv"))


def output(number, data, plot):
    path = RESULTS / "figures" / f"figure_{number}.csv"
    write_csv(data, path)
    FIGURES.mkdir(exist_ok=True)
    plot.draw(pd.read_csv(path), FIGURES / f"figure_{number}.png")


def main():
    FIGURES.mkdir(exist_ok=True)
    figure_1.draw(FIGURES / "figure_1.png")

    annual = read("prevalence", "annual")
    output(3, annual[["year", "n_abstracts", "hits_em", "pct_em"]], figure_3)
    areas = read("subgroups", "areas")
    publishers = read("subgroups", "publishers")
    output(4, areas, figure_4)
    output(5, publishers, figure_5)

    breakpoint = read("time_series", "breakpoint").iloc[0]
    predictions = read("time_series", "predictions")
    for name in ["psi", "psi_lo", "psi_hi"]:
        predictions[name] = breakpoint[name]
    output(6, predictions, figure_6)

    quarterly = read("markers", "quarterly")
    pieces = []
    for marker in MARKERS:
        part = quarterly[["year", "quarter", "year_quarter", "n_abstracts",
                          "hits_" + marker, "pct_" + marker]].copy()
        part = part.rename(columns={"hits_" + marker: "n_with_marker", "pct_" + marker: "pct"})
        part["marker"] = marker
        pieces.append(part)
    marker_data = pd.concat(pieces).merge(read("markers", "ratios"), on="marker", validate="many_to_one")
    marker_data["label"] = marker_data.marker.map(dict(figure_7.PANELS))
    marker_data["decimal_year"] = marker_data.year + (marker_data.quarter - 1) / 4
    for name in ["psi", "psi_lo", "psi_hi"]:
        marker_data[name] = breakpoint[name]
    output(7, marker_data, figure_7)

    fields = read("field_timing", "quarterly")
    fields = fields[["area", "year", "quarter", "year_quarter", "n_abstracts", "hits_em",
                     "pct_em", "baseline_mean_pct", "threshold_pct", "onset_quarter"]]
    onset = read("field_timing", "departures").onset_quarter.dropna()
    dates = onset.str[:4].astype(int) + (onset.str[-1].astype(int) - 1) / 4
    fields["onset_window_start"] = dates.min()
    fields["onset_window_end"] = dates.max()
    output(8, fields, figure_8)

    counts = read("preparation", "corpus_counts").set_index("stage")["count"].to_dict()
    period = read("prevalence", "period_comparison").iloc[0]
    validation = read("validation", "summary").iloc[0]
    counts.update({
        "em_positive": int(annual.hits_em.sum()),
        "n_baseline": int(period.n_baseline), "n_post": int(period.n_post),
        "areas": len(areas), "area_share": areas.corpus_share_pct.sum(),
        "publishers": len(publishers), "publisher_share": publishers.corpus_share_pct.sum(),
        "validation_reviewed": int(validation.reviewed),
        "validation_agreement": int(validation.agreement),
    })
    output(2, pd.DataFrame(counts.items(), columns=["metric", "value"]), figure_2)


if __name__ == "__main__":
    main()
