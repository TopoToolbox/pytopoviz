"""Helpers to create hillshade MapObjects.

Author: B.G.
"""

from typing import Iterable, Tuple, Union

import numpy as np

from topotoolbox import GridObject

from .map_object import MapObject

__all__ = ["hillshade", "multishade"]


def hillshade(
    mapper: MapObject,
    azimuth: float = 315.0,
    altitude: float = 50.0,
    exaggerate: float = 1.0,
    fused: bool = True,
) -> MapObject:
    """Return a MapObject with the hillshade of the mapper's grid.

    NaN values from the source mapper are propagated to the hillshaded result.
    """
    hs_grid: GridObject = mapper.grid.hillshade(
        azimuth=azimuth, altitude=altitude, exaggerate=exaggerate, fused=fused
    )

    mask = np.isnan(mapper.value)
    shaded_values = np.array(hs_grid.z, copy=True)
    shaded_values[mask] = np.nan

    result = MapObject(
        hs_grid,
        cmap='gray',
        alpha=0.45,
    )
    result.value = shaded_values
    return result


def multishade(
    mapper: MapObject,
    azimuths: Union[Iterable[float], Tuple[float, float]] = (315.0, 135.0),
    altitude: float = 50.0,
    exaggerate: float = 1.0,
    fused: bool = True,
) -> MapObject:
    """Average two hillshades from different azimuths."""
    azimuth_list = tuple(azimuths)
    if len(azimuth_list) != 2:
        raise ValueError("azimuths must contain exactly two angles.")

    shade1 = hillshade(
        mapper,
        azimuth=azimuth_list[0],
        altitude=altitude,
        exaggerate=exaggerate,
        fused=fused,
    )
    shade2 = hillshade(
        mapper,
        azimuth=azimuth_list[1],
        altitude=altitude,
        exaggerate=exaggerate,
        fused=fused,
    )

    averaged = np.nanmean(np.stack([shade1.value, shade2.value]), axis=0)

    new_grid = mapper.grid.astype(np.float32)
    new_grid.z = averaged.astype(np.float32)

    result = MapObject(
        new_grid,
        cmap='gray',
        alpha=0.45,
    )
    result.value = averaged
    return result
