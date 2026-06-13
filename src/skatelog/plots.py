from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


@dataclass
class PlotConfig:
    title: str
    label_x: str
    label_y: str
    output_path: Path | None = None
    buf: BytesIO | None = None

def _save_figure(figure: Figure, config: PlotConfig) -> None:
    if config.output_path is not None:
        figure.savefig(config.output_path)

    if config.buf is not None:
        figure.savefig(config.buf, format="png")
        config.buf.seek(0)
        plt.close(figure)

def line(data: Iterable[tuple[Any, int | float]], config: PlotConfig) -> None:
    fig, ax = plt.subplots()
    data_list = list(data)
    ax.plot([x[0] for x in data_list], [x[1] for x in data_list])

    ax.set(xlabel=config.label_x,
           ylabel=config.label_y,
           title=config.title)
    ax.grid()

    _save_figure(fig, config)

def bar(data: Iterable[tuple[Any, int | float]], config: PlotConfig) -> None:
    fig, ax = plt.subplots()
    data_list = list(data)
    data_size = len(data_list)
    cmap = plt.get_cmap('viridis')
    colors = [cmap(i / (data_size - 1)) if data_size > 1 else cmap(0.0) for i in range(data_size)]
    ax.bar([x[0] for x in data_list], [x[1] for x in data_list], color=colors)

    ax.set(xlabel=config.label_x,
           ylabel=config.label_y,
           title=config.title)

    if len(data_list) > 6:
        ax.tick_params(axis='x', rotation=90)
        fig.tight_layout()

    _save_figure(fig, config)

def pie(data: Iterable[tuple[Any, int]], config: PlotConfig) -> None:
    fig, ax = plt.subplots()
    data_list = list(data)
    ax.pie([x[1] for x in data_list], labels=[x[0] for x in data_list])

    ax.set(xlabel=config.label_x,
           ylabel=config.label_y,
           title=config.title)

    _save_figure(fig, config)
