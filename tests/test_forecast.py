import numpy as np
import pandas as pd
import pytest

from common.constants import PROCESSED_DIR
from ml import forecast

VALUE_COLUMNS = ["life_exp", "fertility", "death_rate", "gender_gap"]


def straight_line_panel(years=range(1960, 2000)):
    rows = []
    for iso3, start, slope in [("AAA", 40.0, 0.5), ("BBB", 60.0, 0.2), ("CCC", 50.0, 0.3)]:
        for year in years:
            rows.append(
                {
                    "iso3": iso3,
                    "year": year,
                    "life_exp": start + slope * (year - 1960),
                    "fertility": 6.0 - 0.05 * (year - 1960),
                    "death_rate": 20.0 - 0.2 * (year - 1960),
                    "gender_gap": 4.0,
                }
            )
    return pd.DataFrame(rows)


def test_make_rows_describes_each_origin_and_horizon():
    panel = straight_line_panel()
    rows = forecast.make_rows(panel, [1980])
    assert len(rows) == 3 * 13
    row = rows[(rows["iso3"] == "AAA") & (rows["horizon"] == 3)].iloc[0]
    assert row["life_exp"] == pytest.approx(50.0)
    assert row["change_5y"] == pytest.approx(2.5)
    assert row["change_10y"] == pytest.approx(5.0)
    assert row["earlier_change_5y"] == pytest.approx(2.5)
    assert row["target_year"] == 1983
    assert row["target"] == pytest.approx(1.5)


def test_training_rows_never_reach_past_the_cutoff():
    rows = forecast.training_rows(straight_line_panel(), cutoff=1990)
    assert rows["target_year"].max() == 1990
    assert rows["origin"].min() == forecast.FIRST_TRAINING_ORIGIN
    assert not rows[forecast.ALL_FEATURES + ["target"]].isna().any().any()


def test_persistence_repeats_the_origin_value():
    result = forecast.forecast(straight_line_panel(), 1980, "persistence")
    assert result[result["iso3"] == "AAA"]["predicted"].tolist() == [50.0] * 13


def test_trend_continues_a_straight_line_exactly():
    result = forecast.forecast(straight_line_panel(), 1980, "trend_10")
    row = result[(result["iso3"] == "AAA") & (result["horizon"] == 13)].iloc[0]
    assert row["target_year"] == 1993
    assert row["predicted"] == pytest.approx(40.0 + 0.5 * 33)


def test_trend_gives_no_forecast_when_a_year_in_its_window_is_missing():
    panel = straight_line_panel()
    panel.loc[(panel["iso3"] == "AAA") & (panel["year"] == 1975), "life_exp"] = None
    result = forecast.forecast(panel, 1980, "trend_10")
    assert result[result["iso3"] == "AAA"]["predicted"].isna().all()
    assert result[result["iso3"] == "BBB"]["predicted"].notna().all()


def test_smooth_shocks_replaces_a_one_year_crash_with_the_recent_median():
    panel = straight_line_panel()
    crash = (panel["iso3"] == "BBB") & (panel["year"] == 1985)
    panel.loc[crash, "life_exp"] = 40.0
    smoothed = forecast.smooth_shocks(panel)
    value = smoothed[(smoothed["iso3"] == "BBB") & (smoothed["year"] == 1985)]["life_exp"].iloc[0]
    assert value == pytest.approx(64.6)


def test_smooth_shocks_leaves_normal_years_unchanged():
    panel = straight_line_panel()
    smoothed = forecast.smooth_shocks(panel)
    merged = panel.merge(smoothed, on=["iso3", "year"], suffixes=("", "_smoothed"))
    assert (merged["life_exp"] == merged["life_exp_smoothed"]).all()


def test_smooth_shocks_ignores_a_fall_of_five_years_or_less():
    panel = straight_line_panel()
    panel.loc[(panel["iso3"] == "BBB") & (panel["year"] == 1985), "life_exp"] = 60.0
    smoothed = forecast.smooth_shocks(panel)
    assert smoothed[(smoothed["iso3"] == "BBB") & (smoothed["year"] == 1985)]["life_exp"].iloc[0] == 60.0


def test_forecast_starts_from_the_smoothed_value_after_a_crash():
    panel = straight_line_panel()
    panel.loc[(panel["iso3"] == "BBB") & (panel["year"] == 1990), "life_exp"] = 40.0
    smoothed = forecast.forecast(panel, 1990, "persistence")
    raw = forecast.forecast(panel, 1990, "persistence", smooth=False)
    assert smoothed[smoothed["iso3"] == "BBB"]["predicted"].iloc[0] == pytest.approx(65.6)
    assert raw[raw["iso3"] == "BBB"]["predicted"].iloc[0] == pytest.approx(40.0)


