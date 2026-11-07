import pandas as pd

from common.constants import PROCESSED_DIR, REPORTS_DIR
from ml import forecast

PRACTICE_ORIGINS = (1990, 1995, 2000)
BASELINES = ["persistence", "trend_5", "trend_10", "trend_20"]


def practice_exams(panel):
    methods = list(forecast.METHODS)
    rows = []
    for origin in PRACTICE_ORIGINS:
        table = forecast.backtest(panel, origin, methods)
        errors = forecast.mean_absolute_errors(table, methods)
        rows.append({"origin": origin, "countries": table["iso3"].nunique(), **errors.to_dict()})
    return pd.DataFrame(rows).set_index("origin")


def baselines_on_2011_to_2023(panel):
    table = forecast.backtest(panel, 2010, BASELINES)
    errors = forecast.mean_absolute_errors(table, BASELINES)
    return pd.DataFrame([{"origin": 2010, "countries": table["iso3"].nunique(), **errors.to_dict()}]).set_index("origin")


def main():
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    REPORTS_DIR.mkdir(exist_ok=True)

    exams = practice_exams(panel)
    exams.to_csv(REPORTS_DIR / "forecast_practice_exams.csv", float_format="%.3f")
    print("Practice exams: average mistake in years, lower is better")
    print(exams.round(3).to_string())
    print(exams[list(forecast.METHODS)].mean().round(3).rename("average").to_frame().T.to_string())

    baselines = baselines_on_2011_to_2023(panel)
    baselines.to_csv(REPORTS_DIR / "forecast_baselines_2011_2023.csv", float_format="%.3f")
    print("\nSimple forecasts on 2011 to 2023. Ridge is scored here only on Day 5.")
    print(baselines.round(3).to_string())


if __name__ == "__main__":
    main()
