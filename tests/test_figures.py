import pandas as pd
import pytest

from common import figures, stats
from common.constants import BUCKETS, INCOME_GROUPS, PROCESSED_DIR


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(PROCESSED_DIR / "panel.csv")


def test_line_chart_has_one_line_per_income_group_for_all_64_years(panel):
    figure = figures.income_line_chart(stats.life_exp_by_year(panel))
    assert [trace.name for trace in figure.data] == list(INCOME_GROUPS)
    for trace in figure.data:
        assert len(trace.x) == 64
        assert list(trace.x)[0] == 1960
        assert list(trace.x)[-1] == 2023


def test_line_chart_values_are_the_group_means(panel):
    figure = figures.income_line_chart(stats.life_exp_by_year(panel))
    expected = panel[panel["year"] == 2023].groupby("income_group")["life_exp"].mean()
    for trace in figure.data:
        assert list(trace.y)[-1] == pytest.approx(expected[trace.name])


def test_line_chart_labels_each_line_directly_and_uses_one_y_axis(panel):
    figure = figures.income_line_chart(stats.life_exp_by_year(panel))
    labels = {annotation.text for annotation in figure.layout.annotations}
    assert set(INCOME_GROUPS) <= labels
    assert "yaxis2" not in figure.layout.to_plotly_json()


def test_line_colors_follow_the_income_order_and_never_repeat(panel):
    figure = figures.income_line_chart(stats.life_exp_by_year(panel))
    assert len({trace.line.color for trace in figure.data}) == 4


def test_world_map_colors_every_country_by_its_2023_value(panel):
    figure = figures.world_map(panel)
    trace = figure.data[0]
    assert trace.type == "choropleth"
    assert trace.locationmode == "ISO-3"
    assert len(trace.locations) == 217
    values = dict(zip(trace.locations, trace.z))
    expected = panel[(panel["year"] == 2023) & (panel["iso3"] == "JPN")]["life_exp"].iloc[0]
    assert values["JPN"] == pytest.approx(expected)


def test_world_map_uses_the_detailed_shapes_and_one_color_ramp(panel):
    figure = figures.world_map(panel)
    assert figure.layout.geo.resolution == 50
    assert figure.data[0].colorscale[0][1] != figure.data[0].colorscale[-1][1]
    assert len(figure.data[0].colorscale) >= 2


def test_world_map_names_the_places_it_cannot_draw(panel):
    figure = figures.world_map(panel)
    text = " ".join(annotation.text for annotation in figure.layout.annotations)
    for country in ("Channel Islands", "San Marino", "Kosovo"):
        assert country in text


def test_ranked_chart_shows_the_top_and_bottom_ten(panel):
    figure = figures.ranked_chart(panel)
    countries = list(figure.data[0].y)
    assert len(countries) == 20
    values = panel[panel["year"] == 2023].dropna(subset=["life_exp"])
    assert values.nlargest(1, "life_exp")["country"].iloc[0] in countries
    assert values.nsmallest(1, "life_exp")["country"].iloc[0] in countries


def test_sankey_has_ten_nodes_with_the_exact_bucket_names(panel):
    figure = figures.sankey_chart(stats.bucket_moves(panel))
    labels = list(figure.data[0].node.label)
    assert len(labels) == 10
    for bucket in BUCKETS:
        assert sum(label.startswith(f"{bucket} (") for label in labels) == 2


def test_sankey_links_carry_every_country_and_all_21_moves(panel):
    figure = figures.sankey_chart(stats.bucket_moves(panel))
    link = figure.data[0].link
    assert sum(link.value) == 215
    assert len(link.value) == 21
    assert all(source < 5 <= target for source, target in zip(link.source, link.target))


def test_sankey_fixes_very_high_at_the_top_on_both_sides(panel):
    figure = figures.sankey_chart(stats.bucket_moves(panel))
    trace = figure.data[0]
    assert trace.arrangement == "fixed"
    labels = list(trace.node.label)
    for start in (0, 5):
        side_labels = labels[start : start + 5]
        side_y = list(trace.node.y)[start : start + 5]
        top = side_labels[side_y.index(min(side_y))]
        bottom = side_labels[side_y.index(max(side_y))]
        assert top.startswith("Very high life expectancy")
        assert bottom.startswith("Very low life expectancy")
    assert max(list(trace.node.x)[:5]) < min(list(trace.node.x)[5:])


def test_heatmap_shows_a_number_in_each_of_the_25_cells(panel):
    figure = figures.moves_heatmap(stats.bucket_moves(panel))
    trace = figure.data[0]
    assert sum(sum(row) for row in trace.z) == 215
    assert trace.texttemplate == "%{z}"
    assert len(trace.z) == 5 and len(trace.z[0]) == 5


def test_sankey_and_heatmap_follow_another_number_of_buckets(panel):
    labels = stats.bucket_labels(3)
    moves = stats.bucket_moves(panel, labels)
    sankey = figures.sankey_chart(moves, labels).data[0]
    assert len(sankey.node.label) == 6
    assert sum(sankey.link.value) == 215
    assert all(source < 3 <= target for source, target in zip(sankey.link.source, sankey.link.target))
    heatmap = figures.moves_heatmap(moves, labels).data[0]
    assert len(heatmap.z) == 3


