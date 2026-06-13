all: check test

check:
	uv check --preview-features check-command
	uv run pyright
	uv run pre-commit run --all-files

test:
	uv run pytest

init:
	uv sync
	uv run pre-commit install
