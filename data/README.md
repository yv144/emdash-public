# Data

| File | Contents |
| --- | --- |
| `yearly_counts.csv.gz` | Counts by journal and year, including all eligible abstracts |
| `quarterly_counts.csv.gz` | Counts by journal and inferred quarter, restricted to resolved quarters |
| `journals.csv` | All 489 selected journals, research areas, publishers, and abstract counts |
| `validation_counts.csv` | Manual-review counts by year, Scopus indicator, and publisher judgment |

The annual counts cover 615,299 abstracts from 487 journals. The quarterly counts cover 599,052 abstracts through 2026Q2; the primary models use 569,927 through 2026Q1. Two selected journals have no eligible abstracts.

`n_abstracts` counts abstracts. `hits_*` counts abstracts containing each marker; `characters`, `em_occurrences`, and `hyphen_occurrences` sum characters and occurrences. The marker keys are defined in `scripts/config.py`. En dashes are numeric when digits immediately flank them; an abstract can contain both en-dash categories.

The manual review includes 25 Scopus-positive and 75 Scopus-negative abstracts per year, 2019–2026. `n` is the count for each pair of indicators. To estimate adjusted prevalence, multiply the publisher-positive share in each year/Scopus stratum by that stratum's corpus size, then pool the estimated counts by period.

## Preparation

`scripts/01_prepare.py` reads nested Scopus CSV/XLSX exports from `DATASET_PATH`. Required columns: `EID`, `DOI`, `Title`, `Abstract`, `Year`, `Source title`, `Volume`, `Issue`, `Art. No.`, and `Page start`. The selected journal list at `SOURCE_LIST_PATH` requires `Source title`, `Highest percentile`, and `Publisher`. Paths in `.env` may be absolute or relative to the repository.

Use the snapshot listed in `results/preparation/input_manifest.csv`. Keep its directory structure: EID deduplication retains the first record, with `correction-a` before `correction-y`, followed by sorted folders; CSV exports precede XLSX exports. The source list contains the original 99th-percentile selection.

Preparation excludes missing abstracts and titles or abstracts beginning with `Erratum` or `Correction`. It removes recognized structured headings, terminal copyright notices, and leading U+2014 separators before counting. Retained punctuation keeps its original Unicode characters. The heading and copyright rules derive from MTI Lang commit `dfd31d9d1f11ee708ab815c50750d242ddb7a3d5`; `scripts/utils/abstract_cleaning.py` contains the exact rules.

Quarter assignment uses volume, issue, article, and page ordering within journals. For partial 2026, expected output uses the median of the last five complete years and assignments stop at Q2. Resolved quarters require at least four expected ordering positions. Preparation writes article-level features and cleaning examples to `.cache/`, and aggregate diagnostics to `results/preparation/`.

## Analyses

The overall comparison uses 2019–2022 versus 2023–2026. Subgroups and marker ratios compare the pooled 2019–2022 baseline with partial 2026. Subgroup intervals use Wilson limits for proportions and Newcombe limits for differences. Field departure requires two consecutive quarters above the baseline mean quarterly percentage plus three sample standard deviations.

The primary interrupted time series uses a quasibinomial logit model with seasonal effects and an estimated breakpoint. The fixed-breakpoint refit uses Newey–West covariance (lag 3, Bartlett kernel, finite-sample adjustment, no prewhitening). Marker contrasts use the same breakpoint and joint covariance, with Holm adjustment across eight comparisons. Coefficient and counterfactual intervals condition on the estimated breakpoint.
