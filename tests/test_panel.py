import pandas as pd
import pytest

from lifeexp import panel

COUNTRIES = """iso3,iso2,name,region,income_group
HTI,HT,Haiti,Latin America & Caribbean ,Lower middle income
NAM,NA,Namibia,Sub-Saharan Africa ,Upper middle income
WLD,1W,World,Aggregates,Aggregates
HIC,XD,High income,Aggregates,Aggregates
"""

VALUES = {
    "SP.DYN.LE00.IN": 65.0,
    "SP.DYN.LE00.MA.IN": 60.0,
    "SP.DYN.LE00.FE.IN": 70.0,
    "SP.DYN.CDRT.IN": 8.0,
    "SP.DYN.TFRT.IN": 3.0,
}


@pytest.fixture
def raw_dir(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "countries.csv").write_text(COUNTRIES)
    for indicator, value in VALUES.items():
        lines = ["iso2,iso3,year,value"]
        for iso2, iso3 in [("HT", "HTI"), ("NA", "NAM"), ("1W", "WLD"), ("XD", "")]:
            for year in (1960, 2023, 2024):
                lines.append(f"{iso2},{iso3},{year},{value}")
        lines.append("HT,HTI,1961,")
        (raw / f"{indicator}.csv").write_text("\n".join(lines) + "\n")
    return raw


@pytest.fixture
def built(raw_dir, tmp_path):
    processed = tmp_path / "processed"
    panel.build(raw_dir, processed)
    return pd.read_csv(processed / "panel.csv"), pd.read_csv(processed / "aggregates.csv")


def test_panel_keeps_only_real_countries_including_namibia(built):
    table, _ = built
    assert sorted(table["country"].unique()) == ["Haiti", "Namibia"]


def test_panel_stops_at_2023(built):
    table, _ = built
    assert sorted(table["year"].unique()) == [1960, 1961, 2023]


def test_panel_strips_spaces_from_region_names(built):
    table, _ = built
    regions = table.set_index("iso3")["region"].to_dict()
    assert regions == {"HTI": "Latin America & Caribbean", "NAM": "Sub-Saharan Africa"}


def test_panel_has_one_column_per_indicator_and_a_gender_gap(built):
    table, _ = built
    row = table[(table["iso3"] == "HTI") & (table["year"] == 2023)].iloc[0]
    assert row["income_group"] == "Lower middle income"
    assert row["life_exp"] == 65.0
    assert row["life_exp_male"] == 60.0
    assert row["life_exp_female"] == 70.0
    assert row["death_rate"] == 8.0
    assert row["fertility"] == 3.0
    assert row["gender_gap"] == 10.0


def test_panel_keeps_a_missing_value_as_missing(built):
    table, _ = built
    row = table[(table["iso3"] == "HTI") & (table["year"] == 1961)].iloc[0]
    assert pd.isna(row["life_exp"])


def test_aggregates_hold_only_income_groups_in_the_panel_columns(built):
    table, aggregates = built
    assert list(aggregates.columns) == list(table.columns)
    assert aggregates["income_group"].unique().tolist() == ["High income"]
    assert sorted(aggregates["year"].unique()) == [1960, 2023]
    assert (aggregates["gender_gap"] == 10.0).all()
