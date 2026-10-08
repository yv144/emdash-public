import pandas as pd

from config import RESULTS
from utils.data import (
    aggregate,
    comparison_periods,
    write_csv,
)
from utils.statistics import fixed_composition


def run(counts):
    output = RESULTS / "robustness"
    result = pd.DataFrame(
        [fixed_composition(counts, group) for group in ["journal", "publisher"]]
    )
    write_csv(result, output / "composition.csv")
    write_csv(
        aggregate(comparison_periods(counts), ["period"]),
        output / "length_and_density.csv",
    )
    write_csv(
        aggregate(counts, ["year", "quarter", "year_quarter"]),
        output / "hyphens_and_length.csv",
    )
