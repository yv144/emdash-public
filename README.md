# Em dash prevalence in scientific abstracts

Code and aggregate data for *From indicator to stereotype: the life cycle of the em dash in 600,000 scientific abstracts*.

615,299 Scopus abstracts from 487 journals, 2019 to mid-2026.

![Quarterly em dash prevalence](figures/figure_6.png)

## Reproduce

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and R.

```bash
uv sync --locked
Rscript -e 'install.packages(c("dplyr", "segmented", "sandwich", "lmtest"), repos="https://cloud.r-project.org")'
uv run python scripts/02_analyze.py
Rscript scripts/03_models.R
uv run python scripts/04_figures.py
```

R versions used are in [session.txt](results/time_series/session.txt).

Tests: `PYTHONPATH=scripts uv run python -m unittest discover -s tests`

## Rebuild counts from Scopus exports

Raw exports are not included. With your own copy:

```bash
cp .env.example .env  # set DATASET_PATH and SOURCE_LIST_PATH
uv run python scripts/01_prepare.py
```

See [data/README.md](data/README.md) for methods and limitations.
