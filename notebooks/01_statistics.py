import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from wigglystuff import TangleChoice

    from common import stats
    from common.constants import PROCESSED_DIR
    from scripts.stats import question_1, question_2

    return PROCESSED_DIR, TangleChoice, mo, pd, question_1, question_2, stats


@app.cell
def _(PROCESSED_DIR, pd):
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    aggregates = pd.read_csv(PROCESSED_DIR / "aggregates.csv")
    return aggregates, panel


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Statistical analysis

    World Bank data for 217 economies, 1960 to 2023. The calculations are in `src/common/stats.py`, with tests in `tests/test_stats.py`. This notebook only displays them.

    Click an underlined choice in a sentence to change the definition. The answer changes with it, because some answers depend on the definition.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Question 1: gender gap

    **For which income group has the difference in average life expectancy of men and women changed the most between 1960 and 2023?**

    The gender gap is women's life expectancy minus men's. The headline averages it for each income group in every year from 1960 to 2023, with each country counted in every year it has data.
    """)
    return


@app.cell
def _():
    Q1_COLUMNS = {
        "all countries": "change",
        "only countries with both years": "both_years_change",
        "population weights": "weighted_change",
        "1960-62 to 2017-19 averages": "change_to_2017_19",
        "1960-62 to 2021-23 averages": "change_to_2021_23",
    }
    return (Q1_COLUMNS,)


@app.cell
def _(Q1_COLUMNS, TangleChoice, mo):
    q1_definition = mo.ui.anywidget(TangleChoice(choices=list(Q1_COLUMNS)))
    return (q1_definition,)


@app.cell
def _(aggregates, panel, question_1):
    q1_by_year, q1_summary = question_1(panel, aggregates)
    return q1_by_year, q1_summary


@app.cell
def _(Q1_COLUMNS, q1_definition, q1_summary, stats):
    q1_changes = q1_summary[Q1_COLUMNS[q1_definition.choice]]
    q1_winner = stats.largest_change(q1_changes)
    return q1_changes, q1_winner


@app.cell
def _(mo, q1_changes, q1_definition, q1_winner):
    mo.md(
        f"""
    Using {q1_definition}, **{q1_winner}** changed the most, at **{q1_changes[q1_winner]:+.2f} years**.
    """
    )
    return


@app.cell
def _(Q1_COLUMNS, mo, q1_summary):
    mo.ui.table(
        q1_summary[list(Q1_COLUMNS.values())].round(2).rename(columns={v: k for k, v in Q1_COLUMNS.items()}).reset_index(),
        selection=None,
        pagination=False,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    **Warning.** The winner depends on the definition. Upper middle income leads low income by only 0.11 years on the headline. Population weights pick lower middle income, because India, Pakistan, and Bangladesh had women living shorter lives than men in 1960. Ending before COVID picks low income.

    Lower middle income is +1.54 with all countries and +1.39 with both-years countries, because West Bank and Gaza has data only from 1990.

    Income groups are one recent World Bank label applied to every year, so these are today's groups, not the 1960 groups.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Question 2: variability

    **For which income group has variability in life expectancy at birth changed the most between 1960 and 2023?**

    Variability here is how far apart the countries in a group are in one year. The headline uses the standard deviation across countries.
    """)
    return


@app.cell
def _():
    Q2_COLUMNS = {
        "standard deviation": "change",
        "IQR": "iqr_change",
        "range": "range_change",
        "coefficient of variation": "coefficient_of_variation_change",
    }
    return (Q2_COLUMNS,)


@app.cell
def _(Q2_COLUMNS, TangleChoice, mo):
    q2_measure = mo.ui.anywidget(TangleChoice(choices=list(Q2_COLUMNS)))
    return (q2_measure,)


@app.cell
def _(panel, question_2):
    q2_by_year, q2_summary = question_2(panel)
    return q2_by_year, q2_summary


@app.cell
def _(Q2_COLUMNS, q2_measure, q2_summary, stats):
    q2_changes = q2_summary[Q2_COLUMNS[q2_measure.choice]]
    q2_winner = stats.largest_change(q2_changes)
    return q2_changes, q2_winner


@app.cell
def _(mo, q2_changes, q2_measure, q2_winner):
    mo.md(
        f"""
    Measured by {q2_measure}, **{q2_winner}** changed the most, with a change of **{q2_changes[q2_winner]:+.3f}**.
    """
    )
    return


@app.cell
def _(Q2_COLUMNS, mo, q2_summary):
    mo.ui.table(
        q2_summary[list(Q2_COLUMNS.values())].round(3).rename(columns={v: k for k, v in Q2_COLUMNS.items()}).reset_index(),
        selection=None,
        pagination=False,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    **Warning.** Variability fell in all four groups, so the largest change is a fall. Standard deviation, IQR, and range are in years. Coefficient of variation has no unit. It picks low income because it divides by the group's mean, and that mean rose from a low base.

    China's 33.4 in 1960 could inflate the starting spread. Without China, upper middle income is -3.31, and starting from 1961, 1963, or 1965 gives -3.49, -2.99, and -3.12. It wins every time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Question 3: correlation

    **Which countries have the highest correlation between fertility rate and life expectancy at birth over the years (either positive or negative)? Which countries have the lowest correlation?**

    Each country gets one Pearson correlation across its years. "Highest" means farthest from 0, either positive or negative. "Lowest" means closest to 0.
    """)
    return


@app.cell
def _(panel, stats):
    q3_correlations = stats.country_correlations(panel)
    q3_strongest = q3_correlations["country"].iloc[0]
    q3_weakest = q3_correlations["country"].iloc[-1]
    return q3_correlations, q3_strongest, q3_weakest


@app.cell
def _(mo, q3_correlations, q3_strongest, q3_weakest):
    q3_values = q3_correlations.set_index("country")["pearson"]
    mo.md(
        f"""
    **Highest:** {q3_strongest} ({q3_values[q3_strongest]:+.4f}). **Lowest:** {q3_weakest} ({q3_values[q3_weakest]:+.4f}).
    """
    )
    return


@app.cell
def _(mo, q3_correlations):
    q3_columns = ["country", "pearson", "spearman", "yearly_change_pearson", "years_used"]
    mo.vstack(
        [
            mo.md("**Highest correlation, either sign**"),
            mo.ui.table(q3_correlations.head(5)[q3_columns].round(4), selection=None, pagination=False),
            mo.md("**Lowest correlation, closest to zero**"),
            mo.ui.table(q3_correlations.tail(5).iloc[::-1][q3_columns].round(4), selection=None, pagination=False),
            mo.md("**Most positive correlation**"),
            mo.ui.table(q3_correlations.nlargest(5, "pearson")[q3_columns].round(4), selection=None, pagination=False),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    **Warning.** A strong correlation here does not show that one causes the other. Fertility fell and life expectancy rose over the same decades in most countries, and any two trending series correlate: 208 of 217 values are negative, with a median of -0.887.

    The `yearly_change_pearson` column correlates each year's change instead, which removes most of the shared trend. India falls from -0.9973 to -0.027. The median across countries is -0.001, and no country exceeds 0.9 in absolute value.
    """)
    return


if __name__ == "__main__":
    app.run()
