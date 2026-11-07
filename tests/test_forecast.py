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
    table = forecast.backtest(panel, 2010, methods)
    assert table["iso3"].nunique() == 217
    errors = forecast.mean_absolute_errors(table, methods)
    assert errors.to_dict() == pytest.approx(
        {"persistence": 1.849, "trend_5": 1.476, "trend_10": 1.539, "trend_20": 1.692}, abs=0.005
    )


@pytest.mark.parametrize("origin, persistence_error", [(1990, 2.289), (1995, 2.427), (2000, 2.396)])
def test_snapshot_practice_exams_match_the_earlier_test(panel, origin, persistence_error):
    methods = ["persistence", "trend_10", "ridge"]
    table = forecast.backtest(panel, origin, methods)
    errors = forecast.mean_absolute_errors(table, methods)
    assert errors["persistence"] == pytest.approx(persistence_error, abs=0.005)
    assert errors["ridge"] < errors["trend_10"] < errors["persistence"]
