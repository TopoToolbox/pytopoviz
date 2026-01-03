"""Workflow serialization, loading, and execution helpers.

Author: B.G.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import numpy as np
import rasterio
import topotoolbox as ttb

from topotoolbox import GridObject

from .fig2d import Fig2DObject
from .fig3d import Fig3DObject
from .filter2d import BUILTIN_FILTERS
from .helper3d import BUILTIN_3D
from .map_object import MapObject
from .masknan import BUILTIN_MASK_NAN
from .shading2d import BUILTIN_SHADING
from .style2d import get_style, set_style
from .helper2d import add_grid_crosses, convert_ticks_to_km


def _grid_from_array(arr: np.ndarray, cellsize: float = 1.0) -> GridObject:
    """Build a GridObject from a numeric array and cellsize."""
    grid = GridObject()
    grid.z = np.array(arr, dtype=np.float32)
    grid.cellsize = float(cellsize)
    return grid


def _load_rasterio(path: str, band: int = 1) -> GridObject:
    """Load a raster file into a GridObject using rasterio."""
    with rasterio.open(path) as src:
        data = src.read(band).astype(np.float32)
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan
        transform = src.transform
        cellsize = abs(transform.a)
    return _grid_from_array(data, cellsize=cellsize)


def _load_numpy(path: str, key: Optional[str] = None) -> GridObject:
    """Load a .npy/.npz into a GridObject (cellsize defaults to 1.0)."""
    arr = np.load(path)
    if hasattr(arr, "files"):
        if key is None:
            if len(arr.files) != 1:
                raise ValueError("npz file requires a 'key' when multiple arrays are present.")
            key = arr.files[0]
        arr = arr[key]
    return _grid_from_array(arr, cellsize=1.0)


def _load_topotoolbox_dem(source: str) -> GridObject:
    """Load a DEM using topotoolbox.load_dem."""
    return ttb.load_dem(source)


def _load_topotoolbox_tif(path: str) -> GridObject:
    """Load a GeoTIFF using topotoolbox.read_tif."""
    return ttb.read_tif(path)


def _resolve_cmap(cmap_name: str):
    try:
        import matplotlib.pyplot as plt

        plt.get_cmap(cmap_name)
        return cmap_name
    except Exception:
        try:
            from cmcrameri import cm

            if hasattr(cm, cmap_name):
                return getattr(cm, cmap_name)
        except Exception:
            pass
    return cmap_name


BUILTIN_LOADERS = {
    "topotoolbox.read_tif": _load_topotoolbox_tif,
    "topotoolbox.load_dem": _load_topotoolbox_dem,
    "rasterio": _load_rasterio,
    "numpy": _load_numpy,
}

BUILTIN_PROCESSORS: Dict[str, Any] = {
    **BUILTIN_MASK_NAN,
    **BUILTIN_FILTERS,
    **BUILTIN_SHADING,
    **BUILTIN_3D,
}


def _resolve_param(value: Any, inputs: Dict[str, Any]) -> Any:
    """Resolve a single param value, handling {"$ref": "..."} placeholders."""
    if isinstance(value, dict) and "$ref" in value:
        ref = value["$ref"]
        if ref not in inputs:
            raise KeyError(f"Missing input value for '{ref}'.")
        return inputs[ref]
    return value


def _resolve_params(params: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a param dictionary, applying input references."""
    return {key: _resolve_param(val, inputs) for key, val in params.items()}


def _parse_value(raw: Any, value_type: str) -> Any:
    """Parse raw input values to typed Python objects."""
    if value_type == "path":
        return str(raw)
    if value_type == "str":
        return str(raw)
    if value_type == "int":
        return int(raw)
    if value_type == "float":
        return float(raw)
    if value_type == "bool":
        if isinstance(raw, bool):
            return raw
        if str(raw).lower() in ("true", "1", "yes", "y"):
            return True
        if str(raw).lower() in ("false", "0", "no", "n"):
            return False
        raise ValueError(f"Invalid bool value: {raw}")
    if value_type == "json":
        return json.loads(raw) if isinstance(raw, str) else raw
    return raw


