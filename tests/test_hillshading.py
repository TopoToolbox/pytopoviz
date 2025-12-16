import numpy as np

from topotoolbox import GridObject

from pytopoviz import MapObject, hillshade, multishade

import warnings

def _build_grid(values: np.ndarray) -> GridObject:
    grid = GridObject()
    grid.z = values
    grid.cellsize = 1.0
    return grid


def test_hillshade_propagates_nan_mask():
    grid = _build_grid(np.array([[1.0, 2.0], [np.nan, 4.0]], dtype=np.float32))
    mapper = MapObject(grid)

    shaded = hillshade(mapper)

    assert isinstance(shaded, MapObject)
    assert shaded.grid is not mapper.grid
    assert np.isnan(shaded.value[1, 0])


def test_multishade_averages_two_directions():
    grid = _build_grid(np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    mapper = MapObject(grid)

    shade_single = hillshade(mapper, azimuth=315.0)
    shade_single_alt = hillshade(mapper, azimuth=135.0)

    combined = multishade(mapper, azimuths=(315.0, 135.0))

    expected = np.nanmean(np.stack([shade_single.value, shade_single_alt.value]), axis=0)
    np.testing.assert_allclose(combined.value, expected, rtol=5e-5, atol=5e-5)


def test_hillshade_uses_mapper_value_data():
    base = np.array([[0.0, 1.0, 2.0], [0.0, 1.0, 2.0], [0.0, 1.0, 2.0]], dtype=np.float32)
    grid = _build_grid(base)
    mapper = MapObject(grid)

    smoothed = np.array(
        [[np.nan, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]],
        dtype=np.float32,
    )
    mapper.value = smoothed

    filled = np.nan_to_num(smoothed, nan=0.0)
    expected_grid = mapper.grid.duplicate_with_new_data(filled)
    expected_hs = expected_grid.hillshade(azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True)
    expected_values = np.array(expected_hs.z, copy=True)
    expected_values[np.isnan(smoothed)] = np.nan

    shaded = hillshade(mapper, azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True)

    np.testing.assert_allclose(shaded.value, expected_values, rtol=5e-5, atol=5e-5)


def test_multishade_handles_all_nan_without_warning():
    grid = _build_grid(np.array([[np.nan, np.nan], [np.nan, np.nan]], dtype=np.float32))
    mapper = MapObject(grid)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        shaded = multishade(mapper)

    assert np.all(np.isnan(shaded.value))


def test_hillshade_falls_back_when_value_is_all_nan_but_grid_not():
    grid = _build_grid(np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    mapper = MapObject(grid)
    mapper.value = np.array([[np.nan, np.nan], [np.nan, np.nan]], dtype=np.float32)

    shaded = hillshade(mapper, azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True)

    assert np.isfinite(shaded.value).any()
