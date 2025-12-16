from pytopoviz import MapObject, quickmap3d
import topotoolbox as ttb

# Load the sample DEM
dem = ttb.load_dem("bigtujunga")

quickmap3d(dem, screenshot_path="scene.png")
