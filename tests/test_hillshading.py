import numpy as np

from topotoolbox import GridObject

from pytopoviz import MapObject, hillshade, multishade


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
