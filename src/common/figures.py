import plotly.graph_objects as go
from plotly.subplots import make_subplots

from common import stats, theme
from common.constants import BUCKETS

UNMAPPED_COUNTRIES = ("Channel Islands", "San Marino", "Kosovo")


def income_line_chart(by_year):
    figure = go.Figure()
    for group in by_year.columns:
        figure.add_trace(
            go.Scatter(
                x=by_year.index,
                y=by_year[group],
                name=group,
                mode="lines",
                line={"color": theme.INCOME_COLORS[group], "width": 2},
                hovertemplate="%{y:.1f} years<extra>%{fullData.name}</extra>",
            )
        )
        figure.add_annotation(
            x=2023,
            y=by_year.loc[2023, group],
            text=group,
            xanchor="left",
            xshift=8,
            showarrow=False,
            font={"color": theme.TEXT, "size": 12},
        )
    figure.add_vrect(
        x0=2020,
        x1=2021,
        fillcolor=theme.BAND,
        line_width=0,
        layer="below",
        annotation_text="COVID years",
        annotation_position="bottom left",
        annotation_font={"color": theme.MUTED, "size": 11},
    )
    figure.update_layout(
        width=1100,
        height=620,
        margin={"l": 70, "r": 170, "t": 140, "b": 60},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.02, "x": 0, "yanchor": "bottom"},
    )
    figure.update_xaxes(
        range=[1960, 2023], showgrid=False, linecolor=theme.GRID, ticks="outside", tickcolor=theme.GRID, dtick=10
    )
    figure.update_yaxes(title="Life expectancy at birth (years)", gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(
        figure,
        "Life expectancy at birth by income group, 1960 to 2023",
        "Mean of countries, each counted once. Income groups are the current World Bank labels.",
    )


def world_map(panel):
    values = panel[panel["year"] == 2023].dropna(subset=["life_exp"])
    unmapped = values[values["country"].isin(UNMAPPED_COUNTRIES)]
    note = ", ".join(f"{row.country} ({row.life_exp:.1f})" for row in unmapped.itertuples())

    figure = go.Figure(
        go.Choropleth(
            locations=values["iso3"],
            z=values["life_exp"],
            locationmode="ISO-3",
            text=values["country"],
            colorscale=theme.SEQUENTIAL,
            marker={"line": {"color": theme.SURFACE, "width": 0.4}},
            colorbar={"title": "Years", "thickness": 12, "len": 0.6, "outlinewidth": 0},
            hovertemplate="%{text}<br>%{z:.1f} years<extra></extra>",
        )
    )
    figure.update_geos(
        resolution=50,
        projection_type="equal earth",
        showframe=False,
        showcoastlines=False,
        showland=True,
        landcolor=theme.NO_DATA,
        showocean=False,
        bgcolor=theme.SURFACE,
        lataxis_range=[-58, 85],
    )
    figure.add_annotation(
        text=f"These places have no shape on this map: {note}. Gray means no data.",
        x=0,
        y=-0.02,
        xref="paper",
        yref="paper",
        xanchor="left",
        showarrow=False,
        font={"color": theme.MUTED, "size": 12},
    )
    figure.update_layout(width=1100, height=600, margin={"l": 10, "r": 10, "t": 70, "b": 40})
    return theme.apply_theme(figure, "Life expectancy at birth in 2023", "Darker means higher.")


def ranked_chart(panel):
    values = panel[panel["year"] == 2023].dropna(subset=["life_exp"])
    top = values.nlargest(10, "life_exp")
    bottom = values.nsmallest(10, "life_exp").iloc[::-1]
    ranked = [*top.itertuples(), *bottom.itertuples()]

    figure = go.Figure(
        go.Bar(
            x=[row.life_exp for row in ranked],
            y=[row.country for row in ranked],
            orientation="h",
            marker={"color": theme.BAR},
            text=[f"{row.life_exp:.1f}" for row in ranked],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>%{x:.1f} years<extra></extra>",
        )
    )
    figure.update_layout(width=800, height=640, margin={"l": 190, "r": 50, "t": 90, "b": 50}, bargap=0.35)
    figure.update_xaxes(title="Life expectancy at birth in 2023 (years)", range=[0, 95], gridcolor=theme.GRID, zeroline=False)
    figure.update_yaxes(autorange="reversed", showgrid=False)
    return theme.apply_theme(figure, "Highest and lowest life expectancy in 2023", "Top 10 above, bottom 10 below.")


def sankey_chart(moves, labels=BUCKETS):
    counts = stats.bucket_counts(moves, labels)
    top_to_bottom = list(reversed(labels))
    colors = theme.bucket_colors(labels)
    size = len(labels)

    def node_labels(year):
        groups = moves.groupby(f"bucket_{year}")[f"life_exp_{year}"]
        return [f"{bucket} ({groups.min()[bucket]:.1f} to {groups.max()[bucket]:.1f})" for bucket in top_to_bottom]

    sources, targets, values, link_colors = [], [], [], []
    for start, start_bucket in enumerate(top_to_bottom):
        for end, end_bucket in enumerate(top_to_bottom):
            count = int(counts.loc[start_bucket, end_bucket])
            if count > 0:
                sources.append(start)
                targets.append(end + size)
                values.append(count)
                link_colors.append(_with_opacity(colors[start_bucket], 0.45))

    positions = [(index + 0.5) / size for index in range(size)]
    figure = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node={
                "label": node_labels(1960) + node_labels(2023),
                "x": [0.001] * size + [0.999] * size,
                "y": positions * 2,
                "color": [colors[bucket] for bucket in top_to_bottom] * 2,
                "pad": 14,
                "thickness": 16,
                "line": {"width": 0},
                "hovertemplate": "%{label}<br>%{value} countries<extra></extra>",
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": link_colors,
                "hovertemplate": "%{source.label}<br>to %{target.label}<br>%{value} countries<extra></extra>",
            },
            textfont={"color": theme.TEXT, "size": 12},
        )
    )
    for x, text in ((0, "1960"), (1, "2023")):
        figure.add_annotation(
            x=x, y=1.03, xref="paper", yref="paper", text=f"<b>{text}</b>", showarrow=False, font={"size": 14}
        )
    figure.update_layout(width=1200, height=760, margin={"l": 30, "r": 30, "t": 130, "b": 30})
    sizes = moves["bucket_1960"].value_counts()
    size_text = f"{sizes.min()}" if sizes.min() == sizes.max() else f"{sizes.min()} to {sizes.max()}"
    return theme.apply_theme(
        figure,
        "How countries moved between life expectancy buckets, 1960 to 2023",
        f"{len(moves)} countries with both years, {size_text} in each bucket. "
        "Ranges in years. Buckets are relative to each year.",
    )


