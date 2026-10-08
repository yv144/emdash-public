from analysis import field_timing, markers, prevalence, robustness, subgroups, validation
from utils.data import read_counts


def main():
    yearly = read_counts()
    quarterly = read_counts(resolved=True)
    for analysis in [prevalence, subgroups]:
        analysis.run(yearly)
    for analysis in [markers, field_timing, robustness]:
        analysis.run(quarterly)
    validation.run()


if __name__ == "__main__":
    main()
