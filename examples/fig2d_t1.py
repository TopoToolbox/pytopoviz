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

# Build MapObjects for the elevation and the combined hillshade
elevation = tpz.MapObject(dem, cmap=cm.batlowW, cbar="Elevation (m)")
shade = tpz.multishade(elevation)

# Plot the elevation and hillshade together
figo = tpz.quickmap(elevation, shade)
figo.ax.set_title("Bigtujunga DEM")

plt.show()