def _apply_fig2d_action(fig: Fig2DObject, action: Dict[str, Any]) -> None:
    """Apply a single fig2d action to the selected axis."""
    action_type = action.get("type")
    axis_index = int(action.get("axis", 0))
    if axis_index < 0 or axis_index >= len(fig.axes):
        raise IndexError(f"Axis index {axis_index} out of range.")
    ax = fig.axes[axis_index]

    if action_type == "title":
        ax.set_title(action.get("text", ""), loc=action.get("loc", "center"))
        return
    if action_type == "xlabel":
        ax.set_xlabel(action.get("text", ""))
        return
    if action_type == "ylabel":
        ax.set_ylabel(action.get("text", ""))
        return
    if action_type == "xlim":
        ax.set_xlim(action.get("min"), action.get("max"))
        return
    if action_type == "ylim":
        ax.set_ylim(action.get("min"), action.get("max"))
        return
    if action_type == "convert_ticks_to_km":
        convert_ticks_to_km(ax, axes=action.get("axes", "both"))
        return
    if action_type == "add_grid_crosses":
        add_grid_crosses(
            ax,
            color=action.get("color", "black"),
            size=action.get("size", 5),
            linewidth=action.get("linewidth", 1),
            alpha=action.get("alpha", 0.47),
            include_minor=action.get("include_minor", True),
        )
        return
    raise ValueError(f"Unknown fig2d action '{action_type}'.")


