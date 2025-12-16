# pytopoviz

`pytopoviz` is an extension package for [`pytopotoolbox`](https://github.com/TopoToolbox/pytopotoolbox) focused on creating nice 2D (`matplotlib`) and 3D (`pyvista`) figures from `pytopotoolbox` objects. This scaffold mirrors the original package structure/linting/metadata but intentionally keeps the source minimal so you can layer in visualization utilities without `libtopotoolbox`.

## Features (planned)

- Visualization helpers for TopoToolbox grids and streams.
- Optional PyVista 3D support and Numba accelerations once implemented.

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

## Status

This is a boilerplate scaffold meant to mirror the structure and metadata of `pytopotoolbox` while adding visualization-focused dependencies. Fill in the package under `pytopoviz/` with your actual implementations.
