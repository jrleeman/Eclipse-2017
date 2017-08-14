import cartopy.crs as ccrs
import cartopy.feature as feat
from cartopy.io import shapereader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import ArtistAnimation
from matplotlib import patheffects
from metpy.plots import add_logo
from datetime import datetime, timedelta

# Read shapefiles with eclipse data
umbra_path = shapereader.Reader('../data/eclipse2017_shapefiles/w_upath17.shp')
center_path = shapereader.Reader('../data/eclipse2017_shapefiles_1s/ucenter17_1s.shp')
umbras = shapereader.Reader('../data/eclipse2017_shapefiles_1s/umbra17_1s.shp')

# Setup map projection
proj = ccrs.LambertConformal(central_longitude=-100.0, central_latitude=45.0)

# Grab state boundaries
state_boundaries = feat.NaturalEarthFeature(category='cultural',
                                            name='admin_1_states_provinces_lines',
                                            scale='50m', facecolor='none')

# Create the figure and an axes set to the projection
fig = plt.figure(figsize=(20, 10))
ax = fig.add_subplot(1, 1, 1, projection=proj)

# Add some various map elements to the plot to make it recognizable
ax.add_feature(feat.LAND, zorder=-1)
ax.add_feature(feat.OCEAN, zorder=-1)
ax.add_feature(feat.LAKES, zorder=-1)
ax.coastlines(resolution='50m', zorder=2, color='black')
ax.add_feature(state_boundaries, edgecolor='black')
ax.add_feature(feat.BORDERS, edgecolor='black')

# Set plot bounds
ax.set_extent([235., 290., 20., 55.])

# Plot a shaded umbra path
ax.add_geometries(list(umbra_path.geometries()), ccrs.PlateCarree(), edgecolor='None', facecolor='black', alpha=0.5)

# Plot the path center
ax.add_geometries(list(center_path.geometries()), ccrs.PlateCarree(), edgecolor='None', facecolor='red', alpha=0.5)

# Add the MetPy Logo
fig = add_logo(fig, x=25, y=25, size='large')

# Make the text stand out even better using matplotlib's path effects
outline_effect = [patheffects.withStroke(linewidth=2, foreground='black')]

# Only plot every 5 minutes
sc = ax.add_geometries(list(umbras.geometries())[::300], ccrs.PlateCarree(), edgecolor='black', facecolor='#f4d942', alpha=0.5)

plt.savefig('../plots/event_path.png', bbox_inches='tight')
