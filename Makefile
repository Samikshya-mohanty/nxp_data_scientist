.PHONY: download data stats test

download:
	uv run python -m scripts.fetch

data:
	uv run python -m scripts.panel

stats:
	uv run python -m scripts.stats

test:
	uv run pytest
