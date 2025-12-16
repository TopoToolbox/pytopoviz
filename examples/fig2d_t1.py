"""Example figure with topography and multi-directional hillshade overlay."""

import matplotlib.pyplot as plt
import topotoolbox as ttb
from cmcrameri import cm

import pytopoviz as tpz

# Apply the dark presentation style before plotting
# tpz.set_style('paper')
tpz.set_style('dark_pres_mono')
# tpz.set_style('color_pres')
# tpz.set_style('bw_paper')

# Load the sample DEM
dem = ttb.load_dem("bigtujunga")

# Build the elevation MapObject and attach processors
# - multishade_processor() will create and return a shaded MapObject
elevation = tpz.MapObject(dem, cmap=cm.batlowW, cbar="Elevation (m)")
nan_proc = tpz.processor.nan_below()
nan_proc.threshold = 500
elevation.processors.append(nan_proc)

smooth = tpz.processor.gaussian_smooth()
smooth.sigma = 2
elevation.processors.append(smooth)


# Instantiate processor, tweak parameters, then attach
shade_proc = tpz.processor.multishade()
shade_proc.azimuths = (280.0, 250.0)
elevation.processors.append(shade_proc)
# Optional: smooth the base values before hillshading
# smooth_proc = tpz.processor.gaussian_smooth(sigma=1.5)
# elevation.processors.append(smooth_proc)
# elevation.processors.append(tpz.hillshade_processor())

# Plot elevation; processor automatically adds the hillshade to the same axis
fig, ax = tpz.quickmap(elevation)
ax.set_title("Bigtujunga DEM")

plt.show()
