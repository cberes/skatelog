test:
	uv run pyright
	uv run pre-commit run --all-files
	uv run pytest

init:
	uv sync
	uv run pre-commit install
