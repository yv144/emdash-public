import numpy as np
import pandas as pd

VOLUME_TOLERANCE = 100
ORDERING_BASES = ("issue", "article_number", "page", "volume")
MIN_SLOTS_FOR_QUARTERS = 4
MIN_SLOTS_USABLE = 2
PARTIAL_YEARS = {2026: 2}
HISTORY_YEARS = 5
QUARTER_COLUMNS = [
    "volume_number",
    "volume_is_corrupt",
    "ordering_basis",
    "n_slots_observed",
    "n_slots_expected",
    "slot_position",
    "position_in_year",
    "quarter",
    "year_quarter",
    "quarter_is_resolved",
    "year_is_partial",
]
BASIS_SOURCE_COLUMN = {
    "issue": "issue_number",
    "article_number": "article_number",
    "page": "page_number",
    "volume": "volume_number",
}


def leading_integer(values):
    return pd.to_numeric(values.astype(str).str.extract("(\\d+)")[0], errors="coerce")


def clean_volume_numbers(
    articles, journal_column, year_column, volume_column, tolerance=VOLUME_TOLERANCE
):
    volume = leading_integer(articles[volume_column])
    journal_year = [articles[journal_column], articles[year_column]]
    median_volume = volume.groupby(journal_year).transform("median")
    is_corrupt = ((volume - median_volume).abs() > tolerance).fillna(False)
    cleaned_volume = volume.where(~is_corrupt)
    n_distinct = cleaned_volume.groupby(journal_year).transform("nunique")
    unambiguous = (
        cleaned_volume.groupby(journal_year).transform("median").where(n_distinct == 1)
    )
    n_refilled = int((cleaned_volume.isna() & unambiguous.notna()).sum())
    cleaned_volume = cleaned_volume.fillna(unambiguous)
    report = {
        "parsed": int(volume.notna().sum()),
        "corrupt": int(is_corrupt.sum()),
        "refilled": n_refilled,
        "unresolved": int(cleaned_volume.isna().sum()),
    }
    return (cleaned_volume, is_corrupt, report)


def rank_publication_slots(volume, order_values, journal_year):
    order_values = order_values.where(volume.notna())
    volume_rank = (
        volume.where(order_values.notna()).groupby(journal_year).rank(method="dense")
    )
    order_rank = order_values.groupby(journal_year + [volume]).rank(method="dense")
    order_width = order_rank.groupby(journal_year).transform("max")
    combined_rank = volume_rank * (order_width + 1) + order_rank
    slot_position = combined_rank.groupby(journal_year).rank(method="dense")
    return (slot_position, slot_position.groupby(journal_year).transform("max"))


def choose_ordering_basis(basis_candidates):
    index = next(iter(basis_candidates.values()))[0].index
    basis = pd.Series("none", index=index, dtype=object)
    slot_position = pd.Series(np.nan, index=index, dtype="float64")
    n_slots = pd.Series(np.nan, index=index, dtype="float64")
    for threshold in (MIN_SLOTS_USABLE, MIN_SLOTS_FOR_QUARTERS):
        for basis_name in reversed(ORDERING_BASES):
            candidate_slot, candidate_n_slots = basis_candidates[basis_name]
            qualifies = (candidate_n_slots >= threshold) & candidate_slot.notna()
            basis = basis.mask(qualifies, basis_name)
            slot_position = slot_position.mask(qualifies, candidate_slot)
            n_slots = n_slots.mask(qualifies, candidate_n_slots)
    return (basis, slot_position, n_slots)


def expected_full_year_slots(
    articles, journal_column, year_column, partial_years, history_years
):
    per_journal_year = articles[
        [journal_column, year_column, "ordering_basis", "n_slots_observed"]
    ].drop_duplicates(subset=[journal_column, year_column])
    complete_years = per_journal_year[
        ~per_journal_year[year_column].isin(partial_years)
        & per_journal_year["n_slots_observed"].notna()
    ]
    recent_years = (
        complete_years.sort_values(year_column)
        .groupby([journal_column, "ordering_basis"], observed=True)
        .tail(history_years)
    )
    return (
        recent_years.groupby([journal_column, "ordering_basis"], observed=True)[
            "n_slots_observed"
        ]
        .median()
        .rename("expected_slots")
        .reset_index()
    )


