import pandas as pd
from statsmodels.stats.proportion import proportions_ztest

from config import RESULTS
from utils.data import aggregate, write_csv


def run(counts):
    output = RESULTS / "prevalence"
    annual = aggregate(counts, ["year"])
    write_csv(annual, output / "annual.csv")
    before = counts[counts.year.le(2022)]
    after = counts[counts.year.ge(2023)]
    z, p = proportions_ztest(
        [after.hits_em.sum(), before.hits_em.sum()],
        [int(after.n_abstracts.sum()), int(before.n_abstracts.sum())],
        alternative="larger",
    )
    result = pd.DataFrame(
        [
            {
                "n_baseline": int(before.n_abstracts.sum()),
                "k_baseline": int(before.hits_em.sum()),
                "pct_baseline": 100 * before.hits_em.sum() / before.n_abstracts.sum(),
                "n_post": int(after.n_abstracts.sum()),
                "k_post": int(after.hits_em.sum()),
                "pct_post": 100 * after.hits_em.sum() / after.n_abstracts.sum(),
                "z": z,
                "p_one_sided": p,
            }
        ]
    )
    write_csv(result, output / "period_comparison.csv")
