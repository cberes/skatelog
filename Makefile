test:
	uv run pyright
	uv run ruff check .
	uv run pytest
