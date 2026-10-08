from config import RESULTS
from utils.data import write_csv
from utils.statistics import subgroup_comparisons


def run(counts):
    output = RESULTS / "subgroups"
    areas = subgroup_comparisons(counts, "area")
    write_csv(areas, output / "all_areas.csv")
    write_csv(areas[areas.corpus_share_pct.gt(1)], output / "areas.csv")
    publishers = subgroup_comparisons(counts, "publisher")
    write_csv(publishers, output / "all_publishers.csv")
    selected = publishers[
        publishers.n_journals.ge(5)
        & publishers.n_baseline.ge(500)
        & publishers.n_comparison.ge(100)
    ]
    write_csv(selected, output / "publishers.csv")
    write_csv(subgroup_comparisons(counts, "journal"), output / "journals.csv")
