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
