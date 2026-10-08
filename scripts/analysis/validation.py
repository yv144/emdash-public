import pandas as pd

from config import DATA, RESULTS
from utils.data import write_csv


def run():
    sample = pd.read_csv(DATA / "validation_counts.csv")
    sample["publisher_positive"] = sample.n.where(sample.publisher_em_dash, 0)
    annual = pd.read_csv(RESULTS / "prevalence" / "annual.csv")
    strata = sample.groupby(["year", "scopus_em_dash"], as_index=False).agg(
        reviewed=("n", "sum"), publisher_positive=("publisher_positive", "sum")
    )
    strata = strata.merge(annual[["year", "n_abstracts", "hits_em"]], on="year")
    strata["population"] = strata.hits_em.where(
        strata.scopus_em_dash, strata.n_abstracts - strata.hits_em
    )
    strata["estimated_positive"] = (
        strata.population * strata.publisher_positive / strata.reviewed
    )
    rows = []
    for label, years in [("2019–2022", range(2019, 2023)), ("2023–2026", range(2023, 2027))]:
        counts = annual[annual.year.isin(years)]
        checked = strata[strata.year.isin(years)]
        rows.append({
            "period": label,
            "n_abstracts": int(counts.n_abstracts.sum()),
            "observed_pct": 100 * counts.hits_em.sum() / counts.n_abstracts.sum(),
            "adjusted_pct": 100 * checked.estimated_positive.sum() / checked.population.sum(),
        })
    result = pd.DataFrame(rows)
    write_csv(result, RESULTS / "validation" / "periods.csv")
    write_csv(pd.DataFrame([{
        "reviewed": int(sample.n.sum()),
        "agreement": int(sample.loc[sample.scopus_em_dash.eq(sample.publisher_em_dash), "n"].sum()),
        "observed_change_pp": result.observed_pct.iloc[1] - result.observed_pct.iloc[0],
        "adjusted_change_pp": result.adjusted_pct.iloc[1] - result.adjusted_pct.iloc[0],
    }]), RESULTS / "validation" / "summary.csv")
