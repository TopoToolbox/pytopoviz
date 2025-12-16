"""Processing helpers to transform MapObjects before plotting.

Author: B.G.
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .map_object import MapObject


@dataclass
class ProcessingFunction:
    name: str
    apply: Callable[["ProcessingFunction", MapObject], MapObject | Sequence[MapObject] | None]
    recursive: bool = True

    def __call__(self, mapper: MapObject):
        return self.apply(self, mapper)


class ProcessorFactory:
    """Helper to build ProcessingFunction instances.

    Author: B.G.
    """

    @staticmethod
    def build(
        name: str,
        apply: Callable[["ProcessingFunction", MapObject], MapObject | Sequence[MapObject] | None],
        recursive: bool = True,
        **params,
    ) -> ProcessingFunction:
        """Create a ProcessingFunction and attach provided params as attributes."""
        proc = ProcessingFunction(name=name, apply=apply, recursive=recursive)
        for key, val in params.items():
            setattr(proc, key, val)
        return proc


def is_plottable(obj) -> bool:
    """Return True when object can be rendered by topoviz."""
    return isinstance(obj, MapObject)


def expand_plottables(mapper: MapObject) -> list[MapObject]:
    """Apply processors in-order and collect plottables depth-first."""

    def walk(current: MapObject) -> list[MapObject]:
        collected: list[MapObject] = [current]
        for proc in current.processors:
            produced = proc(current)
            if produced is None:
                continue
            produced_list: Iterable = produced if isinstance(produced, (list, tuple)) else (produced,)
            for item in produced_list:
                if not is_plottable(item):
                    continue
                collected.extend(walk(item))
        return collected

    return walk(mapper)


class _ProcessorNamespace:
    """Namespace-style accessor for built-in processors grouped by module."""

    def __init__(self):
        from . import filter2d, masknan, shading2d  # local import to avoid cycles

        self.masknan = masknan
        self.shading2d = shading2d
        self.filter2d = filter2d
        # Convenient top-level aliases
        self.nan_equal = masknan.nan_equal
        self.nan_below = masknan.nan_below
        self.nan_above = masknan.nan_above
        self.hillshade = shading2d.hillshade_processor
        self.multishade = shading2d.multishade_processor
        self.gaussian_smooth = filter2d.gaussian_smooth


# Expose a shared namespace instance
# This enables convenient access such as tpz.processor.multishade()
processor = _ProcessorNamespace()
