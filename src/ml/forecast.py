import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HORIZONS = range(1, 14)
FIRST_TRAINING_ORIGIN = 1970
LIFE_EXP_FEATURES = ["life_exp", "change_5y", "change_10y", "earlier_change_5y"]
ALL_FEATURES = LIFE_EXP_FEATURES + ["fertility", "fertility_change_5y", "death_rate", "gender_gap"]
KEYS = ["iso3", "origin", "horizon", "target_year"]
SHOCK_YEARS = 5.0
FINAL_METHOD = "boosting"
FINAL_ORIGIN = 2010


def smooth_shocks(known):
    wide = known.pivot(index="iso3", columns="year", values="life_exp")
    before = wide.T.shift(1).rolling(3).median().T
    recent = wide.T.rolling(3).median().T
    smoothed = wide.where(~(wide < before - SHOCK_YEARS), recent)
    values = smoothed.stack().rename("life_exp").reset_index()
    return known.drop(columns="life_exp").merge(values, on=["iso3", "year"], how="left")


def make_rows(known, origins):
    wide = {
        column: known.pivot(index="iso3", columns="year", values=column).reindex(columns=range(1940, 2040))
        for column in ["life_exp", "fertility", "death_rate", "gender_gap"]
    }
    life_exp = wide["life_exp"]
    fertility = wide["fertility"]

    frames = []
    for origin in origins:
        features = pd.DataFrame(
            {
                "life_exp": life_exp[origin],
                "change_5y": life_exp[origin] - life_exp[origin - 5],
                "change_10y": life_exp[origin] - life_exp[origin - 10],
                "earlier_change_5y": life_exp[origin - 5] - life_exp[origin - 10],
                "fertility": fertility[origin],
                "fertility_change_5y": fertility[origin] - fertility[origin - 5],
                "death_rate": wide["death_rate"][origin],
                "gender_gap": wide["gender_gap"][origin],
            }
        )
        for horizon in HORIZONS:
            frames.append(
                features.assign(
                    origin=origin,
                    horizon=horizon,
                    target_year=origin + horizon,
                    target=life_exp[origin + horizon] - life_exp[origin],
                )
            )
    return pd.concat(frames).reset_index()[KEYS + ALL_FEATURES + ["target"]]


def training_rows(known, cutoff):
    rows = make_rows(known, range(FIRST_TRAINING_ORIGIN, cutoff))
    rows = rows[rows["target_year"] <= cutoff]
    return rows.dropna(subset=ALL_FEATURES + ["target"])


def persistence(known, rows, origin):
    return pd.Series(0.0, index=rows.index)


def trend(span):
    def predict(known, rows, origin):
        years = range(origin - span, origin + 1)
        window = known.pivot(index="iso3", columns="year", values="life_exp").reindex(columns=years)
        centered_years = np.array(years) - np.mean(years)
        slopes = (window.sub(window.mean(axis=1), axis=0) * centered_years).sum(axis=1, skipna=False)
        slopes = slopes / (centered_years**2).sum()
        return rows["horizon"] * rows["iso3"].map(slopes)

    return predict


def design(rows, features):
    values = rows[features]
    interactions = values.mul(rows["horizon"], axis=0).add_suffix("_x_horizon")
    return pd.concat([values, rows[["horizon"]], interactions], axis=1)


def ridge(features, alpha=10.0):
    def predict(known, rows, origin):
        train = training_rows(known, origin)
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
        model.fit(design(train, features), train["target"])
        complete = rows.dropna(subset=features)
        return pd.Series(model.predict(design(complete, features)), index=complete.index).reindex(rows.index)

    return predict


def boosting(features):
    def predict(known, rows, origin):
        train = training_rows(known, origin)
        columns = features + ["horizon"]
        model = HistGradientBoostingRegressor(random_state=0)
        model.fit(train[columns], train["target"])
        return pd.Series(model.predict(rows[columns]), index=rows.index)

    return predict


METHODS = {
    "persistence": persistence,
    "trend_5": trend(5),
    "trend_10": trend(10),
    "trend_20": trend(20),
    "ridge_life_exp_only": ridge(LIFE_EXP_FEATURES),
    "ridge": ridge(ALL_FEATURES),
    "boosting_life_exp_only": boosting(LIFE_EXP_FEATURES),
    "boosting": boosting(ALL_FEATURES),
}


def forecast(panel, origin, method, smooth=True):
    known = panel[panel["year"] <= origin]
    if smooth:
        known = smooth_shocks(known)
    rows = make_rows(known, [origin])
    change = METHODS[method](known, rows, origin)
    return rows[KEYS].assign(predicted=rows["life_exp"] + change)


def backtest(panel, origin, methods, smooth=True):
    table = forecast(panel, origin, methods[0], smooth)[KEYS]
    for method in methods:
        table[method] = forecast(panel, origin, method, smooth)["predicted"].values
    actual = panel.set_index(["iso3", "year"])["life_exp"]
    table["actual"] = actual.reindex(pd.MultiIndex.from_frame(table[["iso3", "target_year"]])).values
    return table.dropna().reset_index(drop=True)


def mean_absolute_errors(table, methods):
    return table[methods].sub(table["actual"], axis=0).abs().mean()



def error_summary(table, methods):
    errors = table[methods].sub(table["actual"], axis=0)
    periods = {"2011_2019": (2011, 2019), "2020_2021": (2020, 2021), "2022_2023": (2022, 2023)}
    summary = pd.DataFrame(
        {
            "mae": errors.abs().mean(),
            "rmse": (errors**2).mean() ** 0.5,
            "bias": errors.mean(),
            **{
                f"mae_{name}": errors[table["target_year"].between(first, last)].abs().mean()
                for name, (first, last) in periods.items()
            },
        }
    )
    return summary


def final_forecast_table(panel):
    predicted = forecast(panel, FINAL_ORIGIN, FINAL_METHOD)
    forecasts = predicted.rename(columns={"target_year": "year", "predicted": "life_exp"})[["iso3", "year", "life_exp"]]
    observed = panel[panel["year"] == FINAL_ORIGIN][["iso3", "year", "life_exp"]]
    table = pd.concat([observed.assign(kind="observed"), forecasts.assign(kind="forecast")])
    names = panel.drop_duplicates("iso3").set_index("iso3")[["country", "income_group"]]
    actual = panel.set_index(["iso3", "year"])["life_exp"].rename("actual")
    table = table.join(names, on="iso3").join(actual, on=["iso3", "year"])
    columns = ["iso3", "country", "income_group", "year", "kind", "life_exp", "actual"]
    return table[columns].sort_values(["iso3", "year"]).reset_index(drop=True)
