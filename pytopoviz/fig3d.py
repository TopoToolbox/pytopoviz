"""Quick PyVista 3D helpers for MapObject/GridObject.

Author: B.G.
"""

from typing import Dict, Iterable, Tuple, Union

import numpy as np
import pyvista as pv

from topotoolbox import GridObject

from .map_object import MapObject
from .processing import is_plottable, _processor_is_compatible

__all__ = ["quickmap3d", "Fig3DObject"]


def _ensure_map(obj: Union[MapObject, GridObject]) -> MapObject:
    """Convert GridObject to MapObject when needed."""
    if isinstance(obj, MapObject):
        return obj
    if isinstance(obj, GridObject):
        return MapObject(obj)
    raise TypeError("quickmap3d accepts MapObject or GridObject instances.")


def _structured_grid_from_map(
    mapper: MapObject,
    surface_map: MapObject,
    z_exaggeration: float | None = None,
) -> Tuple[pv.StructuredGrid, str]:
    """Build a StructuredGrid using surface values and mapper scalars."""
    scalars = mapper.value
    z = surface_map.value
    cellsize = getattr(surface_map.grid, "cellsize", 1.0)
    cellsize_value = float(np.asarray(cellsize).ravel()[0]) if cellsize is not None else 1.0
    if cellsize_value <= 0:
        cellsize_value = 1.0
    z_factor = float(surface_map.z_scale_factor)
    if z_exaggeration is None:
        xmin, xmax, ymin, ymax = surface_map.grid.extent
        span_units = max(xmax - xmin, ymax - ymin)
        span_cells = span_units / cellsize_value if cellsize_value > 0 else span_units
        finite = np.isfinite(z)
        z_range = float(np.nanmax(z) - np.nanmin(z)) if finite.any() else 0.0
        if z_range > 0:
            target_relief = 3.2 * span_cells
            z_scale = (target_relief / z_range) * z_factor
        else:
            z_scale = 0.0
    else:
        z_scale = (float(z_exaggeration) / cellsize_value) * z_factor
    ny, nx = z.shape
    xmin, xmax, ymin, ymax = surface_map.grid.extent

    x = np.linspace(xmin, xmax, nx)
    y = np.linspace(ymin, ymax, ny)
    xx, yy = np.meshgrid(x, y)

    # Geometry uses filled values; scalar array preserves NaNs for transparency.
    grid = pv.StructuredGrid(xx, yy, np.nan_to_num(z, nan=0.0) * z_scale)
    scalars_name = "scalars"
    grid[scalars_name] = scalars.ravel(order="F")

    mask = np.isnan(scalars)
    if mask.any():
        grid = grid.extract_points(~mask.ravel(order="F"), adjacent_cells=True)

    return grid, scalars_name


class Fig3DObject:
    """Wrapper around a PyVista plotter to manage 3D map layers."""

    def __init__(
        self,
        *,
        background: str = "white",
        smooth_shading: bool = True,
        show_scalar_bar: bool = True,
        z_exaggeration: float | None = None,
    ):
        self.plotter = pv.Plotter()
        self.plotter.set_background(background)
        self.plotter.enable_eye_dome_lighting()

        self.smooth_shading = smooth_shading
        self.show_scalar_bar = show_scalar_bar
        self.z_exaggeration = None if z_exaggeration is None else float(z_exaggeration)

        self.meshes: Dict[MapObject, pv.Actor] = {}

    def add_maps(self, *maps: Union[MapObject, GridObject]):
        """Add MapObjects to the plotter after applying processors in order."""
        if not maps:
            raise ValueError("Provide at least one MapObject or GridObject to add.")

        map_list_raw = tuple(_ensure_map(m) for m in maps)
        plot_list: list[tuple[MapObject, MapObject]] = []

        def collect(current: MapObject, base_surface: MapObject):
            surface_map = base_surface if current.draped else current
            plot_list.append((current, surface_map))
            for proc in current.processors:
                if not _processor_is_compatible(proc, "3d"):
                    continue
                produced = proc(current)
                if produced is None:
                    continue
                produced_list: Iterable = produced if isinstance(produced, (list, tuple)) else (produced,)
                for item in produced_list:
                    if not is_plottable(item):
                        continue
                    collect(item, surface_map)

        for mapper in map_list_raw:
            collect(mapper, mapper)

        for idx, (mapper, surface_map) in enumerate(plot_list):
            mesh, scalars_name = _structured_grid_from_map(
                mapper,
                surface_map,
                z_exaggeration=self.z_exaggeration,
            )
            scalar_bar_args = {}
            if isinstance(mapper.cbar, str) and self.show_scalar_bar:
                scalar_bar_args["title"] = mapper.cbar
            else:
                scalar_bar_args["title"] = ""

            actor = self.plotter.add_mesh(
                mesh,
                scalars=scalars_name,
                cmap=mapper.cmap,
                clim=(mapper.vmin, mapper.vmax),
                opacity=mapper.alpha,
                nan_opacity=0.0,
                smooth_shading=self.smooth_shading,
                show_scalar_bar=bool(scalar_bar_args.get("title")),
                scalar_bar_args=scalar_bar_args,
                name=f"map_{idx}",
                ambient=0.15,
                diffuse=0.8,
                specular=0.1,
                specular_power=10,
            )
            self.meshes[mapper] = actor
        return self.plotter

    def show(self, screenshot_path: str = "quickmap3d.png", auto_close: bool = False):
        """Render the scene, optionally save a screenshot, and return camera position."""
        cpos = self.plotter.show(auto_close=auto_close)
        if screenshot_path:
            self.plotter.screenshot(screenshot_path)
        if auto_close:
            self.plotter.close()
        return cpos


def quickmap3d(
    *maps: Union[MapObject, GridObject],
    screenshot_path: str = "quickmap3d.png",
    background: str = "white",
    smooth_shading: bool = True,
    show_scalar_bar: bool = True,
    z_exaggeration: float | None = None,
):
    """Display one or more MapObjects in 3D with PyVista and save a screenshot."""
    if len(maps) == 0:
        raise ValueError("Provide at least one MapObject or GridObject.")

    fig = Fig3DObject(
        background=background,
        smooth_shading=smooth_shading,
        show_scalar_bar=show_scalar_bar,
        z_exaggeration=z_exaggeration,
    )
    fig.add_maps(*maps)
    return fig.show(screenshot_path=screenshot_path, auto_close=False)
