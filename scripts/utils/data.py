import hashlib

import numpy as np
import pandas as pd

from config import BASELINE_YEARS, COMPARISON_YEAR, MARKERS, DATA


def read_counts(resolved=False):
    name = "quarterly_counts.csv.gz" if resolved else "yearly_counts.csv.gz"
    return pd.read_csv(DATA / name)


def comparison_periods(counts):
    result = counts.copy()
    result["period"] = np.select(
        [result.year.isin(BASELINE_YEARS), result.year.eq(COMPARISON_YEAR)],
        ["baseline", "comparison"],
        default="other",
    )
    return result[result.period.ne("other")]


def count_articles(articles, keys):
    columns = {
        "n_abstracts": ("eid", "size"),
        "characters": ("characters", "sum"),
        "em_occurrences": ("count_em", "sum"),
        "hyphen_occurrences": ("count_hyphen_all", "sum"),
    }
    columns.update(
        {
            "hits_" + marker: ("has_" + marker, "sum")
            for marker in [*MARKERS, "hyphen_all"]
        }
    )
    result = (
        articles.groupby(keys, observed=True, dropna=False).agg(**columns).reset_index()
    )
    return result


def aggregate(counts, keys):
    columns = ["n_abstracts", "characters", "em_occurrences", "hyphen_occurrences"]
    columns += ["hits_" + marker for marker in [*MARKERS, "hyphen_all"]]
    result = counts.groupby(keys, observed=True, dropna=False)[columns].sum().reset_index()
    return add_rates(result)


def add_rates(result):
    for marker in [*MARKERS, "hyphen_all"]:
        result["pct_" + marker] = 100 * result["hits_" + marker] / result.n_abstracts
    result["mean_characters"] = result.characters / result.n_abstracts
    result["em_per_1000_characters"] = 1000 * result.em_occurrences / result.characters
    result["hyphen_per_1000_characters"] = (
        1000 * result.hyphen_occurrences / result.characters
    )
    return result


def write_csv(table, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0} if path.suffix == ".gz" else None)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
