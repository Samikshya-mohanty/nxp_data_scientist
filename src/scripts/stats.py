import pandas as pd

from common import stats
from common.constants import PROCESSED_DIR, REPORTS_DIR


def question_1(panel, aggregates):
    result = stats.gender_gap_change(panel)
    result["weighted_change"] = stats.gender_gap_change(aggregates)["change"]
    result["change_to_2017_19"] = stats.gender_gap_window_change(panel, (1960, 1961, 1962), (2017, 2018, 2019))
    result["change_to_2021_23"] = stats.gender_gap_window_change(panel, (1960, 1961, 1962), (2021, 2022, 2023))
    return result


def main():
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    aggregates = pd.read_csv(PROCESSED_DIR / "aggregates.csv")

    result = question_1(panel, aggregates)
    REPORTS_DIR.mkdir(exist_ok=True)
    result.to_csv(REPORTS_DIR / "question_1_gender_gap.csv", float_format="%.3f")

    answer = stats.largest_change(result["change"])
    print(f"Question 1: {answer} changed the most ({result.loc[answer, 'change']:+.2f} years).")
    print(result.round(2).to_string())


if __name__ == "__main__":
    main()