@dataclass
class Workflow:
    """Serializable workflow containing data sources, maps, and run settings."""
    spec: Dict[str, Any]

    @classmethod
    def from_file(cls, path: str) -> "Workflow":
        """Load a workflow JSON file."""
        with open(path, "r", encoding="utf-8") as handle:
            return cls(json.load(handle))

    def to_file(self, path: str) -> None:
        """Write the workflow JSON file."""
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(_jsonify(self.spec), handle, indent=2)

    def input_specs(self) -> Dict[str, Dict[str, Any]]:
        """Return input definitions used for runtime prompting/validation."""
        return self.spec.get("inputs", {})

    def validate_defaults(self) -> None:
        """Ensure all inputs declare a default value."""
        missing = [name for name, spec in self.input_specs().items() if "default" not in spec]
        if missing:
            raise ValueError(f"All inputs must define a default. Missing: {', '.join(sorted(missing))}.")

    def resolve_inputs(self, values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve provided input values using defaults when needed."""
        provided = values or {}
        resolved: Dict[str, Any] = {}
        for name, spec in self.input_specs().items():
            if name in provided:
                resolved[name] = _parse_value(provided[name], spec.get("type", "str"))
            elif "default" in spec:
                resolved[name] = spec["default"]
            else:
                raise KeyError(f"Missing required input '{name}'.")
        return resolved

    def build_maps(self, inputs: Dict[str, Any]) -> list[MapObject]:
        """Build MapObjects by loading data and attaching processors."""
        data_sources: Dict[str, Any] = self.spec.get("data_sources", {})
        grids: Dict[str, GridObject] = {}
        for data_id, data_spec in data_sources.items():
            loader_name = data_spec.get("loader")
            if loader_name not in BUILTIN_LOADERS:
                raise ValueError(f"Unknown loader '{loader_name}'.")
            params = _resolve_params(data_spec.get("params", {}), inputs)
            grid = BUILTIN_LOADERS[loader_name](**params)
            grids[data_id] = grid

        maps: list[MapObject] = []
        for map_spec in self.spec.get("maps", []):
            data_id = map_spec.get("data")
            if data_id not in grids:
                raise KeyError(f"Map '{map_spec.get('name')}' references unknown data '{data_id}'.")
            grid = grids[data_id]
            mapper = MapObject(
                grid,
                cmap=_resolve_cmap(map_spec.get("cmap", "terrain")),
                vmin=map_spec.get("vmin"),
                vmax=map_spec.get("vmax"),
                alpha=map_spec.get("alpha", 1.0),
                cbar=map_spec.get("cbar"),
                name=map_spec.get("name"),
                draped=map_spec.get("draped", False),
                ambient=map_spec.get("ambient", 0.15),
                diffuse=map_spec.get("diffuse", 0.8),
                specular=map_spec.get("specular", 0.1),
                specular_power=map_spec.get("specular_power", 10.0),
                smooth_shading=map_spec.get("smooth_shading"),
                eye_dome_lighting=map_spec.get("eye_dome_lighting"),
                light_azimuth=map_spec.get("light_azimuth"),
                light_elevation=map_spec.get("light_elevation"),
                light_intensity=map_spec.get("light_intensity"),
            )
            for proc_spec in map_spec.get("processors", []):
                proc_name = proc_spec.get("name")
                if proc_name not in BUILTIN_PROCESSORS:
                    raise ValueError(f"Unknown processor '{proc_name}'.")
                params = _resolve_params(proc_spec.get("params", {}), inputs)
                proc = BUILTIN_PROCESSORS[proc_name](**params)
                mapper.processors.append(proc)
            maps.append(mapper)
        return maps

    def run(self, inputs: Dict[str, Any], mode: Optional[str] = None):
        """Execute the workflow in fig2d/fig3d mode."""
        maps = self.build_maps(inputs)
        maps_by_name = {m.name: m for m in maps}
        run_spec = self.spec.get("run", {})
        selected_mode = mode or run_spec.get("mode", "fig2d")
        if selected_mode == "fig2d":
            fig_spec = self.spec.get("fig2d", {})
            if fig_spec.get("style"):
                set_style(fig_spec["style"])
            fig = Fig2DObject(figsize=fig_spec.get("figsize"))
            fig.add_maps(fig.ax, *maps)
            for action in fig_spec.get("actions", []):
                _apply_fig2d_action(fig, action)
            if fig_spec.get("save_path"):
                fig.save(fig_spec["save_path"])
            if fig_spec.get("show", True):
                import matplotlib.pyplot as plt

                plt.show()
            return fig
        if selected_mode == "fig3d":
            fig_spec = self.spec.get("fig3d", {})
            fig2d_spec = self.spec.get("fig2d", {})
            if fig2d_spec.get("style"):
                set_style(fig2d_spec["style"])
            fig = Fig3DObject(
                background=fig_spec.get("background", "white"),
                smooth_shading=fig_spec.get("smooth_shading", True),
                show_scalar_bar=fig_spec.get("show_scalar_bar", True),
                z_exaggeration=fig_spec.get("z_exaggeration"),
            )
            if fig_spec.get("camera_position") is not None:
                fig.set_camera_position(fig_spec["camera_position"])
            surface_map = fig_spec.get("surface_map")
            if isinstance(surface_map, str):
                surface_map = maps_by_name.get(surface_map)
            fig.add_maps(*maps, surface_map=surface_map)
            if fig_spec.get("show", True):
                fig.show(
                    screenshot_path=fig_spec.get("screenshot_path", "quickmap3d.png"),
                    auto_close=fig_spec.get("auto_close", False),
                    print_camera=fig_spec.get("print_camera", True),
                )
            else:
                fig.save(fig_spec.get("screenshot_path", "quickmap3d.png"))
            return fig
        if selected_mode == "both":
            self.run(inputs, mode="fig2d")
            return self.run(inputs, mode="fig3d")
        raise ValueError("run.mode must be 'fig2d', 'fig3d', or 'both'.")


def workflow_from_fig2d(
    fig: Fig2DObject,
    *,
    interactive: bool = True,
    default_loader: str = "topotoolbox.read_tif",
) -> Workflow:
    """Create a workflow from a Fig2DObject instance."""
    if not isinstance(fig, Fig2DObject):
        raise TypeError("workflow_from_fig2d expects a Fig2DObject.")
    maps = fig.base_maps if getattr(fig, "base_maps", None) else list(fig.images.keys())
    style = get_style()
    inputs, data_sources, map_specs = _build_specs_from_maps(maps, default_loader=default_loader)
    figsize = None
    try:
        figsize = list(fig.fig.get_size_inches())
    except Exception:
        pass
    fig2d_spec: Dict[str, Any] = {}
    if figsize:
        fig2d_spec["figsize"] = figsize
    if style:
        fig2d_spec["style"] = style
    actions = _extract_fig2d_actions(fig)
    if actions:
        fig2d_spec["actions"] = actions
    spec = {
        "version": 1,
        "interactive": interactive,
        "inputs": inputs,
        "data_sources": data_sources,
        "maps": map_specs,
        "fig2d": fig2d_spec,
        "run": {"mode": "fig2d"},
    }
    return Workflow(spec)


def workflow_from_fig3d(
    fig: Fig3DObject,
    *,
    interactive: bool = True,
    default_loader: str = "topotoolbox.read_tif",
) -> Workflow:
    """Create a workflow from a Fig3DObject instance."""
    maps = fig.base_maps if getattr(fig, "base_maps", None) else list(fig.meshes.keys())
    inputs, data_sources, map_specs = _build_specs_from_maps(maps, default_loader=default_loader)
    spec = {
        "version": 1,
        "interactive": interactive,
        "inputs": inputs,
        "data_sources": data_sources,
        "maps": map_specs,
        "fig3d": {
            "background": _serialize_color(fig.plotter.background_color),
            "smooth_shading": fig.smooth_shading,
            "show_scalar_bar": fig.show_scalar_bar,
            "z_exaggeration": fig.z_exaggeration,
        },
        "run": {"mode": "fig3d"},
    }
    return Workflow(spec)


def _build_specs_from_maps(
    maps: Iterable[MapObject],
    *,
    default_loader: str,
) -> tuple[Dict[str, Any], Dict[str, Any], list[Dict[str, Any]]]:
    """Build input, data source, and map specs from MapObjects."""
    inputs: Dict[str, Any] = {}
    data_sources: Dict[str, Any] = {}
    map_specs: list[Dict[str, Any]] = []

    for mapper in maps:
        data_id = mapper.name
        input_id = f"{data_id}_path"
        inputs[input_id] = {
            "type": "path",
            "prompt": f"Path for {data_id}",
            "required": True,
            "default": f"{data_id}.tif",
        }
        loader_params = {"path": {"$ref": input_id}}
        if default_loader == "topotoolbox.load_dem":
            loader_params = {"source": {"$ref": input_id}}
        elif default_loader == "rasterio":
            loader_params = {"path": {"$ref": input_id}}
        elif default_loader == "numpy":
            loader_params = {"path": {"$ref": input_id}}
        data_sources[data_id] = {
            "loader": default_loader,
            "params": loader_params,
        }
        map_specs.append(
            {
                "name": mapper.name,
                "data": data_id,
                "cmap": mapper.cmap if isinstance(mapper.cmap, str) else getattr(mapper.cmap, "name", "terrain"),
                "alpha": mapper.alpha,
                "cbar": mapper.cbar,
                "draped": mapper.draped,
                "ambient": mapper.ambient,
                "diffuse": mapper.diffuse,
                "specular": mapper.specular,
                "specular_power": mapper.specular_power,
                "smooth_shading": mapper.smooth_shading,
                "eye_dome_lighting": mapper.eye_dome_lighting,
                "light_azimuth": mapper.light_azimuth,
                "light_elevation": mapper.light_elevation,
                "light_intensity": mapper.light_intensity,
                "processors": [
                    {"name": proc.name, "params": _serialize_proc_params(proc)}
                    for proc in mapper.processors
                ],
            }
        )
    return inputs, data_sources, map_specs


def _extract_fig2d_actions(fig: Fig2DObject) -> list[Dict[str, Any]]:
    """Extract fig2d actions from axis state and recorded helpers."""
    actions: list[Dict[str, Any]] = []
    for idx, ax in enumerate(fig.axes):
        recorded = getattr(ax, "_tpz_actions", [])
        for action in recorded:
            enriched = dict(action)
            enriched["axis"] = idx
            actions.append(enriched)
        for loc in ("left", "center", "right"):
            title = ax.get_title(loc=loc)
            if title:
                actions.append({"type": "title", "axis": idx, "text": title, "loc": loc})
        xlabel = ax.get_xlabel()
        if xlabel:
            actions.append({"type": "xlabel", "axis": idx, "text": xlabel})
        ylabel = ax.get_ylabel()
        if ylabel:
            actions.append({"type": "ylabel", "axis": idx, "text": ylabel})
    return actions


def _serialize_proc_params(proc: Any) -> Dict[str, Any]:
    base_keys = {
        "name",
        "apply",
        "recursive",
        "compatible_2d",
        "compatible_3d",
        "2d_compatible",
        "3d_compatible",
    }
    params: Dict[str, Any] = {}
    for key, val in vars(proc).items():
        if key in base_keys:
            continue
        if _is_jsonable(val):
            params[key] = val
    return params


def _serialize_color(value: Any) -> Any:
    """Convert color-like objects to JSON-friendly forms."""
    if value is None:
        return None
    try:
        from pyvista.plotting.colors import Color

        if isinstance(value, Color):
            return list(value.float_rgb)
    except Exception:
        pass
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    return value


def _jsonify(value: Any) -> Any:
    """Recursively convert objects into JSON-serializable structures."""
    if isinstance(value, dict):
        return {key: _jsonify(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(val) for val in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, str):
        return value
    if value is None:
        return None
    color_value = _serialize_color(value)
    if color_value is not value:
        return color_value
    return value


def _is_jsonable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True
