import pandas as pd
import pytest

from lifeexp import fetch


def country(iso3, iso2, name, region, income):
    return {
        "id": iso3,
        "iso2Code": iso2,
        "name": name,
        "region": {"value": region},
        "incomeLevel": {"value": income},
    }


def observation(iso2, iso3, year, value):
    return {
        "country": {"id": iso2},
        "countryiso3code": iso3,
        "date": str(year),
        "value": value,
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture
def fake_api(monkeypatch):
    def get(url, params, timeout):
        page = params["page"]
        if url.endswith("/country"):
            meta = {"page": page, "pages": 1}
            return FakeResponse(
                [
                    meta,
                    [
                        country("NAM", "NA", "Namibia", "Sub-Saharan Africa ", "Upper middle income"),
                        country("WLD", "1W", "World", "Aggregates", "Aggregates"),
                    ],
                ]
            )
        meta = {"page": page, "pages": 2, "lastupdated": "2026-10-08"}
        rows = {
            1: [observation("NA", "NAM", 2023, 67.4), observation("NA", "NAM", 1960, None)],
            2: [observation("1W", "WLD", 2023, 73.3)],
        }
        return FakeResponse([meta, rows[page]])

    monkeypatch.setattr(fetch.requests, "get", get)


def read_indicator(path):
    return pd.read_csv(path, keep_default_na=False, na_values={"value": [""]})


def test_download_writes_all_pages_of_each_indicator(fake_api, tmp_path):
    fetch.download(tmp_path)

    for indicator in fetch.INDICATORS:
        table = read_indicator(tmp_path / f"{indicator}.csv")
        assert sorted(table["iso3"].unique()) == ["NAM", "WLD"]
        assert len(table) == 3


def test_download_keeps_a_missing_value_as_missing(fake_api, tmp_path):
    fetch.download(tmp_path)

    table = read_indicator(tmp_path / f"{fetch.INDICATORS[0]}.csv")
    row = table[(table["iso3"] == "NAM") & (table["year"] == 1960)]
    assert row["value"].isna().all()


def test_download_writes_the_country_list_with_its_labels(fake_api, tmp_path):
    fetch.download(tmp_path)

    table = pd.read_csv(tmp_path / "countries.csv", keep_default_na=False)
    namibia = table[table["iso3"] == "NAM"].iloc[0]
    assert namibia["iso2"] == "NA"
    assert namibia["name"] == "Namibia"
    assert namibia["region"] == "Sub-Saharan Africa "
    assert namibia["income_group"] == "Upper middle income"


def test_download_records_the_last_update_date_of_each_indicator(fake_api, tmp_path):
    fetch.download(tmp_path)

    table = pd.read_csv(tmp_path / "last_updated.csv")
    assert set(table["indicator"]) == set(fetch.INDICATORS)
    assert set(table["last_updated"]) == {"2026-10-08"}


def test_download_twice_gives_identical_files(fake_api, tmp_path):
    fetch.download(tmp_path / "first")
    fetch.download(tmp_path / "second")

    for first in (tmp_path / "first").iterdir():
        assert first.read_bytes() == (tmp_path / "second" / first.name).read_bytes()
