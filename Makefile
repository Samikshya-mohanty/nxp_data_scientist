.PHONY: download data test

download:
	uv run python -m lifeexp.fetch

data:
	uv run python -m lifeexp.panel

test:
	uv run pytest
