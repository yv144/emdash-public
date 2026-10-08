import json
import platform

import pandas as pd

from config import RESULTS, DATA, DATASET_PATH, PREPARED, ROOT, SOURCE_LIST_PATH
from utils.corpus import (
    build_corpus,
    em_dash_rule_variants,
    export_paths,
    has_abstract,
    is_erratum,
    load_journal_areas,
    load_raw_exports,
    normalize_journal_name,
)
from utils.data import count_articles, sha256, write_csv
from utils.quarters import assign_quarters
from utils.cleaning_audit import clean_corpus


def add_features(corpus):
    text = corpus.abstract.fillna("")
    patterns = {
        "em": "—",
        "en_all": "–",
        "en_numeric": r"(?<=\d)–(?=\d)",
        "curly_apostrophe": "’",
        "curly_quote": "“",
        "semicolon": ";",
        "degree_sign": "°",
        "times_sign": "×",
        "greek_alpha": "α",
        "hyphen_all": "-",
    }
    for name, pattern in patterns.items():
        corpus["count_" + name] = text.str.count(pattern)
    corpus["count_en_nonnumeric"] = corpus.count_en_all - corpus.count_en_numeric
    for name in [*patterns, "en_nonnumeric"]:
        corpus["has_" + name] = corpus["count_" + name].gt(0)
    corpus["em_dash"] = corpus.has_em
    corpus["characters"] = text.str.len()
    return corpus


def run():
    if DATASET_PATH is None or SOURCE_LIST_PATH is None:
        raise ValueError("Set DATASET_PATH and SOURCE_LIST_PATH in .env.")
    if not DATASET_PATH.is_dir() or not SOURCE_LIST_PATH.is_file():
        raise FileNotFoundError(
            "The dataset directory or source-list file does not exist."
        )
    output = RESULTS / "preparation"
    raw = load_raw_exports(DATASET_PATH)
    journals = load_journal_areas(SOURCE_LIST_PATH)
    selected = raw.assign(journal=raw.source_title.apply(normalize_journal_name))
    selected = selected[
        selected.journal.isin(journals.journal) & selected.year.between(2019, 2026)
    ]
    with_text = selected[has_abstract(selected)]
    corpus = build_corpus(raw, journals)
    raw_n = len(corpus)
    source = pd.read_csv(SOURCE_LIST_PATH, encoding="utf-8-sig")
    source["journal"] = source["Source title"].apply(normalize_journal_name)
    publishers = source.drop_duplicates("journal").set_index("journal").Publisher
    corpus["publisher"] = corpus.journal.map(publishers)
    corpus = clean_corpus(corpus, add_features)
    counts = pd.DataFrame(
        [
            ("classified_sources", len(journals)),
            ("classified_records_2019_2026", len(selected)),
            ("without_abstract", len(selected) - len(with_text)),
            ("correction_prefix", int(is_erratum(with_text).sum())),
            ("abstracts_before_cleaning", raw_n),
            ("empty_after_cleaning", raw_n - len(corpus)),
            ("abstracts", len(corpus)),
            ("represented_journals", corpus.journal.nunique()),
        ],
        columns=["stage", "count"],
    )
    write_csv(counts, output / "corpus_counts.csv")
    variants = em_dash_rule_variants(corpus.abstract)
    write_csv(variants, RESULTS / "robustness" / "character_rules.csv")
    articles = assign_quarters(add_features(corpus), verbose=False)
    articles["year"] = articles.year.astype(int)
    keep = [
        "eid",
        "year",
        "journal",
        "area",
        "publisher",
        "quarter",
        "year_quarter",
        "quarter_is_resolved",
        "ordering_basis",
        "year_is_partial",
        "characters",
        "em_dash",
    ]
    keep += [column for column in articles if column.startswith(("count_", "has_"))]
    write_csv(articles[keep], PREPARED)
    resolved = articles[articles.quarter.notna() & articles.quarter_is_resolved].copy()
    resolved["quarter"] = resolved.quarter.astype(int)
    keys = ["journal", "area", "publisher", "year"]
    write_csv(count_articles(articles, keys), DATA / "yearly_counts.csv.gz")
    write_csv(count_articles(resolved, keys + ["quarter", "year_quarter"]),
              DATA / "quarterly_counts.csv.gz")
    quarterly = resolved.groupby(["year", "quarter", "area"], as_index=False).agg(
        n_abstracts=("eid", "size"), n_with_em_dash=("em_dash", "sum")
    )
    quarterly["quarter"] = quarterly.quarter.astype(int)
    write_csv(quarterly, output / "quarterly_em_dash.csv")
    coverage = articles.assign(
        assigned=articles.quarter.notna(),
        resolved=articles.quarter.notna() & articles.quarter_is_resolved,
    )
    coverage = coverage.groupby("year", as_index=False).agg(
        n_abstracts=("eid", "size"),
        n_assigned=("assigned", "sum"),
        n_resolved=("resolved", "sum"),
    )
    write_csv(coverage, output / "quarter_coverage.csv")
    journal_counts = articles.groupby("journal").size().rename("n_abstracts")
    appendix = journals.merge(journal_counts, on="journal", how="left")
    appendix["n_abstracts"] = appendix.n_abstracts.fillna(0).astype(int)
    appendix["publisher"] = appendix.journal.map(publishers)
    write_csv(appendix, output / "journals.csv")
    titles = source.drop_duplicates("journal").set_index("journal")["Source title"]
    journal_list = appendix.assign(journal=appendix.journal.map(titles))
    journal_list = journal_list.sort_values(
        "journal", key=lambda values: values.str.casefold()
    )
    write_csv(journal_list, ROOT / "data" / "journals.csv")
    manifest = [
        {"file": str(path.relative_to(DATASET_PATH)), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in export_paths(DATASET_PATH)
    ]
    manifest.append({"file": "source-list.csv", "bytes": SOURCE_LIST_PATH.stat().st_size, "sha256": sha256(SOURCE_LIST_PATH)})
    write_csv(pd.DataFrame(manifest), output / "input_manifest.csv")
    metadata = {
        "python": platform.python_version(), "pandas": pd.__version__,
        "cleaning_sha256": sha256(ROOT / "scripts" / "utils" / "abstract_cleaning.py"),
        "input_manifest_sha256": sha256(output / "input_manifest.csv"),
        "all_abstracts_idempotence_checked": raw_n,
        "raw_text_written_to_public_outputs": False,
    }
    (output / "cleaning_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (PREPARED.parent / "cleaning_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(counts.to_string(index=False))


if __name__ == "__main__":
    run()
