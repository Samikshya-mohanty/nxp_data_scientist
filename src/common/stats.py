import numpy as np
import pandas as pd

from common.constants import BUCKETS, INCOME_GROUPS

SPREAD_MEASURES = {
    "standard_deviation": lambda values: values.std(),
    "iqr": lambda values: values.quantile(0.75) - values.quantile(0.25),
    "range": lambda values: values.max() - values.min(),
    "coefficient_of_variation": lambda values: values.std() / values.mean(),
}


def mean_by_year(table, column):
    years = table[table["year"].between(1960, 2023)]
    means = years.groupby(["year", "income_group"])[column].mean().unstack()
    return means.reindex(columns=INCOME_GROUPS)


def gender_gap_by_year(table):
    return mean_by_year(table, "gender_gap")


def change_summary(by_year):
    return pd.DataFrame(
        {
            "value_1960": by_year.loc[1960],
            "value_2023": by_year.loc[2023],
            "change": by_year.loc[2023] - by_year.loc[1960],
            "lowest": by_year.min(),
            "lowest_year": by_year.idxmin(),
            "highest": by_year.max(),
            "highest_year": by_year.idxmax(),
            "range": by_year.max() - by_year.min(),
            "trend_per_decade": by_year.apply(lambda gaps: np.polyfit(by_year.index, gaps, 1)[0] * 10),
        }
    )


def countries_with_both_years(table, column):
    years = table[table["year"].isin([1960, 2023])].dropna(subset=[column])
    return years[years.groupby("iso3")["year"].transform("size") == 2]


def spread_by_year(table, measure):
    years = table[table["year"].between(1960, 2023)]
    spreads = years.groupby(["year", "income_group"])["life_exp"].agg(SPREAD_MEASURES[measure]).unstack()
    return spreads.reindex(columns=INCOME_GROUPS)


def variability_changes(table):
    return pd.DataFrame(
        {measure: change_summary(spread_by_year(table, measure))["change"] for measure in SPREAD_MEASURES}
    )


def country_correlations(table):
    def correlate(country):
        ordered = country.sort_values("year")
        life_exp = ordered["life_exp"]
        fertility = ordered["fertility"]
        return pd.Series(
            {
                "pearson": life_exp.corr(fertility),
                "spearman": life_exp.corr(fertility, method="spearman"),
                "yearly_change_pearson": life_exp.diff().corr(fertility.diff()),
                "years_used": (life_exp.notna() & fertility.notna()).sum(),
            }
        )

    result = table.groupby(["iso3", "country", "income_group"]).apply(correlate).reset_index()
    result["years_used"] = result["years_used"].astype(int)
    result["strength"] = result["pearson"].abs()
    return result.sort_values("strength", ascending=False)


def gender_gap_change(table):
    both_years = countries_with_both_years(table, "gender_gap")

    means = both_years.groupby(["income_group", "year"])["gender_gap"].mean().unstack()
    result = means.rename(columns={1960: "gap_1960", 2023: "gap_2023"})
    result["change"] = result["gap_2023"] - result["gap_1960"]
    result.insert(0, "countries", both_years.groupby("income_group")["iso3"].nunique())
    return result.reindex(INCOME_GROUPS)


def country_gender_gap_change(table):
    years = table[table["year"].isin([1960, 2023])]
    gaps = years.pivot(index=["iso3", "country", "income_group"], columns="year", values="gender_gap")
    result = gaps.rename(columns={1960: "gap_1960", 2023: "gap_2023"}).rename_axis(columns=None).reset_index()
    result["change"] = result["gap_2023"] - result["gap_1960"]
    return result.sort_values("change", ascending=False)


def largest_change(changes):
    return changes.abs().idxmax()


def gender_gap_window_change(table, start_years, end_years):
    def window_mean(years):
        return table[table["year"].isin(years)].groupby("income_group")["gender_gap"].mean()

    return (window_mean(end_years) - window_mean(start_years)).reindex(INCOME_GROUPS)


def life_exp_by_year(table):
    return mean_by_year(table, "life_exp")


def bucket_labels(count):
    if count == len(BUCKETS):
        return BUCKETS
    names = [f"Bucket {number}" for number in range(1, count + 1)]
    names[0] += " (lowest)"
    names[-1] += " (highest)"
    return tuple(names)


def assign_buckets(values, labels=BUCKETS):
    ranks = values.sort_index().rank(method="first").astype(int) - 1
    positions = ranks * len(labels) // len(ranks)
    return positions.map(dict(enumerate(labels))).reindex(values.index)


def bucket_moves(table, labels=BUCKETS):
    both_years = countries_with_both_years(table, "life_exp")
    values = both_years.pivot(index=["iso3", "country"], columns="year", values="life_exp")
    moves = pd.DataFrame(
        {
            "bucket_1960": assign_buckets(values.droplevel("country")[1960], labels).values,
            "bucket_2023": assign_buckets(values.droplevel("country")[2023], labels).values,
            "life_exp_1960": values[1960].values,
            "life_exp_2023": values[2023].values,
        },
        index=values.index,
    )
    return moves.reset_index()


def bucket_counts(moves, labels=BUCKETS):
    counts = pd.crosstab(moves["bucket_1960"], moves["bucket_2023"])
    return counts.reindex(index=labels, columns=labels, fill_value=0)


ALL = "All"
GROUP_COLUMNS = {"Income group": "income_group", "Region": "region"}
MEASURES = {
    "life_exp": "Life expectancy (years)",
    "death_rate": "Death rate (per 1,000 people)",
    "fertility": "Fertility (births per woman)",
    "gender_gap": "Gender gap (women minus men, years)",
}


def filter_panel(panel, region=ALL, income_group=ALL, years=(1960, 2023)):
    rows = panel[panel["year"].between(years[0], years[1])]
    if region != ALL:
        rows = rows[rows["region"] == region]
    if income_group != ALL:
        rows = rows[rows["income_group"] == income_group]
    return rows


def countries_in(panel, region, income_group):
    return sorted(filter_panel(panel, region, income_group)["country"].unique())


def latest_and_change(rows, column):
    values = rows.dropna(subset=[column]).sort_values("year")
    if values.empty:
        return None
    first = values.iloc[0]
    last = values.iloc[-1]
    return {
        "value": float(last[column]),
        "year": int(last["year"]),
        "change": float(last[column] - first[column]),
        "since": int(first["year"]),
    }


def group_series(rows, group_by, column, countries=()):
    if group_by == "Country":
        selected = rows[rows["country"].isin(countries)]
        result = selected.rename(columns={"country": "series", column: "value"})
    else:
        key = GROUP_COLUMNS[group_by]
        means = rows.groupby([key, "year"], as_index=False)[column].mean()
        result = means.rename(columns={key: "series", column: "value"})
    return result[["series", "year", "value"]].sort_values(["series", "year"]).reset_index(drop=True)


def story_numbers(panel):
    moves = bucket_moves(panel)
    lowest, highest = BUCKETS[0], BUCKETS[-1]
    return {
        "top_of_lowest_bucket_2023": moves[moves["bucket_2023"] == lowest]["life_exp_2023"].max(),
        "bottom_of_highest_bucket_1960": moves[moves["bucket_1960"] == highest]["life_exp_1960"].min(),
        "spread_changes": variability_changes(panel)["standard_deviation"],
    }
