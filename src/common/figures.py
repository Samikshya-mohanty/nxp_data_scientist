import plotly.graph_objects as go

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


def sankey_chart(moves):
    counts = stats.bucket_counts(moves)
    top_to_bottom = list(reversed(BUCKETS))

    def node_labels(year):
        groups = moves.groupby(f"bucket_{year}")[f"life_exp_{year}"]
        return [f"{bucket} ({groups.min()[bucket]:.1f} to {groups.max()[bucket]:.1f})" for bucket in top_to_bottom]

    sources, targets, values, colors = [], [], [], []
    for start, start_bucket in enumerate(top_to_bottom):
        for end, end_bucket in enumerate(top_to_bottom):
            count = int(counts.loc[start_bucket, end_bucket])
            if count > 0:
                sources.append(start)
                targets.append(end + 5)
                values.append(count)
                colors.append(_with_opacity(theme.BUCKET_COLORS[start_bucket], 0.45))

    positions = [0.1, 0.3, 0.5, 0.7, 0.9]
    figure = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node={
                "label": node_labels(1960) + node_labels(2023),
                "x": [0.001] * 5 + [0.999] * 5,
                "y": positions * 2,
                "color": [theme.BUCKET_COLORS[bucket] for bucket in top_to_bottom] * 2,
                "pad": 14,
                "thickness": 16,
                "line": {"width": 0},
                "hovertemplate": "%{label}<br>%{value} countries<extra></extra>",
            },
            link={
                "source": sources,
                "target": targets,
                "value": values,
                "color": colors,
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
    return theme.apply_theme(
        figure,
        "How countries moved between life expectancy buckets, 1960 to 2023",
        "215 countries with both years, 43 in each bucket. Ranges in years. Buckets are relative to each year.",
    )


def moves_heatmap(moves):
    counts = stats.bucket_counts(moves)
    top_to_bottom = list(reversed(BUCKETS))
    figure = go.Figure(
        go.Heatmap(
            z=counts.loc[top_to_bottom, list(BUCKETS)].values.tolist(),
            x=list(BUCKETS),
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


def _with_opacity(hex_color, opacity):
    red, green, blue = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({red},{green},{blue},{opacity})"
