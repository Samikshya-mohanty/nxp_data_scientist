import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Life expectancy dashboard")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    from common import figures, stats
    from common.constants import INCOME_GROUPS, PROCESSED_DIR, REPORTS_DIR

    return INCOME_GROUPS, PROCESSED_DIR, REPORTS_DIR, figures, mo, pd, stats


@app.cell
def _(PROCESSED_DIR, REPORTS_DIR, pd):
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    forecast_errors = pd.read_csv(REPORTS_DIR / "forecast_country_errors.csv")
    return forecast_errors, panel


@app.cell
def _(mo, panel, stats):
    region = mo.ui.dropdown(options=[stats.ALL] + sorted(panel["region"].unique()), value=stats.ALL, label="Region", full_width=True)
    return (region,)


@app.cell
def _(INCOME_GROUPS, mo, stats):
    income = mo.ui.dropdown(options=[stats.ALL] + list(INCOME_GROUPS), value=stats.ALL, label="Income group", full_width=True)
    return (income,)


@app.cell
def _(mo):
    years = mo.ui.range_slider(start=1960, stop=2023, step=1, value=[1960, 2023], label="Years", full_width=True)
    return (years,)


@app.cell
def _(income, panel, region, stats):
    valid_countries = stats.countries_in(panel, region.value, income.value)
    return (valid_countries,)


@app.cell
def _(mo, valid_countries):
    country = mo.ui.dropdown(options=valid_countries, value=valid_countries[0], label="Country", full_width=True) if valid_countries else None
    return (country,)


@app.cell
def _(mo):
    group_by = mo.ui.radio(options=["Country", "Income group", "Region"], value="Income group", label="Compare by", inline=True)
    return (group_by,)


@app.cell
def _(mo, stats):
    measure = mo.ui.dropdown(options={label: key for key, label in stats.MEASURES.items()}, value=stats.MEASURES["life_exp"], label="Measure")
    return (measure,)


@app.cell
def _(mo, valid_countries):
    compare_countries = mo.ui.multiselect(options=valid_countries, value=valid_countries[:3], label="Countries, up to 8", max_selections=8)
    return (compare_countries,)


@app.cell
def _(country, income, mo, region, years):
    no_country = mo.md("**No countries match these filters.** Change the region or income group.")
    mo.sidebar(
        [
            mo.md("## Filters"),
            region,
            income,
            country if country is not None else no_country,
            years,
            mo.md(f"{years.value[0]} to {years.value[1]}"),
        ]
    )
    return (no_country,)


@app.cell
def _(income, panel, region, stats, years):
    table_rows = stats.filter_panel(panel, region.value, income.value, tuple(years.value))
    return (table_rows,)


@app.cell
def _(country, panel, stats, years):
    country_rows = None
    country_info = None
    tiles = None
    if country is not None:
        country_rows = stats.filter_panel(panel[panel["country"] == country.value], years=tuple(years.value))
        country_info = panel[panel["country"] == country.value].iloc[0][["income_group", "region"]].to_dict()
        tiles = {column: stats.latest_and_change(country_rows, column) for column in stats.MEASURES}
    return country_info, country_rows, tiles


@app.cell
def _(country, country_info, country_rows, figures, mo, no_country, stats, tiles):
    def tile(column):
        result = tiles[column]
        if result is None:
            return mo.stat(value="No data", label=stats.MEASURES[column], bordered=True)
        return mo.stat(
            value=f"{result['value']:.1f}",
            label=f"{stats.MEASURES[column]}, {result['year']}",
            caption=f"{result['change']:+.1f} since {result['since']}",
            bordered=True,
        )

    if country is None:
        country_view = no_country
        gender_view = no_country
    else:
        country_view = mo.vstack(
            [
                mo.md(f"## {country.value}\n**Income group:** {country_info['income_group']} &nbsp;&nbsp; **Region:** {country_info['region']}"),
                mo.hstack([tile(column) for column in stats.MEASURES], justify="start", gap=1, wrap=True),
                figures.country_trends_chart(country_rows),
            ]
        )
        gender_view = mo.vstack(
            [
                mo.md(f"## {country.value}: women and men\nA gap above 0 means women can expect to live longer than men."),
                figures.gender_chart(country_rows),
            ]
        )
    return country_view, gender_view


@app.cell
def _(compare_countries, group_by, measure, stats, table_rows):
    series = stats.group_series(table_rows, group_by.value, measure.value, compare_countries.value)
    return (series,)


@app.cell
def _(compare_countries, figures, group_by, measure, mo, series, stats):
    controls = [mo.hstack([group_by, measure], justify="start", gap=2)]
    if group_by.value == "Country":
        controls.append(compare_countries)
    note = (
        "Each line is one country."
        if group_by.value == "Country"
        else "Each line is the average of its countries, with every country counted once. It is not weighted by population."
    )
    chart = (
        mo.md("Choose at least one country.")
        if series.empty
        else figures.compare_chart(series, group_by.value, stats.MEASURES[measure.value])
    )
    compare_view = mo.vstack([*controls, mo.md(note), chart])
    return (compare_view,)


@app.cell
def _(mo, table_rows):
    download = mo.download(
        data=table_rows.to_csv(index=False).encode(), filename="life_expectancy.csv", label="Download these rows as CSV"
    )
    table_view = mo.vstack(
        [
            mo.md(f"**{table_rows['country'].nunique()} countries, {len(table_rows):,} rows**, using the region, income group, and year filters."),
            download,
            mo.ui.table(table_rows.round(2).reset_index(drop=True), selection=None, page_size=20, format_mapping={"year": "{:d}"}),
        ]
    )
    return (table_view,)


@app.cell
def _(figures, forecast_errors, mo, panel, stats):
    numbers = stats.story_numbers(panel)
    worst = forecast_errors.nlargest(3, "boosting")
    worst_text = ", ".join(f"{row.country} ({row.boosting:.1f} years off)" for row in worst.itertuples())
    story_view = mo.vstack(
        [
            mo.md(
                f"""
## Life expectancy rose in every country, but sudden events still matter

1. **People live much longer.** No country has a lower value in 2023 than in 1960. The top of 2023's lowest bucket ({numbers['top_of_lowest_bucket_2023']:.1f} years) is about where 1960's highest bucket began ({numbers['bottom_of_highest_bucket_1960']:.1f} years).
2. **Countries became more alike.** The spread between countries fell in all four income groups, by {abs(numbers['spread_changes']).min():.1f} to {abs(numbers['spread_changes']).max():.1f} years.
3. **Sudden events still matter.** A forecast using data up to 2010 was off by about 1 year on average, but the largest mistakes were {worst_text}.

**Keep in mind:** income groups are today's World Bank labels applied to every year, and averages count each country once.
"""
            ),
            figures.income_line_chart(stats.life_exp_by_year(panel)),
        ]
    )
    return (story_view,)


@app.cell
def _(compare_view, country_view, gender_view, mo, story_view, table_view):
    mo.vstack(
        [
            mo.md("# Life expectancy dashboard\nWorld Bank data for 217 economies, 1960 to 2023. Use the filters on the left."),
            mo.ui.tabs(
                {
                    "Story": story_view,
                    "Country": country_view,
                    "Women and men": gender_view,
                    "Compare": compare_view,
                    "Table": table_view,
                }
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
