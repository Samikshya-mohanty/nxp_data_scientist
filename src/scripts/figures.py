import pandas as pd

from common import figures, stats
from common.constants import PROCESSED_DIR, REPORTS_DIR

FIGURES_DIR = REPORTS_DIR / "figures"


def save(figure, name):
    figure.write_html(FIGURES_DIR / f"{name}.html", include_plotlyjs="cdn", div_id=name)
    figure.write_image(FIGURES_DIR / f"{name}.png", scale=2)
    print(f"Saved {name}")


def main():
    panel = pd.read_csv(PROCESSED_DIR / "panel.csv")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    moves = stats.bucket_moves(panel)
    moves.to_csv(REPORTS_DIR / "bucket_moves.csv", index=False, float_format="%.3f")

    save(figures.income_line_chart(stats.life_exp_by_year(panel)), "income_line_chart")
    save(figures.world_map(panel), "world_map")
    save(figures.ranked_chart(panel), "ranked_chart")
    save(figures.sankey_chart(moves), "sankey")
    save(figures.moves_heatmap(moves), "moves_heatmap")


if __name__ == "__main__":
    main()
