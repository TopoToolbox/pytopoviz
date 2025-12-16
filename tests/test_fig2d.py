import matplotlib

# Use non-interactive backend for tests
matplotlib.use("Agg")

import numpy as np

from topotoolbox import GridObject

from pytopoviz import MapObject, quickmap


def _grid_with_values(values):
    grid = GridObject()
    grid.z = np.array(values, dtype=np.float32)
    return grid


def test_quickmap_single_and_cbar_label():
    grid = _grid_with_values([[1, 2], [3, 4]])
    mapper = MapObject(grid, cbar="elev")

    fig, ax = quickmap(mapper)

    assert fig is not None
    assert ax is not None
    # Single axis + colorbar
    assert len(fig.axes) == 2  # imshow axis + colorbar axis
    assert fig.axes[1].get_label() == "<colorbar>"
    assert fig.axes[1].get_ylabel() == "elev"
    # Extent should follow GridObject.extent
    im = fig.axes[0].images[0]
    assert tuple(im.get_extent()) == grid.extent


def test_quickmap_stacks_multiple_maps_on_same_axis():
    grid1 = _grid_with_values([[0, 1]])
    grid2 = _grid_with_values([[1, 0]])

    mapper1 = MapObject(grid1, cbar="one")
    mapper2 = MapObject(grid2, cmap="gray", alpha=0.4)

    fig, ax = quickmap(mapper1, mapper2)

    # Both images plotted on same axis
    assert len(ax.images) == 2
    # Only one colorbar attached (from mapper1)
    assert len(fig.axes) == 2
    assert fig.axes[1].get_ylabel() == "one"


def test_quickmap_labels_ticks_and_crosses():
    grid = _grid_with_values([[0, 1], [2, 3]])
    mapper = MapObject(grid, cbar="elev")

    fig, ax = quickmap(mapper)

    assert ax.get_xlabel() == "Easting (km)"
    assert ax.get_ylabel() == "Northing (km)"

    # Tick formatter should convert meters to km (1000 -> 1.0)
    x_formatter = ax.xaxis.get_major_formatter()
    assert x_formatter(1000) == "1.0"

    # Cross markers added
    assert len(ax.lines) > 0
