"""Quick PyVista 3D helpers for MapObject/GridObject."""

from typing import Tuple, Union

import numpy as np
import pyvista as pv

from topotoolbox import GridObject

from .map_object import MapObject

__all__ = ["quickmap3d"]


def _ensure_map(obj: Union[MapObject, GridObject]) -> MapObject:
    """Convert GridObject to MapObject when needed."""
    if isinstance(obj, MapObject):
        return obj
    if isinstance(obj, GridObject):
        return MapObject(obj)
    raise TypeError("quickmap3d accepts MapObject or GridObject instances.")


def _structured_grid_from_map(mapper: MapObject) -> Tuple[pv.StructuredGrid, str]:
    """Build a StructuredGrid with per-point scalars from a MapObject."""
    z = mapper.value
    ny, nx = z.shape
    xmin, xmax, ymin, ymax = mapper.grid.extent

    x = np.linspace(xmin, xmax, nx)
    y = np.linspace(ymin, ymax, ny)
    xx, yy = np.meshgrid(x, y)

    # Geometry uses filled values; scalar array preserves NaNs for transparency.
    grid = pv.StructuredGrid(xx, yy, np.nan_to_num(z, nan=0.0))
    scalars_name = "scalars"
    grid[scalars_name] = z.ravel(order="F")

    mask = np.isnan(z)
    if mask.any():
        grid = grid.extract_points(~mask.ravel(order="F"), adjacent_cells=True)

    return grid, scalars_name


def quickmap3d(
    *maps: Union[MapObject, GridObject],
    screenshot_path: str = "quickmap3d.png",
    background: str = "white",
    smooth_shading: bool = True,
    show_scalar_bar: bool = True,
):
    """Display one or more MapObjects in 3D with PyVista and save a screenshot.

    Parameters
    ----------
    *maps :
        One or more MapObject or GridObject instances. The first map defines the
        surface geometry; each map adds a colored surface using its own colormap
        and alpha.
    screenshot_path : str
        Output path for the captured screenshot after the interactive window is
        closed.
    background : str
        Plotter background color.
    smooth_shading : bool
        Toggle smooth shading.
    show_scalar_bar : bool
        If True, show scalar bars for map entries that define ``cbar`` labels.

    Returns
    -------
    cpos :
        Camera position returned by ``pv.Plotter.show``.
    """
    if len(maps) == 0:
        raise ValueError("Provide at least one MapObject or GridObject.")

    map_list = tuple(_ensure_map(m) for m in maps)

    plotter = pv.Plotter()
    plotter.set_background(background)
    plotter.enable_eye_dome_lighting()

    for idx, mapper in enumerate(map_list):
        mesh, scalars_name = _structured_grid_from_map(mapper)
        scalar_bar_args = {}
        if isinstance(mapper.cbar, str) and show_scalar_bar:
            scalar_bar_args["title"] = mapper.cbar
        else:
            scalar_bar_args["title"] = ""

        plotter.add_mesh(
            mesh,
            scalars=scalars_name,
            cmap=mapper.cmap,
            clim=(mapper.vmin, mapper.vmax),
            opacity=mapper.alpha,
            nan_opacity=0.0,
            smooth_shading=smooth_shading,
            show_scalar_bar=bool(scalar_bar_args.get("title")),
            scalar_bar_args=scalar_bar_args,
            name=f"map_{idx}",
            ambient=0.15,
            diffuse=0.8,
            specular=0.1,
            specular_power=10,
        )

    cpos = plotter.show(auto_close=False)
    plotter.screenshot(screenshot_path)
    plotter.close()
    return cpos
