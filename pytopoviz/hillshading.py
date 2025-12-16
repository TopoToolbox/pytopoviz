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
    values = np.asarray(mapper.value, dtype=np.float32)
    mask = np.isnan(values)
    has_finite_values = np.isfinite(values).any()

    clean_values = np.nan_to_num(values, nan=np.nanmean(mapper.grid.z))
    import matplotlib.pyplot as plt
    temp_grid: GridObject = mapper.grid.duplicate_with_new_data(clean_values)

    hs_grid: GridObject = temp_grid.hillshade(
        azimuth=azimuth, altitude=altitude, exaggerate=exaggerate, fused=fused
    )

    shaded_values = np.array(hs_grid.z, copy=True)
    if mask.any():
        if has_finite_values:
            shaded_values[mask] = np.nan
        else:
            base_mask = np.isnan(np.asarray(mapper.grid.z, dtype=np.float32))
            shaded_values[base_mask] = np.nan

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

    stacked = np.stack([shade1.value, shade2.value])
    valid_counts = np.isfinite(stacked).sum(axis=0)
    summed = np.nansum(stacked, axis=0, dtype=np.float32)
    averaged = np.divide(
        summed,
        valid_counts,
        out=np.full_like(summed, np.nan, dtype=np.float32),
        where=valid_counts > 0,
    )

    new_grid = mapper.grid.astype(np.float32)
    new_grid.z = averaged.astype(np.float32)

    result = MapObject(
        new_grid,
        cmap='gray',
        alpha=0.45,
    )
    result.value = averaged
    return result