def test_horizon_error_chart_has_one_line_per_method_and_labels_them():
    by_horizon = pd.DataFrame(
        {"persistence": [0.5, 3.0], "boosting": [0.3, 1.5]}, index=pd.Index([1, 13], name="horizon")
    )
    figure = figures.horizon_error_chart(by_horizon)
    assert [trace.name for trace in figure.data] == ["persistence", "boosting"]
    assert list(figure.data[1].y) == [0.3, 1.5]
    labels = {annotation.text for annotation in figure.layout.annotations}
    assert {"Stay the same", "Boosting (chosen)"} <= labels


def test_horizon_error_chart_keeps_close_labels_apart():
    by_horizon = pd.DataFrame({"ridge": [1.40], "boosting": [1.40]}, index=pd.Index([13], name="horizon"))
    figure = figures.horizon_error_chart(by_horizon)
    positions = sorted(annotation.y for annotation in figure.layout.annotations)
    assert positions[1] - positions[0] >= 0.09


def test_forecast_examples_chart_shows_actual_and_forecast_for_each_country(panel):
    table = pd.DataFrame(
        {
            "country": ["India"] * 3,
            "year": [2010, 2011, 2012],
            "kind": ["observed", "forecast", "forecast"],
            "life_exp": [67.2, 67.6, 68.0],
        }
    )
    figure = figures.forecast_examples_chart(panel, table, ["India"])
    names = [trace.name for trace in figure.data]
    assert names == ["Actual", "Forecast from 2010"]
    assert list(figure.data[1].x) == [2011, 2012]
    assert min(figure.data[0].x) == 1990


def one_country(panel, name):
    return panel[panel["country"] == name]


def test_country_chart_has_three_measures_on_a_shared_year_axis(panel):
    figure = figures.country_trends_chart(one_country(panel, "India"))
    assert [trace.name for trace in figure.data] == ["Life expectancy", "Death rate", "Fertility"]
    assert figure.layout.xaxis.matches == figure.layout.xaxis2.matches or figure.layout.xaxis2.matches == "x3"
    assert all(len(trace.x) == 64 for trace in figure.data)


def test_country_chart_keeps_missing_years_as_gaps(panel):
    figure = figures.country_trends_chart(one_country(panel, "West Bank and Gaza"))
    assert figure.data[0].connectgaps is False
    assert pd.isna(list(figure.data[0].y)[0])


def test_gender_chart_shows_men_women_and_the_gap(panel):
    figure = figures.gender_chart(one_country(panel, "Pakistan"))
    assert [trace.name for trace in figure.data] == ["Women", "Men", "Gap (women minus men)"]
    gap = dict(zip(figure.data[2].x, figure.data[2].y))
    assert gap[1960] == pytest.approx(-3.98, abs=0.005)


def test_compare_chart_draws_one_labelled_line_per_series():
    series = pd.DataFrame(
        {"series": ["Low income", "Low income", "High income", "High income"], "year": [2000, 2023] * 2, "value": [50.0, 60.0, 75.0, 80.0]}
    )
    figure = figures.compare_chart(series, "Income group", "Life expectancy (years)")
    assert sorted(trace.name for trace in figure.data) == ["High income", "Low income"]
    assert {"Low income", "High income"} <= {annotation.text for annotation in figure.layout.annotations}


def test_series_colors_do_not_change_when_another_series_is_removed():
    both = pd.DataFrame({"series": ["Kenya", "Peru"], "year": [2000, 2000], "value": [50.0, 60.0]})
    only_peru = both[both["series"] == "Peru"]
    color_with_both = {t.name: t.line.color for t in figures.compare_chart(both, "Country", "x").data}["Peru"]
    color_alone = figures.compare_chart(only_peru, "Country", "x").data[0].line.color
    assert color_with_both == color_alone


def test_measure_map_colors_countries_by_the_chosen_year_and_measure(panel):
    figure = figures.measure_map(panel, panel[panel["year"] == 1960], "fertility", "Fertility (births per woman)")
    trace = figure.data[0]
    assert trace.type == "choropleth"
    values = dict(zip(trace.locations, trace.z))
    expected = panel[(panel["year"] == 1960) & (panel["iso3"] == "BRA")]["fertility"].iloc[0]
    assert values["BRA"] == pytest.approx(expected)
    assert figure.layout.geo.resolution == 50


def test_measure_map_leaves_out_countries_without_a_value(panel):
    figure = figures.measure_map(panel, panel[panel["year"] == 1960], "life_exp", "Life expectancy (years)")
    assert len(figure.data[0].locations) == 215
    assert "ISR" not in list(figure.data[0].locations)


def test_measure_map_keeps_the_same_color_scale_in_every_year(panel):
    early = figures.measure_map(panel, panel[panel["year"] == 1960], "life_exp", "x").data[0]
    late = figures.measure_map(panel, panel[panel["year"] == 2023], "life_exp", "x").data[0]
    assert (early.zmin, early.zmax) == (late.zmin, late.zmax)


def test_measure_map_centers_the_gender_gap_on_zero(panel):
    trace = figures.measure_map(panel, panel[panel["year"] == 1960], "gender_gap", "x").data[0]
    assert trace.zmid == 0
    assert len({color for _, color in trace.colorscale}) == 3

