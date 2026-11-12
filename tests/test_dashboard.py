import importlib.util
from pathlib import Path
from types import SimpleNamespace

DASHBOARD = Path(__file__).parents[1] / "app" / "dashboard.py"


def run(**values):
    spec = importlib.util.spec_from_file_location("dashboard", DASHBOARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, defs = module.app.run(defs={name: SimpleNamespace(value=value) for name, value in values.items()})
    return defs


def test_dashboard_runs_with_its_default_filters():
    defs = run()
    assert len(defs["valid_countries"]) == 217
    assert defs["country"].value == defs["valid_countries"][0]


def test_region_filter_limits_the_country_list():
    assert len(run(region="South Asia")["valid_countries"]) == 6


def test_income_and_region_filters_work_together():
    defs = run(region="Europe & Central Asia", income="Low income")
    assert defs["valid_countries"] == []
    assert defs["country"] is None


def test_country_view_shows_income_group_region_and_tiles():
    defs = run(country="Haiti")
    assert defs["country_info"]["income_group"] == "Lower middle income"
    assert defs["country_info"]["region"] == "Latin America & Caribbean"
    assert defs["tiles"]["life_exp"]["value"] > 60


def test_a_country_with_missing_years_still_works():
    defs = run(country="West Bank and Gaza")
    assert defs["tiles"]["life_exp"]["since"] == 1990


def test_year_filter_limits_the_rows():
    defs = run(country="India", years=(2000, 2010))
    assert sorted(defs["country_rows"]["year"]) == list(range(2000, 2011))


def test_grouping_uses_income_groups():
    defs = run(group_by="Income group", measure="life_exp")
    assert defs["series"]["series"].nunique() == 4


def test_filters_apply_to_the_table():
    defs = run(region="South Asia")
    assert defs["table_rows"]["country"].nunique() == 6


def test_map_uses_the_chosen_year():
    defs = run(map_year=1960, map_measure="life_exp")
    assert set(defs["map_rows"]["year"]) == {1960}
    assert defs["map_rows"]["life_exp"].notna().sum() == 215


def test_map_follows_the_region_filter():
    defs = run(region="South Asia", map_year=2023, map_measure="fertility")
    assert defs["map_rows"]["country"].nunique() == 6


def test_map_handles_filters_with_no_countries():
    defs = run(region="North America", income="Low income")
    assert defs["map_rows"].empty

