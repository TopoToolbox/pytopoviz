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
    """Apply processors to a MapObject and collect all plottable outputs."""
    plottables: list[MapObject] = []
    queue: list[MapObject] = [mapper]

    while queue:
        current = queue.pop(0)
        base_recursive = [p for p in current.processors if p.recursive]

        for proc in current.processors:
            produced = proc(current)

            if produced is not None:
                produced_list: Iterable = produced if isinstance(produced, (list, tuple)) else (produced,)
                for item in produced_list:
                    if not is_plottable(item):
                        continue
                    for rp in base_recursive:
                        if rp not in item.processors:
                            item.processors.append(rp)
                    queue.append(item)
        plottables.append(current)

    return plottables


class _ProcessorNamespace:
    """Namespace-style accessor for built-in processors grouped by module."""

    def __init__(self):
        from . import masknan, shading2d  # local import to avoid cycles

        self.masknan = masknan
        self.shading2d = shading2d


# Expose a shared namespace instance
processor = _ProcessorNamespace()
