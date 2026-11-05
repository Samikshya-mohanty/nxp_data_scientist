import pandas as pd
import pytest

from common import stats
from common.constants import PROCESSED_DIR


def row(iso3, income_group, year, gender_gap):
    return {"iso3": iso3, "income_group": income_group, "year": year, "gender_gap": gender_gap}


@pytest.fixture
def table():
    return pd.DataFrame(
        [
            row("AAA", "Low income", 1960, 2.0),
            row("AAA", "Low income", 2023, 5.0),
            row("BBB", "Low income", 1960, 4.0),
            row("BBB", "Low income", 2023, 9.0),
            row("NEW", "Low income", 1960, None),
            row("NEW", "Low income", 2023, 100.0),
            row("CCC", "High income", 1960, 8.0),
            row("CCC", "High income", 1990, 50.0),
            row("CCC", "High income", 2023, 5.0),
        ]
    )


def test_gender_gap_change_averages_each_group_for_each_year(table):
    result = stats.gender_gap_change(table)
    low = result.loc["Low income"]
    assert low["gap_1960"] == 3.0
    assert low["gap_2023"] == 7.0
    assert low["change"] == 4.0


def test_gender_gap_change_skips_countries_without_both_years(table):
    result = stats.gender_gap_change(table)
    assert result.loc["Low income", "countries"] == 2


def test_gender_gap_change_ignores_the_years_in_between(table):
    result = stats.gender_gap_change(table)
    assert result.loc["High income", "change"] == -3.0


def test_gender_gap_change_lists_groups_from_low_to_high_income(table):
    result = stats.gender_gap_change(table)
    assert result.dropna().index.tolist() == ["Low income", "High income"]


def test_largest_change_compares_size_and_ignores_the_sign():
    changes = pd.Series({"Low income": 2.0, "High income": -3.0})
    assert stats.largest_change(changes) == "High income"


def test_window_change_averages_all_values_in_each_window():
    table = pd.DataFrame(
        [
            row("AAA", "Low income", 1960, 1.0),
            row("AAA", "Low income", 1961, 3.0),
            row("AAA", "Low income", 2022, 6.0),
            row("BBB", "Low income", 2023, 10.0),
        ]
    )
    result = stats.gender_gap_window_change(table, (1960, 1961), (2022, 2023))
    assert result["Low income"] == 6.0


def test_country_change_gives_one_row_per_country_with_largest_rise_first(table):
    named = table.assign(country=table["iso3"].str.title())
    result = stats.country_gender_gap_change(named)
    assert result["iso3"].tolist() == ["BBB", "AAA", "CCC", "NEW"]
    assert result["change"].tolist()[:3] == [5.0, 3.0, -3.0]


def test_country_change_stays_blank_without_both_years(table):
    named = table.assign(country=table["iso3"].str.title())
    result = stats.country_gender_gap_change(named).set_index("iso3")
    assert pd.isna(result.loc["NEW", "gap_1960"])
    assert result.loc["NEW", "gap_2023"] == 100.0
    assert pd.isna(result.loc["NEW", "change"])


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(PROCESSED_DIR / "panel.csv")


def test_snapshot_country_changes_cover_every_country(panel):
    result = stats.country_gender_gap_change(panel)
    assert len(result) == 217
    assert result["change"].notna().sum() == 215
    assert set(result[result["change"].isna()]["country"]) == {"Israel", "West Bank and Gaza"}


def test_snapshot_country_changes_average_to_the_group_changes(panel):
    countries = stats.country_gender_gap_change(panel)
    groups = stats.gender_gap_change(panel)
    averages = countries.groupby("income_group")["change"].mean().reindex(groups.index)
    assert averages.tolist() == pytest.approx(groups["change"].tolist())


@pytest.fixture(scope="module")
def aggregates():
    return pd.read_csv(PROCESSED_DIR / "aggregates.csv")


def test_snapshot_equal_weight_answer_is_upper_middle_income(panel):
    result = stats.gender_gap_change(panel)
    assert result["change"].to_dict() == pytest.approx(
        {
            "Low income": 1.56,
            "Lower middle income": 1.39,
            "Upper middle income": 1.67,
            "High income": -0.05,
        },
        abs=0.005,
    )
    assert result["countries"].tolist() == [25, 46, 59, 85]
    assert stats.largest_change(result["change"]) == "Upper middle income"


def test_snapshot_population_weighted_answer_is_lower_middle_income(aggregates):
    result = stats.gender_gap_change(aggregates)
    assert result["change"].to_dict() == pytest.approx(
        {
            "Low income": 1.27,
            "Lower middle income": 3.53,
            "Upper middle income": 1.81,
            "High income": -0.28,
        },
        abs=0.005,
    )
    assert stats.largest_change(result["change"]) == "Lower middle income"


def test_snapshot_window_ending_before_covid_picks_low_income(panel):
    result = stats.gender_gap_window_change(panel, (1960, 1961, 1962), (2017, 2018, 2019))
    assert result.to_dict() == pytest.approx(
        {
            "Low income": 1.82,
            "Lower middle income": 1.22,
            "Upper middle income": 1.65,
            "High income": 0.04,
        },
        abs=0.005,
    )
    assert stats.largest_change(result) == "Low income"
