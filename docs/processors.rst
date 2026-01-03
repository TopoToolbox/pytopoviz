Processors
==========

Processors are small, composable steps attached to a ``MapObject`` that run in
order before plotting. They can mutate values in-place (e.g., smoothing or
masking) or produce derived ``MapObject`` layers (e.g., hillshade) which are
then plotted in sequence. Processors can be marked as 2D-only or 3D-only and
are skipped automatically in the other context.

Masking (NaN filters)
---------------------

These set values to ``NaN`` based on a condition to hide or clip data.

``nan_below(threshold)``
  Set values below ``threshold`` to ``NaN``. Parameters: ``threshold`` (float).

``nan_above(threshold)``
  Set values above ``threshold`` to ``NaN``. Parameters: ``threshold`` (float).

``nan_equal(value)``
  Set values equal to ``value`` to ``NaN``. Parameters: ``value`` (float).

``nan_mask(mask)``
  Set values to ``NaN`` where ``mask`` is True/1. Parameters: ``mask`` (2D array, same shape as data).

Filtering (value transforms)
----------------------------

``gaussian_smooth(sigma=1.0, mode="nearest")``
  Gaussian filter that preserves ``NaN`` regions. Parameters: ``sigma`` (float),
  ``mode`` (str, forwarded to ``scipy.ndimage.gaussian_filter``).

Shading (derived layers)
------------------------

These generate derived ``MapObject`` layers (draped in 3D) and typically use a
gray colormap with alpha for overlay.

``hillshade(azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True, alpha=0.45)``
  Single-direction hillshade. Parameters: ``azimuth``, ``altitude``,
  ``exaggerate``, ``fused``, ``alpha``.

``multishade(azimuths=(315.0, 135.0), altitude=50.0, exaggerate=1.0, fused=True, alpha=0.45)``
  Average of two hillshades. Parameters: ``azimuths`` (pair of floats),
  ``altitude``, ``exaggerate``, ``fused``, ``alpha``.

``smooth_hillshade(sigma=1.0, mode="nearest", azimuth=315.0, altitude=50.0, exaggerate=1.0, fused=True, alpha=0.45)``
  Hillshade computed on a smoothed copy of the data. Parameters: ``sigma``,
  ``mode``, ``azimuth``, ``altitude``, ``exaggerate``, ``fused``, ``alpha``.

``smooth_multishade(sigma=1.0, mode="nearest", azimuths=(315.0, 135.0), altitude=50.0, exaggerate=1.0, fused=True, alpha=0.45)``
  Dual-azimuth hillshade on smoothed data. Parameters: ``sigma``, ``mode``,
  ``azimuths``, ``altitude``, ``exaggerate``, ``fused``, ``alpha``.

3D helpers (surface scale)
--------------------------

3D-only processors that affect surface height scaling without changing colors.

``scale(factor)``
  Multiply the surface height scale by ``factor``. Parameters: ``factor`` (float).

``double_scale()``
  Convenience: same as ``scale(2.0)``.

``halve_scale()``
  Convenience: same as ``scale(0.5)``.

``tenfold()``
  Convenience: same as ``scale(10.0)``.

``tenthfold()``
  Convenience: same as ``scale(0.1)``.

3D helpers (lighting)
---------------------

3D-only processors that tweak lighting and shading.

``lighting_control(...)``
  Base lighting control with safeguards. Parameters: ``enabled`` (bool or None),
  ``ambient``, ``diffuse``, ``specular``, ``specular_power``,
  ``smooth_shading``, ``eye_dome_lighting``, ``light_azimuth``,
  ``light_elevation``, ``light_intensity``.

Presets:

``matte_lighting()``
  Low specular highlights for a matte look.

``glossy_lighting()``
  Stronger specular highlights for a glossy look.

``flat_lighting()``
  Minimal shading (ambient only) for a cartographic look.

``dramatic_lighting()``
  Higher contrast lighting.

``heightmap_lighting()``
  Balanced lighting tuned for large heightmaps.

Relative adjustments:

``lighting_intensity_up()``, ``lighting_intensity_down()``
  Increase or decrease overall lighting intensity by 20%.

``lighting_brighten()``, ``lighting_darken()``
  Shift brightness by adjusting ambient and diffuse.

``light_rotate_left(degrees=20.0)``, ``light_rotate_right(degrees=20.0)``
  Rotate light azimuth left/right by ``degrees``.

``light_raise(degrees=10.0)``, ``light_lower(degrees=10.0)``
  Raise/lower light elevation by ``degrees``.
