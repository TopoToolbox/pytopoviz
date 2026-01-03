Workflows
=========

Workflows are JSON files that describe how to load data, build ``MapObject``
layers, and render figures in 2D or 3D. The goal is to share a visualization
recipe without bundling the original data. Workflows can be interactive (prompt
for inputs) or non-interactive (all inputs provided up front).

Author: B.G.

Overview
--------

1. **Inputs** define values that must be provided at runtime (paths, numbers).
2. **Data sources** define how to load grids using built-in loaders.
3. **Maps** define visualization settings and processor chains.
4. **Figure settings** define how to render 2D or 3D outputs.
5. **Run mode** chooses which figure(s) to render.

Creating workflows
------------------

There are two ways to create a workflow:

Factory (recommended)
^^^^^^^^^^^^^^^^^^^^

Use an existing figure to generate a workflow skeleton that captures map
settings, processors, and figure style:

.. code-block:: python

  import pytopoviz as tpz

  # After building a figure
  wf = tpz.workflow_from_fig2d(fig2d)
  wf.to_file("workflow.json")

  # Or for 3D figures
  wf = tpz.workflow_from_fig3d(fig3d)
  wf.to_file("workflow.json")

Manual
^^^^^^

Create a ``Workflow`` directly from a JSON spec and save it. This is useful
when you want full control over inputs or loaders.

.. code-block:: python

  from pytopoviz.workflow import Workflow

  spec = {
    "version": 1,
    "interactive": true,
    "inputs": {
      "dem_path": {"type": "path", "default": "dem.tif"}
    },
    "data_sources": {
      "dem": {"loader": "topotoolbox.read_tif", "params": {"path": {"$ref": "dem_path"}}}
    },
    "maps": [{"name": "elevation", "data": "dem", "cmap": "terrain"}],
    "run": {"mode": "fig2d"}
  }

  wf = Workflow(spec)
  wf.to_file("workflow.json")

JSON structure
--------------

Minimal example:

.. code-block:: json

  {
    "version": 1,
    "interactive": true,
    "inputs": {
      "dem_path": {
        "type": "path",
        "prompt": "Select a DEM file",
        "required": true
      },
      "threshold": {
        "type": "float",
        "default": 500.0
      }
    },
    "data_sources": {
      "dem": {
        "loader": "topotoolbox.read_tif",
        "params": {"path": {"$ref": "dem_path"}}
      }
    },
    "maps": [
      {
        "name": "elevation",
        "data": "dem",
        "cmap": "terrain",
        "cbar": "Elevation (m)",
        "processors": [
          {"name": "nan_below", "params": {"threshold": {"$ref": "threshold"}}},
          {"name": "multishade", "params": {"alpha": 0.6}}
        ]
      }
    ],
    "fig2d": {
      "style": "dark_pres_mono",
      "actions": [
        {"type": "title", "axis": 0, "text": "Bigtujunga DEM"},
        {"type": "xlabel", "axis": 0, "text": "Easting (km)"},
        {"type": "ylabel", "axis": 0, "text": "Northing (km)"},
        {"type": "convert_ticks_to_km", "axis": 0},
        {"type": "add_grid_crosses", "axis": 0}
      ]
    },
    "fig3d": {
      "background": "black",
      "show_scalar_bar": true,
      "screenshot_path": "scene.png",
      "show": true
    },
    "run": {"mode": "fig3d"}
  }

Built-in loaders
----------------

- ``topotoolbox.read_tif`` (default): loads a DEM from a GeoTIFF path. Params: ``path`` (required).
- ``topotoolbox.load_dem``: loads a DEM from a file path or named dataset. Params: ``source`` (required).
- ``rasterio``: loads a raster file (first band). Params: ``path`` (required), ``band`` (optional).
- ``numpy``: loads ``.npy`` or ``.npz``. Params: ``path`` (required), ``key`` (optional for ``.npz``).

Inputs
------

Input ``type`` controls how values are parsed:

- ``path``: string path
- ``str``: string
- ``int``: integer
- ``float``: floating point
- ``bool``: true/false (accepts ``true/false/1/0``)
- ``json``: parsed as JSON

CLI usage
---------

Run a workflow via the CLI (interactive prompts by default):

.. code-block:: bash

  pytopoviz-run workflow.json

GUI prompts (one dialog per input):

.. code-block:: bash

  pytopoviz-run workflow.json --gui

Generate a param file with defaults:

.. code-block:: bash

  pytopoviz-run workflow.json --file

Run from a param file:

.. code-block:: bash

  pytopoviz-run workflow.json --file workflow.json.params

Fast mode (only loader inputs prompted; other values use defaults):

.. code-block:: bash

  pytopoviz-run workflow.json --fast

Factory from maps
-----------------

You can generate a workflow skeleton from an existing ``Fig2DObject`` or
``Fig3DObject``:

.. code-block:: python

  import pytopoviz as tpz
  wf = tpz.workflow_from_fig3d(fig3d)
  wf.to_file("workflow.json")

Figure actions
--------------

``fig2d.actions`` allows common axis tweaks to be replayed in workflows.
Each action can specify an ``axis`` index.

Supported actions:

- ``title``: set axis title (``text``)
- ``xlabel``: set x label (``text``)
- ``ylabel``: set y label (``text``)
- ``xlim``/``ylim``: set limits (``min``, ``max``)
- ``convert_ticks_to_km``: apply kilometer formatter (``axes`` = "x"/"y"/"both")
- ``add_grid_crosses``: overlay grid crosses (``color``, ``size``, ``linewidth``, ``alpha``, ``include_minor``)
