import numpy as np
import pandas as pd
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_confint,
    proportions_ztest,
)

from config import BASELINE_YEARS, COMPARISON_YEAR
from utils.data import comparison_periods


def compare_counts(k_baseline, n_baseline, k_comparison, n_comparison):
    base_lo, base_hi = proportion_confint(k_baseline, n_baseline, method="wilson")
    comp_lo, comp_hi = proportion_confint(k_comparison, n_comparison, method="wilson")
    diff_lo, diff_hi = confint_proportions_2indep(
        k_comparison,
        n_comparison,
        k_baseline,
        n_baseline,
        method="newcomb",
        compare="diff",
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        z, p = proportions_ztest([k_comparison, k_baseline], [n_comparison, n_baseline])
    baseline = 100 * k_baseline / n_baseline
    comparison = 100 * k_comparison / n_comparison
    return {
        "n_baseline": n_baseline,
        "k_baseline": k_baseline,
        "pct_baseline": baseline,
        "pct_baseline_lo": 100 * base_lo,
        "pct_baseline_hi": 100 * base_hi,
        "n_comparison": n_comparison,
        "k_comparison": k_comparison,
        "pct_comparison": comparison,
        "pct_comparison_lo": 100 * comp_lo,
        "pct_comparison_hi": 100 * comp_hi,
        "change_pp": comparison - baseline,
        "change_pp_lo": 100 * diff_lo,
        "change_pp_hi": 100 * diff_hi,
        "z": z,
        "p": p,
    }


def subgroup_comparisons(counts, group):
    rows = []
    for name, subset in counts.groupby(group, observed=True):
        base = subset[subset.year.isin(BASELINE_YEARS)]
        comp = subset[subset.year.eq(COMPARISON_YEAR)]
        if base.empty or comp.empty:
            continue
        row = compare_counts(
            int(base.hits_em.sum()), int(base.n_abstracts.sum()),
            int(comp.hits_em.sum()), int(comp.n_abstracts.sum())
        )
        row.update(
            {
                group: name,
                "n_journals": subset.journal.nunique(),
                "n_journals_baseline": base.journal.nunique(),
                "n_journals_comparison": comp.journal.nunique(),
                "corpus_share_pct": 100 * subset.n_abstracts.sum() / counts.n_abstracts.sum(),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("pct_baseline").reset_index(drop=True)


def fixed_composition(counts, group):
    data = comparison_periods(counts)
    counts = data.groupby([group, "period"], observed=True).agg(
        n=("n_abstracts", "sum"), k=("hits_em", "sum")
    )
    counts = counts.unstack("period").dropna()
    n0, n1 = counts["n", "baseline"], counts["n", "comparison"]
    p0, p1 = counts["k", "baseline"] / n0, counts["k", "comparison"] / n1
    weights = n0 / n0.sum()
    return {
        "group": group,
        "common_groups": len(counts),
        "n_pre": int(n0.sum()),
        "n_post": int(n1.sum()),
        "coverage_pre_pct": 100 * n0.sum() / data.loc[data.period.eq("baseline"), "n_abstracts"].sum(),
        "coverage_post_pct": 100 * n1.sum() / data.loc[data.period.eq("comparison"), "n_abstracts"].sum(),
        "pre_pct": 100 * (weights * p0).sum(),
        "post_observed_pct": 100 * counts["k", "comparison"].sum() / n1.sum(),
        "post_fixed_weights_pct": 100 * (weights * p1).sum(),
        "fixed_change_pp": 100 * (weights * (p1 - p0)).sum(),
    }


def baseline_departure(series):
    baseline = series.loc[series.year.isin(BASELINE_YEARS), "pct_em"]
    threshold = baseline.mean() + 3 * baseline.std(ddof=1)
    above = series.pct_em.gt(threshold).to_numpy()
    starts = np.flatnonzero(above[:-1] & above[1:])
    onset = series.iloc[starts[0]].year_quarter if len(starts) else None
    return baseline.mean(), threshold, onset
