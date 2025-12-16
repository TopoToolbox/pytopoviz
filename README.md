# pytopoviz

`pytopoviz` is visualisation framework for crafting/using reproduciple recipes to make 2D and 3D figure from [`pytopotoolbox`](https://github.com/TopoToolbox/pytopotoolbox). 2D figures are built on top of `matplotlib`, 3D on `pyvista`.

## Features

- style sheets
- automatically handles geographic extent
- 2D composite figure object
- 3D quick figure
- built-in processors:
  + conditional nan masking (e.g. removing data below elevation)
  + hillshading, smoothing other filtering
  + WIP
- (WIP) per-application recipes (e.g. graphflood, slope, ...)
- (WIP) topographic analyses processors (e.g. stream network)

## Requirements

- Python >= 3.10
- Core dependencies: `topotoolbox`, `numpy`, `matplotlib`, `scipy`, `rasterio`, `geopandas`, `shapely`, `clarabel`
- Extra dependencies for this extension: `pyvista`, `numba`

## Installation

Once published to PyPI:

```bash
pip install --upgrade pytopoviz
```

For local development from this repository:

```bash
pip install -e ".[test,docs]"
```

## Development

- Source lives in `pytopoviz/`.
- Tests live in `tests/` and use `pytest`.
- Docs use Sphinx; starter files live in `docs/`.
- Linting follows the same `pylint` configuration used in `pytopotoolbox`.

## Authors

Boris Gailleton (boris.gailleton@univ-rennes.fr)
