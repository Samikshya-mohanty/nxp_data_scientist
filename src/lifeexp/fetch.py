from pathlib import Path

import pandas as pd
import requests

API_URL = "https://api.worldbank.org/v2"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
INDICATORS = {
    "SP.DYN.LE00.IN": "life_exp",
    "SP.DYN.LE00.MA.IN": "life_exp_male",
    "SP.DYN.LE00.FE.IN": "life_exp_female",
    "SP.DYN.CDRT.IN": "death_rate",
    "SP.DYN.TFRT.IN": "fertility",
}


def fetch_pages(path):
    records = []
    page = 1
    pages = 1
    while page <= pages:
        response = requests.get(
            f"{API_URL}/{path}",
            params={"format": "json", "per_page": 20000, "page": page},
            timeout=60,
        )
        response.raise_for_status()
        meta, rows = response.json()
        records += rows
        pages = meta["pages"]
        page += 1
    return meta, records


def country_table(records):
    rows = [
        {
            "iso3": record["id"],
            "iso2": record["iso2Code"],
            "name": record["name"],
            "region": record["region"]["value"],
            "income_group": record["incomeLevel"]["value"],
        }
        for record in records
    ]
    return pd.DataFrame(rows).sort_values("iso3")


def indicator_table(records):
    rows = [
        {
            "iso2": record["country"]["id"],
            "iso3": record["countryiso3code"],
            "year": int(record["date"]),
            "value": record["value"],
        }
        for record in records
    ]
    return pd.DataFrame(rows).sort_values(["iso2", "year"])


def download(raw_dir):
    raw_dir.mkdir(parents=True, exist_ok=True)

    _, countries = fetch_pages("country")
    country_table(countries).to_csv(raw_dir / "countries.csv", index=False)

    updates = []
    for indicator in INDICATORS:
        meta, records = fetch_pages(f"country/all/indicator/{indicator}")
        indicator_table(records).to_csv(raw_dir / f"{indicator}.csv", index=False)
        updates.append({"indicator": indicator, "last_updated": meta["lastupdated"]})
    pd.DataFrame(updates).to_csv(raw_dir / "last_updated.csv", index=False)


if __name__ == "__main__":
    download(RAW_DIR)