def assign_quarters(
    articles,
    journal_column="journal",
    year_column="year",
    volume_column="volume",
    issue_column="issue",
    article_number_column="article_no",
    page_column="page_start",
    tolerance=VOLUME_TOLERANCE,
    partial_years=None,
    history_years=HISTORY_YEARS,
    verbose=True,
):
    partial_years = PARTIAL_YEARS if partial_years is None else partial_years
    out = articles.copy()
    out["_year"] = pd.to_numeric(out[year_column], errors="coerce")
    volume, is_corrupt, volume_report = clean_volume_numbers(
        out, journal_column, "_year", volume_column, tolerance
    )
    out["volume_number"] = volume
    out["volume_is_corrupt"] = is_corrupt
    out["issue_number"] = leading_integer(out[issue_column])
    out["article_number"] = leading_integer(out[article_number_column])
    out["page_number"] = leading_integer(out[page_column])
    journal_year = [out[journal_column], out["_year"]]
    basis_candidates = {
        basis_name: rank_publication_slots(
            out["volume_number"], out[source_column], journal_year
        )
        for basis_name, source_column in BASIS_SOURCE_COLUMN.items()
    }
    out["ordering_basis"], out["slot_position"], out["n_slots_observed"] = (
        choose_ordering_basis(basis_candidates)
    )
    out["year_is_partial"] = out["_year"].isin(partial_years)
    expected_slots = expected_full_year_slots(
        out, journal_column, "_year", partial_years, history_years
    )
    out = out.merge(expected_slots, on=[journal_column, "ordering_basis"], how="left")
    quarters_covered = out["_year"].map(partial_years)
    rescaled_slots = out["n_slots_observed"] * 4 / quarters_covered
    denominator = out["n_slots_observed"].where(
        ~out["year_is_partial"], out["expected_slots"].fillna(rescaled_slots)
    )
    out["n_slots_expected"] = np.maximum(denominator, out["n_slots_observed"])
    out["position_in_year"] = (out["slot_position"] - 0.5) / out["n_slots_expected"]
    quarter = np.floor(out["position_in_year"] * 4) + 1
    out["quarter"] = quarter.clip(lower=1, upper=quarters_covered.fillna(4)).astype(
        "Int64"
    )
    out["quarter_is_resolved"] = (
        out["n_slots_expected"] >= MIN_SLOTS_FOR_QUARTERS
    ).fillna(False)
    out["year_quarter"] = (
        out["_year"].astype("Int64").astype(str) + "Q" + out["quarter"].astype(str)
    ).where(out["quarter"].notna())
    out = out.drop(
        columns=[
            "_year",
            "expected_slots",
            "issue_number",
            "article_number",
            "page_number",
        ]
    )
    if verbose:
        n_articles = len(out)
        n_assigned = int(out["quarter"].notna().sum())
        n_resolved = int((out["quarter"].notna() & out["quarter_is_resolved"]).sum())
        print(
            f"Volume: {volume_report['parsed']:,} parsed, {volume_report['corrupt']:,} corrupt, {volume_report['refilled']:,} refilled, {volume_report['unresolved']:,} unresolved"
        )
        print(
            f"Quarter assigned: {n_assigned:,} / {n_articles:,} ({n_assigned / n_articles:.2%})"
        )
        print(
            f"  of which resolved (>= {MIN_SLOTS_FOR_QUARTERS} slots): {n_resolved:,} ({n_resolved / n_articles:.2%})"
        )
        print("\nOrdering basis used (% of articles):")
        print(
            (out["ordering_basis"].value_counts(normalize=True) * 100).to_string(
                float_format=lambda value: f"{value:6.2f}"
            )
        )
    return out
