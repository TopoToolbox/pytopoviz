import numpy as np
import warnings

from topotoolbox import GridObject

from pytopoviz import MapObject, hillshade, multishade, smooth_hillshade, smooth_multishade

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

    grid_values = np.asarray(grid.z, dtype=np.float32)
    grid_mean = grid_values[np.isfinite(grid_values)].mean()
    filled = np.where(np.isfinite(smoothed), smoothed, grid_mean)
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


def _nan_gaussian_smooth(values: np.ndarray, sigma: float = 1.0, mode: str = "nearest") -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    data = np.asarray(values, dtype=np.float32)
    finite_mask = np.isfinite(data)
    filled = np.where(finite_mask, data, 0.0)
    smoothed_data = gaussian_filter(filled, sigma=sigma, mode=mode)
    weights = gaussian_filter(finite_mask.astype(float), sigma=sigma, mode=mode)
    with np.errstate(invalid="ignore", divide="ignore"):
        result = smoothed_data / weights
    result[weights == 0.0] = np.nan
    return result.astype(np.float32)


def test_smooth_hillshade_matches_manual_smoothing():
    grid = _build_grid(np.array([[0.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.0]], dtype=np.float32))
    mapper = MapObject(grid)
    original_value = mapper.value.copy()

    smoothed = _nan_gaussian_smooth(mapper.value, sigma=1.0, mode="nearest")
    expected_grid = mapper.grid.duplicate_with_new_data(smoothed)
    expected_hs = expected_grid.hillshade(azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True)

    shaded = smooth_hillshade(mapper, sigma=1.0, mode="nearest", azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True)

    np.testing.assert_allclose(shaded.value, expected_hs.z, rtol=5e-5, atol=5e-5)
    np.testing.assert_array_equal(mapper.value, original_value)  # original untouched


def test_smooth_multishade_averages_two_smoothed_directions():
    grid = _build_grid(np.array([[0.0, 1.0], [2.0, 3.0]], dtype=np.float32))
    mapper = MapObject(grid)

    shade_single = smooth_hillshade(mapper, sigma=0.5, azimuth=315.0)
    shade_single_alt = smooth_hillshade(mapper, sigma=0.5, azimuth=135.0)

    combined = smooth_multishade(mapper, azimuths=(315.0, 135.0), sigma=0.5)

    expected = np.nanmean(np.stack([shade_single.value, shade_single_alt.value]), axis=0)
    np.testing.assert_allclose(combined.value, expected, rtol=5e-5, atol=5e-5)
