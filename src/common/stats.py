import numpy as np
import pandas as pd

from common.constants import INCOME_GROUPS


def gender_gap_by_year(table):
    years = table[table["year"].between(1960, 2023)]
    means = years.groupby(["year", "income_group"])["gender_gap"].mean().unstack()
    return means.reindex(columns=INCOME_GROUPS)


def gender_gap_summary(by_year):
    return pd.DataFrame(
        {
            "gap_1960": by_year.loc[1960],
            "gap_2023": by_year.loc[2023],
            "change": by_year.loc[2023] - by_year.loc[1960],
            "lowest": by_year.min(),
            "lowest_year": by_year.idxmin(),
            "highest": by_year.max(),
            "highest_year": by_year.idxmax(),
            "range": by_year.max() - by_year.min(),
            "trend_per_decade": by_year.apply(lambda gaps: np.polyfit(by_year.index, gaps, 1)[0] * 10),
        }
    )


def gender_gap_change(table):
    years = table[table["year"].isin([1960, 2023])].dropna(subset=["gender_gap"])
    both_years = years[years.groupby("iso3")["year"].transform("size") == 2]

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