def test_boosting_gives_a_prediction_for_every_country_and_horizon():
    result = forecast.forecast(straight_line_panel(), 1990, "boosting")
    assert len(result) == 3 * 13
    assert np.isfinite(result["predicted"]).all()


def test_error_summary_reports_mistakes_bias_and_periods():
    table = pd.DataFrame(
        {
            "iso3": ["AAA", "AAA", "AAA"],
            "target_year": [2015, 2020, 2023],
            "horizon": [5, 10, 13],
            "model": [71.0, 70.0, 75.0],
            "actual": [70.0, 72.0, 75.0],
        }
    )
    summary = forecast.error_summary(table, ["model"]).loc["model"]
    assert summary["mae"] == pytest.approx(1.0)
    assert summary["rmse"] == pytest.approx((5 / 3) ** 0.5)
    assert summary["bias"] == pytest.approx(-1 / 3)
    assert summary["mae_2011_2019"] == pytest.approx(1.0)
    assert summary["mae_2020_2021"] == pytest.approx(2.0)
    assert summary["mae_2022_2023"] == pytest.approx(0.0)


def test_ridge_gives_a_prediction_for_every_country_and_horizon():
    result = forecast.forecast(straight_line_panel(), 1990, "ridge")
    assert len(result) == 3 * 13
    assert np.isfinite(result["predicted"]).all()


def test_backtest_scores_every_method_on_the_same_rows():
    table = forecast.backtest(straight_line_panel(), 1980, ["persistence", "trend_10"])
    assert len(table) == 3 * 13
    errors = forecast.mean_absolute_errors(table, ["persistence", "trend_10"])
    assert errors["trend_10"] == pytest.approx(0.0, abs=1e-9)
    expected_persistence = np.mean([slope * horizon for slope in (0.5, 0.2, 0.3) for horizon in range(1, 14)])
    assert errors["persistence"] == pytest.approx(expected_persistence)


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(PROCESSED_DIR / "panel.csv")


@pytest.mark.parametrize("method", list(forecast.METHODS))
def test_forecasts_from_2010_never_use_later_data(panel, method):
    poisoned = panel.copy()
    poisoned.loc[poisoned["year"] > 2010, VALUE_COLUMNS] = 999.0
    clean = forecast.forecast(panel, 2010, method)
    tampered = forecast.forecast(poisoned, 2010, method)
    pd.testing.assert_frame_equal(clean, tampered)


def test_snapshot_baseline_errors_on_2011_to_2023_match_the_earlier_test(panel):
    methods = ["persistence", "trend_5", "trend_10", "trend_20"]
    table = forecast.backtest(panel, 2010, methods, smooth=False)
    assert table["iso3"].nunique() == 217
    errors = forecast.mean_absolute_errors(table, methods)
    assert errors.to_dict() == pytest.approx(
        {"persistence": 1.849, "trend_5": 1.476, "trend_10": 1.539, "trend_20": 1.692}, abs=0.005
    )


@pytest.mark.parametrize("origin, persistence_error", [(1990, 2.289), (1995, 2.427), (2000, 2.396)])
def test_snapshot_practice_exams_match_the_earlier_test(panel, origin, persistence_error):
    methods = ["persistence", "trend_10", "ridge"]
    table = forecast.backtest(panel, origin, methods, smooth=False)
    errors = forecast.mean_absolute_errors(table, methods)
    assert errors["persistence"] == pytest.approx(persistence_error, abs=0.005)
    assert errors["ridge"] < errors["trend_10"] < errors["persistence"]


def test_snapshot_rule_and_boosting_match_the_day_5_exploration(panel):
    errors = {}
    for origin in (1990, 1995, 2000):
        table = forecast.backtest(panel, origin, ["ridge", "boosting"])
        errors[origin] = forecast.mean_absolute_errors(table, ["ridge", "boosting"])
    assert errors[1990]["boosting"] == pytest.approx(1.384, abs=0.02)
    assert errors[2000]["boosting"] == pytest.approx(1.228, abs=0.02)
    assert errors[1990]["ridge"] == pytest.approx(1.556, abs=0.02)
    average = pd.DataFrame(errors).T.mean()
    assert average["boosting"] < average["ridge"]


def test_final_table_has_2010_observed_and_2011_to_2023_forecasts(panel):
    table = forecast.final_forecast_table(panel)
    assert table["iso3"].nunique() == 217
    assert sorted(table["year"].unique()) == list(range(2010, 2024))
    observed = table[table["year"] == 2010]
    assert (observed["kind"] == "observed").all()
    haiti_2010 = panel[(panel["iso3"] == "HTI") & (panel["year"] == 2010)]["life_exp"].iloc[0]
    assert observed[observed["iso3"] == "HTI"]["life_exp"].iloc[0] == pytest.approx(haiti_2010)
    assert (table[table["year"] > 2010]["kind"] == "forecast").all()
    assert table["life_exp"].notna().all()
