import pandas as pd
import pytest

from common import stats
from common.constants import BUCKETS, INCOME_GROUPS, PROCESSED_DIR


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


def test_gap_by_year_counts_a_country_in_every_year_it_has_data(table):
    by_year = stats.gender_gap_by_year(table)
    assert by_year.loc[1960, "Low income"] == 3.0
    assert by_year.loc[2023, "Low income"] == 38.0


def test_gap_by_year_includes_both_edge_years_and_the_years_between(table):
    by_year = stats.gender_gap_by_year(table)
    assert by_year.index.tolist() == [1960, 1990, 2023]
    assert by_year.loc[1990, "High income"] == 50.0


def test_gap_by_year_leaves_out_years_outside_the_period():
    table = pd.DataFrame(
        [
            row("AAA", "Low income", 1959, 1.0),
            row("AAA", "Low income", 1960, 2.0),
            row("AAA", "Low income", 2023, 3.0),
            row("AAA", "Low income", 2024, 4.0),
        ]
    )
    assert stats.gender_gap_by_year(table).index.tolist() == [1960, 2023]


def test_change_summary_describes_the_whole_period():
    by_year = pd.DataFrame(
        {"Low income": [2.0, 6.0, 4.0], "High income": [5.0, 1.0, 3.0]},
        index=[1960, 2000, 2023],
    )
    summary = stats.change_summary(by_year)
    low = summary.loc["Low income"]
    assert low["value_1960"] == 2.0
    assert low["value_2023"] == 4.0
    assert low["change"] == 2.0
    assert low["lowest"] == 2.0
    assert low["lowest_year"] == 1960
    assert low["highest"] == 6.0
    assert low["highest_year"] == 2000
    assert low["range"] == 4.0
    assert summary.loc["High income", "change"] == -2.0


def test_change_summary_trend_is_change_per_decade():
    by_year = pd.DataFrame({"Low income": [1.0, 7.3]}, index=[1960, 2023])
    summary = stats.change_summary(by_year)
    assert summary.loc["Low income", "trend_per_decade"] == pytest.approx(1.0)


def spread_table():
    return pd.DataFrame(
        [
            {"iso3": "AAA", "income_group": "Low income", "year": 1960, "life_exp": 50.0},
            {"iso3": "BBB", "income_group": "Low income", "year": 1960, "life_exp": 60.0},
            {"iso3": "CCC", "income_group": "Low income", "year": 1960, "life_exp": 70.0},
            {"iso3": "AAA", "income_group": "Low income", "year": 2023, "life_exp": 75.0},
            {"iso3": "BBB", "income_group": "Low income", "year": 2023, "life_exp": 76.0},
            {"iso3": "CCC", "income_group": "Low income", "year": 2023, "life_exp": 77.0},
            {"iso3": "NEW", "income_group": "Low income", "year": 2023, "life_exp": None},
        ]
    )


@pytest.mark.parametrize(
    "measure, value_1960",
    [
        ("standard_deviation", 10.0),
        ("iqr", 10.0),
        ("range", 20.0),
        ("coefficient_of_variation", 10.0 / 60.0),
    ],
)
def test_spread_by_year_measures_the_spread_across_countries(measure, value_1960):
    by_year = stats.spread_by_year(spread_table(), measure)
    assert by_year.loc[1960, "Low income"] == pytest.approx(value_1960)


def test_variability_changes_gives_each_measure_for_each_group():
    table = pd.concat(spread_table().assign(income_group=group) for group in INCOME_GROUPS)
    changes = stats.variability_changes(table)
    assert changes.loc["Low income", "standard_deviation"] == pytest.approx(-9.0)
    assert changes.loc["Low income", "range"] == pytest.approx(-18.0)


def correlation_table(rows):
    return pd.DataFrame(
        [
            {
                "iso3": iso3,
                "country": iso3.title(),
                "income_group": "Low income",
                "year": year,
                "life_exp": life_exp,
                "fertility": fertility,
            }
            for iso3, year, life_exp, fertility in rows
        ]
    )


def test_correlations_find_positive_and_negative_links_and_sort_by_strength():
    table = correlation_table(
        [
            ("NEG", 1960, 40.0, 6.0),
            ("NEG", 1961, 50.0, 4.0),
            ("NEG", 1962, 60.0, 2.0),
            ("POS", 1960, 40.0, 2.0),
            ("POS", 1961, 50.0, 3.0),
            ("POS", 1962, 60.0, 5.0),
            ("NIL", 1960, 40.0, 3.0),
            ("NIL", 1961, 50.0, 2.0),
            ("NIL", 1962, 60.0, 3.0),
        ]
    )
    result = stats.country_correlations(table)
    assert result["iso3"].tolist() == ["NEG", "POS", "NIL"]
    values = result.set_index("iso3")["pearson"]
    assert values["NEG"] == pytest.approx(-1.0)
    assert 0 < values["POS"] < 1
    assert values["NIL"] == pytest.approx(0.0)


