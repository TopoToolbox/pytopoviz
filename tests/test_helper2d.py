import matplotlib

# non-interactive backend for tests
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from pytopoviz import add_grid_crosses, convert_ticks_to_km


def test_convert_ticks_to_km_updates_formatter_and_labels():
    fig, ax = plt.subplots()
    ax.set_xlabel("distance (m)")
    ax.set_ylabel("height m")
    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 2000)

    convert_ticks_to_km(ax)

    assert ax.get_xlabel() == "distance (km)"
    assert ax.get_ylabel() == "height km"
    fmt = ax.xaxis.get_major_formatter()
    assert fmt(1000, 0) == "1.0"


def test_add_grid_crosses_adds_markers_at_ticks():
    fig, ax = plt.subplots()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])

    add_grid_crosses(ax, color="red", size=5)

    # One Line2D per cross
    lines = [line for line in ax.lines if line.get_marker() == "+"]
    assert len(lines) == 9
