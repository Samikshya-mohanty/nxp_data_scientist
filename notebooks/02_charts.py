import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from wigglystuff import TangleSlider

    from common import figures, stats
    from common.constants import PROCESSED_DIR

    return PROCESSED_DIR, TangleSlider, figures, mo, pd, stats


@app.cell
def _(PROCESSED_DIR, pd):
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    return (panel,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Data visualizations

    World Bank data for 217 economies, 1960 to 2023. The charts are built in `src/common/figures.py`, with tests in `tests/test_figures.py`. This notebook only displays them. Hover over any chart to see exact values.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Life expectancy by income group

    **Create a time-series line chart showing how life expectancy at birth has changed over the years for each income group.**

    Every group rose, and the poorest gained most: low income went from 39.8 to 64.2 years (+24.4), and high income from 65.1 to 79.8 (+14.7). The low income dip in 2009 comes largely from one country, Central African Republic.
    """)
    return


@app.cell
def _(figures, panel, stats):
    figures.income_line_chart(stats.life_exp_by_year(panel))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. World map, 2023

    **Create a world map where each country is color coded according to how high or low the life expectancy at birth is in 2023.**

    A map shows where, but it is poor at showing rank, and small states are hard to see. The ranked chart below it shows the top and bottom 10.
    """)
    return


@app.cell
def _(figures, panel):
    figures.world_map(panel)
    return


@app.cell
def _(figures, panel):
    figures.ranked_chart(panel)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. Moves between life expectancy buckets, 1960 to 2023

    **For 1960 and 2023, rank the countries and classify them into five buckets of roughly equal size. Create a Sankey diagram showing from which category in 1960 countries have moved to in 2023.**

    Buckets compare countries within one year. No country has a lower value in 2023 than in 1960, even though some moved down a bucket.
    """)
    return


@app.cell
def _(TangleSlider, mo):
    bucket_count = mo.ui.anywidget(TangleSlider(amount=5, min_value=3, max_value=7, step=1, digits=0))
    return (bucket_count,)


@app.cell
def _(bucket_count, panel, stats):
    labels = stats.bucket_labels(int(bucket_count.amount))
    moves = stats.bucket_moves(panel, labels)
    return labels, moves


@app.cell
def _(bucket_count, mo):
    mo.md(f"""
    Split the countries into {bucket_count} buckets. Drag the number to try 3 to 7. The assignment asks for 5, and only 5 uses its bucket names.
    """)
    return


@app.cell
def _(figures, labels, moves):
    figures.sankey_chart(moves, labels)
    return


@app.cell
def _(figures, labels, moves):
    figures.moves_heatmap(moves, labels)
    return


@app.cell
def _(labels, mo):
    move_from = mo.ui.dropdown(options=list(labels), value=labels[1], label="Bucket in 1960")
    return (move_from,)


@app.cell
def _(labels, mo):
    move_to = mo.ui.dropdown(options=list(labels), value=labels[-1], label="Bucket in 2023")
    return (move_to,)


@app.cell
def _(move_from, move_to, moves):
    movers = moves[(moves["bucket_1960"] == move_from.value) & (moves["bucket_2023"] == move_to.value)]
    return (movers,)


@app.cell
def _(mo, move_from, move_to, movers):
    mo.vstack(
        [
            mo.md("**Which countries made this move?** Plotly cannot select a Sankey link, so choose the move here."),
            mo.hstack([move_from, move_to], justify="start"),
            mo.md(f"{len(movers)} countries."),
            mo.ui.table(
                movers[["country", "life_exp_1960", "life_exp_2023"]].round(1),
                selection=None,
                pagination=False,
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
