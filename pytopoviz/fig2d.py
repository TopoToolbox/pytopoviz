"""Quick matplotlib helpers for MapObject/GridObject."""

from typing import Iterable, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np

from topotoolbox import GridObject

from .helper2d import add_colorbar, add_grid_crosses, convert_ticks_to_km, finalize_figsize
from .map_object import MapObject

__all__ = ["quickmap"]


def _ensure_map(obj: Union[MapObject, GridObject]) -> MapObject:
    """Convert GridObject to MapObject when needed."""
    if isinstance(obj, MapObject):
        return obj
    if isinstance(obj, GridObject):
        return MapObject(obj)
    raise TypeError("quickmap accepts MapObject or GridObject instances.")


def quickmap(*maps: Union[MapObject, GridObject]):
    """Plot one or more MapObjects on a single axis, in order.

    Returns
    -------
    (fig, ax)
        Matplotlib figure and axis.
    """
    if len(maps) == 0:
        raise ValueError("Provide at least one MapObject or GridObject.")

    map_list: Tuple[MapObject, ...] = tuple(_ensure_map(m) for m in maps)

    figsize = finalize_figsize(map_list)
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True, layout=None)
    fig.set_constrained_layout_pads(w_pad=0.05, h_pad=0.05, wspace=0.02, hspace=0.02)
    for mapper in map_list:
        im = ax.imshow(
            mapper.value,
            cmap=mapper.cmap,
            alpha=mapper.alpha,
            extent=mapper.grid.extent,
        )
        if isinstance(mapper.cbar, str):
            add_colorbar(ax, im, label=mapper.cbar)

    ax.set_xlabel("Easting (km)")
    ax.set_ylabel("Northing (km)")
    convert_ticks_to_km(ax)
    add_grid_crosses(ax)
    return fig, ax
