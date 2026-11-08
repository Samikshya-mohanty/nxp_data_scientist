import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    from common import figures
    from common.constants import PROCESSED_DIR, REPORTS_DIR

    return PROCESSED_DIR, REPORTS_DIR, figures, mo, pd


@app.cell
def _(PROCESSED_DIR, REPORTS_DIR, pd):
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    exams = pd.read_csv(REPORTS_DIR / "forecast_practice_exams.csv", index_col="origin")
    scores = pd.read_csv(REPORTS_DIR / "forecast_final_scores.csv", index_col=0)
    by_horizon = pd.read_csv(REPORTS_DIR / "forecast_errors_by_horizon.csv", index_col="horizon")
    by_income = pd.read_csv(REPORTS_DIR / "forecast_errors_by_income.csv", index_col="income_group")
    final_table = pd.read_csv(REPORTS_DIR / "forecast_2010_2023.csv")
    return by_horizon, by_income, exams, final_table, panel, scores


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Forecasting life expectancy, 2011 to 2023

    **Build a machine learning model to forecast life expectancy at birth for each country from 2010 to 2023, using only data available up to and including 2010.**

    The calculations are in `src/ml/forecast.py`, with tests in `tests/test_forecast.py`. This notebook only reads the saved results from `make forecast`. It never scores 2011 to 2023 again.

    Every forecast first removes all data after its start year, and a test replaces every value after 2010 with 999 to prove the forecasts do not change.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Choosing the model with practice exams

    Each practice exam pretends it is 1990, 1995, or 2000 and forecasts the next 13 years. The model was chosen here, before 2011 to 2023 was scored. Numbers are the average mistake in years, so lower is better.
    """)
    return


@app.cell
def _(exams, mo):
    exam_origin = mo.ui.dropdown(options=[str(origin) for origin in exams.index], value="2000", label="Practice exam")
    return (exam_origin,)


@app.cell
def _(exam_origin, exams, mo):
    exam_errors = exams.loc[int(exam_origin.value)].drop("countries").sort_values()
    mo.vstack(
        [
            exam_origin,
            mo.md(f"{int(exams.loc[int(exam_origin.value), 'countries'])} countries. Best method: **{exam_errors.index[0]}**."),
            mo.ui.table(exam_errors.round(3).rename("average mistake").reset_index(), selection=None, pagination=False),
        ]
    )
    return (exam_errors,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. The final score on 2011 to 2023

    The chosen model is gradient boosting with all five datasets and the sudden-drop rule. Bias above 0 means the forecasts were too high on average.
    """)
    return


@app.cell
def _(mo, scores):
    mo.ui.table(scores.round(3).reset_index(names="method"), selection=None, pagination=False)
    return


@app.cell
def _(by_horizon, figures):
    figures.horizon_error_chart(by_horizon[["persistence", "trend_5", "ridge", "boosting"]])
    return


@app.cell
def _(by_income, mo):
    mo.vstack(
        [
            mo.md("**Average mistake by income group.** Poorer countries are harder to forecast."),
            mo.ui.table(by_income.round(3).reset_index(), selection=None, pagination=False),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. Forecast against what happened, for any country

    The gray line is the reported value. The blue dashes are the forecast made with data up to 2010.
    """)
    return


@app.cell
def _(final_table, mo):
    country = mo.ui.dropdown(options=sorted(final_table["country"].unique()), value="Haiti", label="Country")
    return (country,)


@app.cell
def _(country, final_table, figures, mo, panel):
    country_rows = final_table[final_table["country"] == country.value]
    mo.vstack([country, figures.forecast_examples_chart(panel, final_table, [country.value])])
    return (country_rows,)


if __name__ == "__main__":
    app.run()
