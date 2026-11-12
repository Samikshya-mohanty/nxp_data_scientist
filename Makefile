.PHONY: download data stats figures forecast notebooks test app all

all: data stats figures forecast

download:
	uv run python -m scripts.fetch

data:
	uv run python -m scripts.panel

stats:
	uv run python -m scripts.stats

figures:
	uv run python -m scripts.figures

forecast:
	uv run python -m scripts.forecast

notebooks:
	uv run marimo export html notebooks/01_statistics.py -o reports/notebooks/01_statistics.html
	uv run marimo export html notebooks/02_charts.py -o reports/notebooks/02_charts.html
	uv run marimo export html notebooks/03_forecast.py -o reports/notebooks/03_forecast.html

test:
	uv run pytest

app:
	uv run marimo run app/dashboard.py