def test_correlations_use_only_years_with_both_values():
    table = correlation_table(
        [
            ("AAA", 1960, 40.0, 6.0),
            ("AAA", 1961, 50.0, 4.0),
            ("AAA", 1962, None, 1.0),
            ("AAA", 1963, 70.0, None),
            ("AAA", 1964, 60.0, 2.0),
        ]
    )
    row = stats.country_correlations(table).iloc[0]
    assert row["years_used"] == 3
    assert row["pearson"] == pytest.approx(-1.0)


def test_correlations_report_rank_and_yearly_change_versions():
    table = correlation_table(
        [
            ("AAA", 1960, 40.0, 8.0),
            ("AAA", 1961, 41.0, 7.0),
            ("AAA", 1962, 42.0, 5.0),
            ("AAA", 1963, 43.0, 4.0),
            ("AAA", 1964, 44.0, 1.0),
        ]
    )
    row = stats.country_correlations(table).iloc[0]
    assert row["spearman"] == pytest.approx(-1.0)
    assert row["pearson"] > -1.0
    assert pd.isna(row["yearly_change_pearson"])


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


def test_snapshot_all_countries_and_all_years_answer_is_upper_middle_income(panel):
    by_year = stats.gender_gap_by_year(panel)
    assert by_year.shape == (64, 4)
    assert not by_year.isna().any().any()

    summary = stats.change_summary(by_year)
    assert summary["change"].to_dict() == pytest.approx(
        {
            "Low income": 1.56,
            "Lower middle income": 1.54,
            "Upper middle income": 1.67,
            "High income": -0.05,
        },
        abs=0.005,
    )
    assert summary["range"].to_dict() == pytest.approx(
        {
            "Low income": 1.94,
            "Lower middle income": 1.85,
            "Upper middle income": 2.23,
            "High income": 1.23,
        },
        abs=0.005,
    )
    assert summary.loc["Upper middle income", "highest_year"] == 2020
    assert stats.largest_change(summary["change"]) == "Upper middle income"
    assert stats.largest_change(summary["range"]) == "Upper middle income"
    assert stats.largest_change(summary["trend_per_decade"]) == "Upper middle income"


def test_snapshot_question_2_standard_deviation_answer(panel):
    changes = stats.variability_changes(panel)
    assert changes["standard_deviation"].to_dict() == pytest.approx(
        {
            "Low income": -2.16,
            "Lower middle income": -1.44,
            "Upper middle income": -3.77,
            "High income": -2.73,
        },
        abs=0.005,
    )
    assert stats.largest_change(changes["standard_deviation"]) == "Upper middle income"
    assert stats.largest_change(changes["iqr"]) == "Upper middle income"
    assert stats.largest_change(changes["range"]) == "Upper middle income"
    assert stats.largest_change(changes["coefficient_of_variation"]) == "Low income"


def test_snapshot_question_2_both_years_check_matches_the_earlier_test(panel):
    both_years = stats.countries_with_both_years(panel, "life_exp")
    changes = stats.change_summary(stats.spread_by_year(both_years, "standard_deviation"))["change"]
    assert changes.to_dict() == pytest.approx(
        {
            "Low income": -2.16,
            "Lower middle income": -1.40,
            "Upper middle income": -3.77,
            "High income": -2.72,
        },
        abs=0.01,
    )


def test_snapshot_question_3_strongest_and_weakest_countries(panel):
    result = stats.country_correlations(panel)
    assert len(result) == 217
    assert result["country"].head(3).tolist() == ["India", "Brunei Darussalam", "Ghana"]
    assert result["country"].tail(2).tolist() == ["Eswatini", "Belarus"]
    values = result.set_index("country")["pearson"]
    assert values["India"] == pytest.approx(-0.9973, abs=0.00005)
    assert values["Belarus"] == pytest.approx(0.0204, abs=0.00005)
    assert values["Zimbabwe"] == pytest.approx(0.3452, abs=0.00005)
    assert (result["pearson"] < 0).sum() == 208
    assert (result["pearson"] > 0).sum() == 9


def test_snapshot_both_years_check_is_upper_middle_income(panel):
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


