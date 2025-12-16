"""pytopoviz placeholder package."""

__version__ = "0.0.0"

from .map_object import MapObject
from .hillshading import hillshade, multishade
from .fig2d import Fig2DObject, quickmap
from .fig3d import quickmap3d
from .processing import (
    ProcessorFactory,
    ProcessingFunction,
    expand_plottables,
    is_plottable,
    processor,
)
from .masknan import nan_above, nan_below, nan_equal, BUILTIN_MASK_NAN
from .shading2d import hillshade_processor, multishade_processor, BUILTIN_SHADING
from .filter2d import gaussian_smooth, BUILTIN_FILTERS
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
    "ProcessingFunction",
    "ProcessorFactory",
    "expand_plottables",
    "is_plottable",
    "processor",
    "nan_equal",
    "nan_below",
    "nan_above",
    "hillshade_processor",
    "multishade_processor",
    "gaussian_smooth",
    "BUILTIN_MASK_NAN",
    "BUILTIN_SHADING",
    "BUILTIN_FILTERS",
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
