"""pytopoviz placeholder package."""

__version__ = "0.0.0"

from .map_object import MapObject
from .hillshading import hillshade, multishade
from .fig2d import Fig2DObject, quickmap
from .fig3d import quickmap3d
from .style2d import (
    apply_dark_pres_mono_style,
    apply_color_pres_style,
    apply_paper_style,
    apply_bw_paper_style,
    set_style,
)
from .helper2d import convert_ticks_to_km, add_grid_crosses

__all__ = [
    "MapObject",
    "Fig2DObject",
    "hillshade",
    "multishade",
    "quickmap",
    "quickmap3d",
    "apply_dark_pres_mono_style",
    "apply_color_pres_style",
    "apply_paper_style",
    "apply_bw_paper_style",
    "set_style",
    "convert_ticks_to_km",
    "add_grid_crosses",
    "__version__",
]
