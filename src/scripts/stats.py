import pandas as pd

from common import stats
from common.constants import PROCESSED_DIR, REPORTS_DIR


def question_1(panel, aggregates):
    by_year = stats.gender_gap_by_year(panel)
    summary = stats.change_summary(by_year)
    summary["both_years_change"] = stats.gender_gap_change(panel)["change"]
    summary["weighted_change"] = stats.gender_gap_change(aggregates)["change"]
    summary["change_to_2017_19"] = stats.gender_gap_window_change(panel, (1960, 1961, 1962), (2017, 2018, 2019))
    summary["change_to_2021_23"] = stats.gender_gap_window_change(panel, (1960, 1961, 1962), (2021, 2022, 2023))
    return by_year, summary


def question_2(panel):
    by_year = stats.spread_by_year(panel, "standard_deviation")
    summary = stats.change_summary(by_year)
    both_years = stats.countries_with_both_years(panel, "life_exp")
    summary["both_years_change"] = stats.change_summary(stats.spread_by_year(both_years, "standard_deviation"))["change"]
    changes = stats.variability_changes(panel).drop(columns="standard_deviation").add_suffix("_change")
    return by_year, summary.join(changes)


def report_question_1(panel, aggregates):
    by_year, summary = question_1(panel, aggregates)
    by_year.to_csv(REPORTS_DIR / "question_1_by_year.csv", float_format="%.3f")
    summary.to_csv(REPORTS_DIR / "question_1_gender_gap.csv", float_format="%.3f")
    stats.country_gender_gap_change(panel).to_csv(
        REPORTS_DIR / "question_1_by_country.csv", index=False, float_format="%.3f"
    )
    answer = stats.largest_change(summary["change"])
    print(f"Question 1: {answer} changed the most ({summary.loc[answer, 'change']:+.2f} years).")
    print(summary.round(2).T.to_string())


def report_question_2(panel):
    by_year, summary = question_2(panel)
    by_year.to_csv(REPORTS_DIR / "question_2_by_year.csv", float_format="%.3f")
    summary.to_csv(REPORTS_DIR / "question_2_variability.csv", float_format="%.3f")
    answer = stats.largest_change(summary["change"])
    print(f"\nQuestion 2: {answer} changed the most ({summary.loc[answer, 'change']:+.2f} years of standard deviation).")
    print(summary.round(3).T.to_string())


def report_question_3(panel):
    correlations = stats.country_correlations(panel)
    correlations.to_csv(REPORTS_DIR / "question_3_correlations.csv", index=False, float_format="%.4f")
    columns = ["country", "pearson", "spearman", "yearly_change_pearson", "years_used"]
    print("\nQuestion 3: highest correlation, either sign:")
    print(correlations.head(5)[columns].round(4).to_string(index=False))
    print("\nLowest correlation, closest to zero:")
    print(correlations.tail(5).iloc[::-1][columns].round(4).to_string(index=False))
    print("\nMost positive correlation:")
    print(correlations.nlargest(5, "pearson")[columns].round(4).to_string(index=False))


def main():
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    aggregates = pd.read_csv(PROCESSED_DIR / "aggregates.csv")
    REPORTS_DIR.mkdir(exist_ok=True)

    report_question_1(panel, aggregates)
    report_question_2(panel)
    report_question_3(panel)


if __name__ == "__main__":
    main()
