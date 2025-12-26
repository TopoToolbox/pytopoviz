"""3D-only processing helpers.

Author: B.G.
"""

from .map_object import MapObject
from .processing import ProcessingFunction, ProcessorFactory


def scale(factor: float) -> ProcessingFunction:
    """Return a 3D-only processor that scales 3D surface height."""

    def process(self: ProcessingFunction, mapper: MapObject):
        mapper.z_scale_factor = mapper.z_scale_factor * self.factor
        return None

    return ProcessorFactory.build(
        "scale",
        process,
        recursive=True,
        compatible_2d=False,
        compatible_3d=True,
        factor=float(factor),
    )


def double_scale() -> ProcessingFunction:
    """Convenience processor: multiply values by 2."""
    return scale(2.0)


def halve_scale() -> ProcessingFunction:
    """Convenience processor: multiply values by 0.5."""
    return scale(0.5)


def tenfold() -> ProcessingFunction:
    """Convenience processor: multiply values by 10."""
    return scale(10.0)


def tenthfold() -> ProcessingFunction:
    """Convenience processor: multiply values by 0.1."""
    return scale(0.1)


BUILTIN_3D = {
    "scale": scale,
    "double_scale": double_scale,
    "halve_scale": halve_scale,
    "tenfold": tenfold,
    "tenthfold": tenthfold,
}
