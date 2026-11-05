from common.constants import INCOME_GROUPS


def gender_gap_change(table):
    years = table[table["year"].isin([1960, 2023])].dropna(subset=["gender_gap"])
    both_years = years[years.groupby("iso3")["year"].transform("size") == 2]

    means = both_years.groupby(["income_group", "year"])["gender_gap"].mean().unstack()
    result = means.rename(columns={1960: "gap_1960", 2023: "gap_2023"})
    result["change"] = result["gap_2023"] - result["gap_1960"]
    result.insert(0, "countries", both_years.groupby("income_group")["iso3"].nunique())
    return result.reindex(INCOME_GROUPS)


def largest_change(changes):
    return changes.abs().idxmax()


def gender_gap_window_change(table, start_years, end_years):
    def window_mean(years):
        return table[table["year"].isin(years)].groupby("income_group")["gender_gap"].mean()

    return (window_mean(end_years) - window_mean(start_years)).reindex(INCOME_GROUPS)