def moves_heatmap(moves, labels=BUCKETS):
    counts = stats.bucket_counts(moves, labels)
    top_to_bottom = list(reversed(labels))
    figure = go.Figure(
        go.Heatmap(
            z=counts.loc[top_to_bottom, list(labels)].values.tolist(),
            x=list(labels),
            y=top_to_bottom,
            colorscale=theme.SEQUENTIAL,
            texttemplate="%{z}",
            showscale=False,
            xgap=2,
            ygap=2,
            hovertemplate="1960: %{y}<br>2023: %{x}<br>%{z} countries<extra></extra>",
        )
    )
    figure.update_layout(width=900, height=620, margin={"l": 200, "r": 30, "t": 90, "b": 130})
    figure.update_xaxes(title="Bucket in 2023", tickangle=-20)
    figure.update_yaxes(title="Bucket in 1960", autorange="reversed")
    return theme.apply_theme(figure, "Number of countries in each move, 1960 to 2023", "Diagonal cells stayed in the same bucket.")


def _spread_apart(values, gap):
    ordered = values.sort_values()
    positions = {}
    previous = None
    for name, value in ordered.items():
        position = value if previous is None else max(value, previous + gap)
        positions[name] = position
        previous = position
    return positions


def _with_opacity(rgb_color, opacity):
    return rgb_color.replace("rgb(", "rgba(").replace(")", f", {opacity})")


METHOD_NAMES = {
    "persistence": "Stay the same",
    "trend_5": "5-year trend",
    "trend_10": "10-year trend",
    "trend_20": "20-year trend",
    "ridge": "Ridge",
    "boosting": "Boosting (chosen)",
}


