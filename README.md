# skatelog

A CLI for tracking skateboarding sessions.

## Background

I try to skateboard for fun and exercise as often as possible.
And I like to keep track of what I work on and also how long my gear lasts.
I've been keeping this data in a spreadsheet since 2024.

Also, I used to be comfortable with Python.
I even used it profesionally around 2014 to 2015.
Since then I've barely used Python at all.
I decided to work on this project with the goal of re-learning Python.

In an effort to actually _learn_ Python I'm writing everything by hand.
Also, I've become interested in [tmux](https://github.com/tmux/tmux/)
and [neovim](https://neovim.io/), so I'm using those tools as well.

## Features

- [Typer](https://typer.tiangolo.com/) CLI
- Text formatting with [rich](https://rich.readthedocs.io/en/latest/)
- Stores data in a [SQLite](https://sqlite.org) database
- Imports from and exports to CSV files

## Dependencies

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

## Usage

- `uv run skatelog add` logs a new session
- `uv run skatelog list` lists sessions
- `uv run skatelog show 2026-05-22` shows the session on the specified date
- `uv run skatelog list-disciplines` lists all known disciplines and how many times they were trained
- `uv run skatelog list-locations` lists all known locations and how many times they were visited
- `uv run skatelog list-shoes` lists all known shoes and how many times they were worn
- `uv run skatelog list-boards` lists all known boards and how many times there were skated
- `uv run skatelog import /path/to/import.csv` imports data from a CSV file
- `uv run skatelog export /path/to/export.csv` exports data to a CSV file

## Development

- Run pyright: `uv run pyright`
- Run tests: `uv run py.test`
- Run ruff: TODO I haven't configured this yet
