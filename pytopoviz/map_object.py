"""Container for visualization settings tied to a GridObject."""

from typing import Optional, Union

import numpy as np
from matplotlib.colors import Colormap

from topotoolbox import GridObject

__all__ = ["MapObject"]


class MapObject:
    """Store visualization defaults for a GridObject."""

    def __init__(
        self,
        grid: GridObject,
        cmap: Union[str, Colormap] = "terrain",
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        alpha: float = 1.0,
        cbar: Optional[str] = None,
    ) -> None:
        """
        Parameters
        ----------
        grid : GridObject
            The grid to visualize.
        cmap : str or matplotlib.colors.Colormap, optional
            The colormap to apply when displaying the grid.
        vmin : float, optional
            Lower bound for normalization. Defaults to the minimum finite value.
        vmax : float, optional
            Upper bound for normalization. Defaults to the maximum finite value.
        alpha : float, optional
            Transparency value in [0, 1]. Defaults to 1.0 (opaque).
        cbar : str or None, optional
            If a string, use it as the colorbar label when plotting.
        """
        self._grid = grid
        self._cmap = cmap
        self._alpha = alpha
        self._cbar = cbar

        self._value = self._prepare_value(grid.z)

        self._vmin = np.nanmin(self._value) if vmin is None else vmin
        self._vmax = np.nanmax(self._value) if vmax is None else vmax

    @staticmethod
    def _prepare_value(value: np.ndarray) -> np.ndarray:
        """Return float32 array with non-finite entries as NaN."""
        val = np.array(value, dtype=np.float32, copy=True)
        val[~np.isfinite(val)] = np.nan
        return val

    @property
    def grid(self) -> GridObject:
        return self._grid

    @grid.setter
    def grid(self, grid: GridObject) -> None:
        self._grid = grid
        self.value = grid.z

    @property
    def cmap(self) -> Union[str, Colormap]:
        return self._cmap

    @cmap.setter
    def cmap(self, cmap: Union[str, Colormap]) -> None:
        self._cmap = cmap

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        self._alpha = alpha

    @property
    def vmin(self) -> float:
        return self._vmin

    @vmin.setter
    def vmin(self, vmin: float) -> None:
        self._vmin = vmin

    @property
    def vmax(self) -> float:
        return self._vmax

    @vmax.setter
    def vmax(self, vmax: float) -> None:
        self._vmax = vmax

    @property
    def value(self) -> np.ndarray:
        return self._value

    @value.setter
    def value(self, value: np.ndarray) -> None:
        self._value = self._prepare_value(value)
        self._vmin = np.nanmin(self._value)
        self._vmax = np.nanmax(self._value)

    @property
    def cbar(self) -> Optional[str]:
        return self._cbar

    @cbar.setter
    def cbar(self, label: Optional[str]) -> None:
        self._cbar = label

    def set_nan_equal(self, target: float) -> None:
        """Set values equal to ``target`` to NaN."""
        self.value[self.value == target] = np.nan

    def set_nan_below(self, threshold: float) -> None:
        """Set values less than or equal to ``threshold`` to NaN."""
        self.value[self.value <= threshold] = np.nan

    def set_nan_above(self, threshold: float) -> None:
        """Set values greater than or equal to ``threshold`` to NaN."""
        self.value[self.value >= threshold] = np.nan
