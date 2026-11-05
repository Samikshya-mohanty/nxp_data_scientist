.PHONY: download data test

download:
	uv run python -m scripts.fetch

data:
	uv run python -m scripts.panel

test:
	uv run pytest
