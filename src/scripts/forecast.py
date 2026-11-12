import pandas as pd

from common import figures
from common.constants import INCOME_GROUPS, PROCESSED_DIR, REPORTS_DIR
from ml import forecast
from scripts.figures import FIGURES_DIR, save

PRACTICE_ORIGINS = (1990, 1995, 2000)
METHODS = ["persistence", "trend_5", "trend_10", "trend_20", "ridge", "boosting"]


def practice_exams(panel):
    methods = list(forecast.METHODS)
    rows = []
    for origin in PRACTICE_ORIGINS:
        table = forecast.backtest(panel, origin, methods)
        errors = forecast.mean_absolute_errors(table, methods)
        rows.append({"origin": origin, "countries": table["iso3"].nunique(), **errors.to_dict()})
    return pd.DataFrame(rows).set_index("origin")


def final_scores(panel):
    table = forecast.backtest(panel, forecast.FINAL_ORIGIN, METHODS)
    table["boosting_without_rule"] = forecast.backtest(panel, forecast.FINAL_ORIGIN, ["boosting"], smooth=False)[
        "boosting"
    ].values
    income = panel.drop_duplicates("iso3").set_index("iso3")["income_group"]
    table["income_group"] = table["iso3"].map(income)
    return table


def country_errors(table):
    errors = table[METHODS].sub(table["actual"], axis=0).abs()
    by_country = errors.groupby(table["iso3"]).mean()
    names = table.drop_duplicates("iso3").set_index("iso3")
    return by_country.join(names[["income_group"]]).sort_values("boosting")


def main():
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    REPORTS_DIR.mkdir(exist_ok=True)
    names = panel.drop_duplicates("iso3").set_index("iso3")["country"]

    exams = practice_exams(panel)
    exams.to_csv(REPORTS_DIR / "forecast_practice_exams.csv", float_format="%.3f")
    print("Practice exams: average mistake in years, lower is better")
    print(exams.round(3).to_string())

    table = final_scores(panel)
    scored = METHODS + ["boosting_without_rule"]
    summary = forecast.error_summary(table, scored)
    summary.to_csv(REPORTS_DIR / "forecast_final_scores.csv", float_format="%.3f")
    print(f"\nFinal scores on 2011 to 2023, {table['iso3'].nunique()} countries. The chosen model is boosting.")
    print(summary.round(3).to_string())

    by_horizon = table[scored].sub(table["actual"], axis=0).abs().groupby(table["horizon"]).mean()
    by_horizon.to_csv(REPORTS_DIR / "forecast_errors_by_horizon.csv", float_format="%.3f")

    by_income = table[METHODS].sub(table["actual"], axis=0).abs().groupby(table["income_group"]).mean()
    by_income = by_income.reindex(INCOME_GROUPS)
    by_income.to_csv(REPORTS_DIR / "forecast_errors_by_income.csv", float_format="%.3f")
    print("\nAverage mistake by income group")
    print(by_income.round(3).to_string())

    countries = country_errors(table)
    countries.insert(0, "country", countries.index.map(names))
    countries.to_csv(REPORTS_DIR / "forecast_country_errors.csv", float_format="%.3f")
    print("\nBest 5 countries for boosting")
    print(countries.head(5)[["country", "boosting", "trend_10", "persistence"]].round(2).to_string(index=False))
    print("\nWorst 5 countries for boosting")
    print(countries.tail(5)[["country", "boosting", "trend_10", "persistence"]].round(2).to_string(index=False))
    for baseline in ("persistence", "trend_10", "ridge"):
        wins = (countries["boosting"] < countries[baseline]).sum()
        print(f"Boosting beats {baseline} in {wins} of {len(countries)} countries")

    without_haiti = table[table["iso3"] != "HTI"]
    print(
        "\nWithout Haiti, boosting mistake:",
        round(forecast.mean_absolute_errors(without_haiti, ["boosting"])["boosting"], 3),
    )

    final_table = forecast.final_forecast_table(panel)
    final_table.to_csv(REPORTS_DIR / "forecast_2010_2023.csv", index=False, float_format="%.3f")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    save(figures.horizon_error_chart(by_horizon[["persistence", "trend_5", "ridge", "boosting"]]), "forecast_by_horizon")
    examples = ["Australia", "India", "Haiti", "South Sudan"]
    save(figures.forecast_examples_chart(panel, final_table, examples), "forecast_examples")
    print(f"\nSaved the 2010 to 2023 forecast table: {len(final_table)} rows, {final_table['iso3'].nunique()} countries")


if __name__ == "__main__":
    main()
