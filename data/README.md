# Data

| File | Contents |
| --- | --- |
| `yearly_counts.csv.gz` | Counts by journal and year (615,299 abstracts) |
| `quarterly_counts.csv.gz` | Counts by journal and estimated quarter (599,052 abstracts) |
| `journals.csv` | 489 selected journals with area, publisher, and abstract count |
| `validation_counts.csv` | Manual check of Scopus text against publisher text |

`hits_<marker>` counts abstracts containing the marker. Markers are defined in `scripts/config.py`.

## Corpus

758,468 Scopus records, minus 134,587 without an abstract and 8,582 errata or corrections, gives 615,299 abstracts. Headings, terminal copyright notices, and leading em dashes are removed before counting; 19,642 abstracts still contain a © afterwards.

## Quarters

Scopus gives only the year. Quarters are estimated from each article's position in its journal's volume, issue, and page order. 2026 articles past June go into Q2, so the time-series models stop at 2026Q1 (569,927 abstracts).

## Validation

100 abstracts per year, 2019–2026, checked against the publisher's version: 795 of 800 agree. Adjusting for the disagreements changes the 2019–2022 to 2023–2026 increase from 1.41 to 0.86 percentage points (`results/validation/`).

## Analyses

- 2019–2022 vs 2023–2026: two-proportion z-test.
- Subgroups and markers: 2019–2022 vs first half of 2026, Wilson and Newcombe intervals.
- Time series: quasibinomial regression with an estimated breakpoint and Newey–West errors. Intervals treat the breakpoint as known.
- Markers: slope change compared with the em dash, Holm-adjusted.
- Field timing: first of two quarters above the 2019–2022 mean plus three SD.
