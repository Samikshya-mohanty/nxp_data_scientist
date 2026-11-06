.PHONY: download data stats figures notebooks test

download:
	uv run python -m scripts.fetch

data:
	uv run python -m scripts.panel

stats:
	uv run python -m scripts.stats

figures:
	uv run python -m scripts.figures

notebooks:
	uv run marimo export html notebooks/01_statistics.py -o reports/notebooks/01_statistics.html
	uv run marimo export html notebooks/02_charts.py -o reports/notebooks/02_charts.html

test:
	uv run pytest
