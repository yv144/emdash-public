import pandas as pd

from config import RESULTS
from utils.data import aggregate, write_csv
from utils.statistics import baseline_departure


def run(counts):
    counts = counts[counts.year_quarter.le("2026Q1")]
    fields = counts.groupby("area").n_abstracts.sum().nlargest(5).index
    quarters = aggregate(
        counts[counts.area.isin(fields)],
        ["area", "year", "quarter", "year_quarter"],
    )
    rows = []
    for area, series in quarters.groupby("area"):
        mean, threshold, onset = baseline_departure(
            series.sort_values(["year", "quarter"])
        )
        rows.append(
            {
                "area": area,
                "baseline_mean_pct": mean,
                "threshold_pct": threshold,
                "onset_quarter": onset,
                "n_abstracts": int(series.n_abstracts.sum()),
                "share_of_its_sample_pct": 100
                * series.n_abstracts.sum()
                / counts.n_abstracts.sum(),
            }
        )
    departures = pd.DataFrame(rows)
    quarters = quarters.merge(
        departures.drop(columns="n_abstracts"), on="area", validate="many_to_one"
    )
    write_csv(quarters, RESULTS / "field_timing" / "quarterly.csv")
    write_csv(departures, RESULTS / "field_timing" / "departures.csv")