def test_life_exp_by_year_averages_each_group_in_every_year():
    table = pd.DataFrame(
        [
            {"iso3": "AAA", "income_group": "Low income", "year": 1960, "life_exp": 40.0},
            {"iso3": "BBB", "income_group": "Low income", "year": 1960, "life_exp": 50.0},
            {"iso3": "BBB", "income_group": "Low income", "year": 2023, "life_exp": 70.0},
            {"iso3": "CCC", "income_group": "Low income", "year": 2023, "life_exp": None},
        ]
    )
    by_year = stats.life_exp_by_year(table)
    assert by_year.loc[1960, "Low income"] == 45.0
    assert by_year.loc[2023, "Low income"] == 70.0
    assert list(by_year.columns) == list(INCOME_GROUPS)


def test_assign_buckets_splits_into_five_equal_named_groups():
    values = pd.Series(range(10), index=[f"C{i}" for i in range(10)], dtype=float)
    buckets = stats.assign_buckets(values)
    assert buckets.value_counts().to_dict() == {bucket: 2 for bucket in BUCKETS}
    assert buckets["C0"] == "Very low life expectancy"
    assert buckets["C9"] == "Very high life expectancy"


def test_assign_buckets_keeps_sizes_roughly_equal_when_they_cannot_be_exact():
    values = pd.Series(range(12), index=[f"C{i:02d}" for i in range(12)], dtype=float)
    sizes = stats.assign_buckets(values).value_counts()
    assert sizes.max() - sizes.min() <= 1
    assert sizes.sum() == 12


def test_assign_buckets_breaks_ties_by_country_code():
    values = pd.Series([50.0] * 5, index=["EEE", "AAA", "DDD", "BBB", "CCC"])
    buckets = stats.assign_buckets(values)
    assert buckets["AAA"] == "Very low life expectancy"
    assert buckets["EEE"] == "Very high life expectancy"


def test_bucket_moves_uses_only_countries_with_both_years():
    rows = [
        {"iso3": f"C{i}", "country": f"Country {i}", "year": year, "life_exp": float(i) + (year - 1960)}
        for i in range(5)
        for year in (1960, 2023)
    ]
    rows.append({"iso3": "NEW", "country": "New", "year": 2023, "life_exp": 99.0})
    moves = stats.bucket_moves(pd.DataFrame(rows))
    assert "NEW" not in moves["iso3"].tolist()
    assert len(moves) == 5
    first = moves.set_index("iso3").loc["C0"]
    assert first["bucket_1960"] == "Very low life expectancy"
    assert first["country"] == "Country 0"
    assert first["life_exp_2023"] == 63.0


def test_snapshot_bucket_moves_match_the_earlier_test(panel):
    moves = stats.bucket_moves(panel)
    assert len(moves) == 215
    assert set(moves["bucket_1960"].value_counts()) == {43}
    assert set(moves["bucket_2023"].value_counts()) == {43}

    counts = stats.bucket_counts(moves)
    assert list(counts.index) == list(BUCKETS)
    assert list(counts.columns) == list(BUCKETS)
    assert counts.values.tolist() == [
        [25, 11, 3, 4, 0],
        [14, 15, 8, 4, 2],
        [4, 13, 14, 9, 3],
        [0, 4, 14, 17, 8],
        [0, 0, 4, 9, 30],
    ]
    assert (counts.values > 0).sum() == 21
    assert sum(counts.iloc[i, i] for i in range(5)) == 101


def test_snapshot_biggest_bucket_movers_match_the_earlier_test(panel):
    moves = stats.bucket_moves(panel).set_index("country")
    for country in ("United Arab Emirates", "Bahrain"):
        assert moves.loc[country, "bucket_1960"] == "Low life expectancy"
        assert moves.loc[country, "bucket_2023"] == "Very high life expectancy"
    for country in ("China", "Iran, Islamic Rep.", "Maldives", "Oman"):
        assert moves.loc[country, "bucket_1960"] == "Very low life expectancy"
        assert moves.loc[country, "bucket_2023"] == "High life expectancy"


def test_bucket_labels_use_the_assignment_names_for_five_buckets():
    assert stats.bucket_labels(5) == BUCKETS
    assert stats.bucket_labels(3) == ("Bucket 1 (lowest)", "Bucket 2", "Bucket 3 (highest)")


def test_assign_buckets_can_use_another_number_of_buckets():
    values = pd.Series(range(9), index=[f"C{i}" for i in range(9)], dtype=float)
    labels = stats.bucket_labels(3)
    buckets = stats.assign_buckets(values, labels)
    assert buckets.value_counts().to_dict() == {label: 3 for label in labels}
    assert buckets["C8"] == "Bucket 3 (highest)"
