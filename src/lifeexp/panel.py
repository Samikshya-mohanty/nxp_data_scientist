import pandas as pd

from lifeexp.fetch import INDICATORS, RAW_DIR

PROCESSED_DIR = RAW_DIR.parent / "processed"
LAST_YEAR = 2023
INCOME_GROUPS = ("Low income", "Lower middle income", "Upper middle income", "High income")
COLUMNS = [
    "iso3",
    "country",
    "region",
    "income_group",
    "year",
    "life_exp",
    "life_exp_male",
    "life_exp_female",
    "gender_gap",
    "death_rate",
    "fertility",
]


def read_countries(raw_dir):
    # keep_default_na=False stops pandas reading Namibia's iso2 code, NA, as missing.
    countries = pd.read_csv(raw_dir / "countries.csv", keep_default_na=False)
    countries["region"] = countries["region"].str.strip()
    return countries.rename(columns={"name": "country"})


def read_indicators(raw_dir):
    tables = [
        pd.read_csv(raw_dir / f"{indicator}.csv", keep_default_na=False, na_values={"value": [""]})
        .drop(columns="iso3")
        .rename(columns={"value": column})
        .set_index(["iso2", "year"])
        for indicator, column in INDICATORS.items()
    ]
    return pd.concat(tables, axis=1).reset_index()


def build(raw_dir, processed_dir):
    processed_dir.mkdir(parents=True, exist_ok=True)

    values = read_indicators(raw_dir)
    values = values[values["year"] <= LAST_YEAR]
    values["gender_gap"] = values["life_exp_female"] - values["life_exp_male"]
    table = read_countries(raw_dir).merge(values, on="iso2")

    panel = table[table["region"] != "Aggregates"]
    panel[COLUMNS].sort_values(["iso3", "year"]).to_csv(processed_dir / "panel.csv", index=False)

    aggregates = table[table["country"].isin(INCOME_GROUPS)].assign(income_group=lambda t: t["country"])
    aggregates[COLUMNS].sort_values(["iso3", "year"]).to_csv(processed_dir / "aggregates.csv", index=False)


if __name__ == "__main__":
    build(RAW_DIR, PROCESSED_DIR)