def horizon_error_chart(by_horizon):
    figure = go.Figure()
    grays = iter(["#9d9b95", "#7a7873", "#5c5a56", "#3f3e3b"])
    label_y = _spread_apart(by_horizon.iloc[-1], gap=0.09)
    for method in by_horizon.columns:
        chosen = method == "boosting"
        color = theme.BAR if chosen else next(grays)
        figure.add_trace(
            go.Scatter(
                x=by_horizon.index,
                y=by_horizon[method],
                name=method,
                mode="lines+markers",
                line={"color": color, "width": 3 if chosen else 2},
                marker={"size": 6},
                hovertemplate="%{x} years ahead<br>%{y:.2f} years off<extra>" + METHOD_NAMES[method] + "</extra>",
            )
        )
        figure.add_annotation(
            x=by_horizon.index[-1],
            y=label_y[method],
            text=METHOD_NAMES[method],
            xanchor="left",
            xshift=8,
            showarrow=False,
            font={"color": theme.TEXT, "size": 12},
        )
    figure.update_layout(width=1000, height=560, margin={"l": 70, "r": 170, "t": 100, "b": 60}, showlegend=False)
    figure.update_xaxes(
        title="Years ahead of 2010", dtick=1, range=[0.6, by_horizon.index[-1] + 0.3], showgrid=False, linecolor=theme.GRID
    )
    figure.update_yaxes(title="Average mistake (years)", rangemode="tozero", gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(
        figure,
        "Forecast mistakes grow with years ahead",
        "Forecasts made from 2010 for 2011 to 2023, averaged over 217 countries. Lower is better.",
    )


def forecast_examples_chart(panel, final_table, countries):
    columns = 2 if len(countries) > 1 else 1
    rows = (len(countries) + columns - 1) // columns
    figure = make_subplots(rows=rows, cols=columns, subplot_titles=countries, vertical_spacing=0.14)
    for index, country in enumerate(countries):
        row, column = index // columns + 1, index % columns + 1
        actual = panel[(panel["country"] == country) & (panel["year"] >= 1990)]
        predicted = final_table[(final_table["country"] == country) & (final_table["kind"] == "forecast")]
        figure.add_trace(
            go.Scatter(
                x=actual["year"],
                y=actual["life_exp"],
                name="Actual",
                mode="lines",
                line={"color": theme.MUTED, "width": 2},
                showlegend=index == 0,
                hovertemplate="%{x}: %{y:.1f} years<extra>Actual</extra>",
            ),
            row=row,
            col=column,
        )
        figure.add_trace(
            go.Scatter(
                x=predicted["year"],
                y=predicted["life_exp"],
                name="Forecast from 2010",
                mode="lines",
                line={"color": theme.BAR, "width": 2, "dash": "dash"},
                showlegend=index == 0,
                hovertemplate="%{x}: %{y:.1f} years<extra>Forecast</extra>",
            ),
            row=row,
            col=column,
        )
    figure.add_vline(x=2010, line={"color": theme.GRID, "width": 1})
    figure.update_layout(
        width=1100,
        height=360 * rows + 40,
        margin={"l": 60, "r": 30, "t": 120, "b": 80},
        legend={"orientation": "h", "y": -0.06, "x": 0, "yanchor": "top"},
    )
    figure.update_xaxes(showgrid=False, linecolor=theme.GRID)
    figure.update_yaxes(gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(
        figure,
        "Forecast from 2010 against what happened",
        "Gray is the reported value. Blue dashes are the boosting forecast made with data up to 2010.",
    )


def country_trends_chart(rows):
    ordered = rows.sort_values("year")
    panels = [
        ("life_exp", "Life expectancy", "Life expectancy (years)"),
        ("death_rate", "Death rate", "Death rate (per 1,000 people)"),
        ("fertility", "Fertility", "Fertility (births per woman)"),
    ]
    figure = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=[title for _, _, title in panels]
    )
    for row, (column, name, _) in enumerate(panels, start=1):
        figure.add_trace(
            go.Scatter(
                x=ordered["year"],
                y=ordered[column],
                name=name,
                mode="lines",
                connectgaps=False,
                line={"color": theme.BAR, "width": 2},
                hovertemplate="%{x}: %{y:.2f}<extra>" + name + "</extra>",
            ),
            row=row,
            col=1,
        )
    figure.update_layout(height=720, margin={"l": 60, "r": 30, "t": 40, "b": 40}, showlegend=False, hovermode="x unified")
    figure.update_xaxes(showgrid=False, linecolor=theme.GRID)
    figure.update_yaxes(gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(figure, "")


def gender_chart(rows):
    ordered = rows.sort_values("year")
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
        subplot_titles=["Life expectancy of women and men (years)", "Difference between women and men (years)"],
    )
    lines = [("life_exp_female", "Women", "#1c5cab", 1), ("life_exp_male", "Men", "#eb6834", 1), ("gender_gap", "Gap (women minus men)", theme.MUTED, 2)]
    for column, name, color, row in lines:
        figure.add_trace(
            go.Scatter(
                x=ordered["year"],
                y=ordered[column],
                name=name,
                mode="lines",
                connectgaps=False,
                line={"color": color, "width": 2},
                hovertemplate="%{x}: %{y:.2f} years<extra>" + name + "</extra>",
            ),
            row=row,
            col=1,
        )
    figure.add_hline(y=0, line={"color": theme.MUTED, "width": 1}, row=2, col=1)
    figure.update_layout(
        height=620,
        margin={"l": 60, "r": 30, "t": 40, "b": 40},
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.08, "x": 0, "yanchor": "top"},
    )
    figure.update_xaxes(showgrid=False, linecolor=theme.GRID)
    figure.update_yaxes(gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(figure, "")


def compare_chart(series, group_by, value_label):
    figure = go.Figure()
    last_rows = series.dropna(subset=["value"]).sort_values("year").groupby("series").tail(1).set_index("series")
    span = max(series["value"].max() - series["value"].min(), 1.0)
    label_y = _spread_apart(last_rows["value"], gap=span * 0.035)
    for name, rows in series.groupby("series", sort=False):
        figure.add_trace(
            go.Scatter(
                x=rows["year"],
                y=rows["value"],
                name=name,
                mode="lines",
                connectgaps=False,
                line={"color": theme.series_color(name, group_by), "width": 2},
                hovertemplate="%{y:.2f}<extra>" + name + "</extra>",
            )
        )
        if name in last_rows.index:
            figure.add_annotation(
                x=last_rows.loc[name, "year"],
                y=label_y[name],
                text=name,
                xanchor="left",
                xshift=8,
                showarrow=False,
                font={"color": theme.TEXT, "size": 11},
            )
    figure.update_layout(
        height=560,
        margin={"l": 60, "r": 360, "t": 40, "b": 50},
        hovermode="x unified",
        showlegend=False,
    )
    figure.update_xaxes(showgrid=False, linecolor=theme.GRID, range=[series["year"].min(), series["year"].max()])
    figure.update_yaxes(title=value_label, gridcolor=theme.GRID, zeroline=False)
    return theme.apply_theme(figure, "")


def measure_map(panel, rows, column, value_label):
    values = rows.dropna(subset=[column])
    if column == "gender_gap":
        limit = panel[column].abs().quantile(0.99)
        scale = {"colorscale": theme.DIVERGING, "zmin": -limit, "zmax": limit, "zmid": 0}
    else:
        scale = {
            "colorscale": theme.SEQUENTIAL,
            "zmin": panel[column].quantile(0.01),
            "zmax": panel[column].quantile(0.99),
        }
    figure = go.Figure(
        go.Choropleth(
            locations=values["iso3"],
            z=values[column],
            locationmode="ISO-3",
            text=values["country"],
            marker={"line": {"color": theme.SURFACE, "width": 0.4}},
            colorbar={"title": value_label, "thickness": 12, "len": 0.7, "outlinewidth": 0},
            hovertemplate="%{text}<br>%{z:.2f}<extra></extra>",
            **scale,
        )
    )
    figure.update_geos(
        resolution=50,
        projection_type="equal earth",
        showframe=False,
        showcoastlines=False,
        showland=True,
        landcolor=theme.NO_DATA,
        showocean=False,
        bgcolor=theme.SURFACE,
        lataxis_range=[-58, 85],
    )
    figure.update_layout(height=560, margin={"l": 10, "r": 10, "t": 20, "b": 10})
    return theme.apply_theme(figure, "")
