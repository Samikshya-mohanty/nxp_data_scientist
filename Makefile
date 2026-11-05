.PHONY: download data stats notebooks test

download:
	uv run python -m scripts.fetch

data:
	uv run python -m scripts.panel

stats:
	uv run python -m scripts.stats

notebooks:
	uv run marimo export html notebooks/01_statistics.py -o reports/notebooks/01_statistics.html

test:
	uv run pytest
