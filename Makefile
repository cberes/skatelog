all: check test

check:
	uv run pre-commit run --all-files
	uv check --preview-features check-command

test:
	uv run pytest

init:
	uv sync
	uv run pre-commit install
