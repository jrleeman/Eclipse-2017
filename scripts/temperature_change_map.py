"""Create a map of temperature change during the eclipse."""
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import cartopy.feature as feat
from cartopy.io import shapereader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.animation import ArtistAnimation
from metpy.plots import add_logo
import pandas as pd


def strip_data(df):
    """Remove unused columns from the data."""
    names = [' dwpf', ' relh', ' drct',
             ' sknt', ' p01i', ' alti', ' mslp', ' vsby', ' gust', ' skyc1',
             ' skyc2', ' skyc3', ' skyc4', ' skyl1', ' skyl2', ' skyl3',
             ' skyl4', ' presentwx', ' metar']
    for colname in names:
        del df[colname]
    return df


def get_within_time(df, time, tolerance):
    """Get data within tolerance of time."""
    start_time = time - tolerance
    end_time = time + tolerance
    return df[(df['valid'] >= start_time) & (df['valid'] <= end_time)]


def get_temperature_change(df, time, span, tolerance):
    """Calculate station based temperature change."""
    first_time_data = get_within_time(df, time - span, tolerance)
    last_time_data = get_within_time(df, time, tolerance)

    df = pd.merge(first_time_data, last_time_data, on='station')
    df['temp_change'] = df['tmpf_y'] - df['tmpf_x']
    df['lon'] = df['lon_x']
    df['lat'] = df['lat_x']
    del df['valid_x']
    del df['lon_x']
    del df['lat_x']
    del df['tmpf_x']
    del df['valid_y']
    del df['lon_y']
    del df['lat_y']
    del df['tmpf_y']
    return df


df = pd.read_csv('../data/surface_obs/ASOS_surface_obs.txt', comment='#', na_values='M')
df['valid'] = pd.to_datetime(df['valid'], format='%Y-%m-%d %H:%M', errors='coerce')
df = strip_data(df)
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['tmpf'] = pd.to_numeric(df['tmpf'], errors='coerce')

# Make the text stand out even better using matplotlib's path effects
outline_effect = [patheffects.withStroke(linewidth=2, foreground='black')]

proj = ccrs.LambertConformal(central_longitude=-100.0, central_latitude=45.0)
state_boundaries = feat.NaturalEarthFeature(category='cultural',
                                            name='admin_1_states_provinces_lines',
                                            scale='50m', facecolor='none')

# Create the figure and an axes set to the projection
fig = plt.figure(figsize=(13.75, 10))
ax = fig.add_subplot(1, 1, 1, projection=proj)
plt.subplots_adjust(left=0, bottom=0.055, right=1, top=1, wspace=0, hspace=0)

# Add some various map elements to the plot to make it recognizable
ax.add_feature(feat.LAND, zorder=-1)
ax.add_feature(feat.OCEAN, zorder=-1)
ax.add_feature(feat.LAKES, zorder=-1)
ax.coastlines(resolution='50m', zorder=2, color='black')
ax.add_feature(state_boundaries, edgecolor='black')
ax.add_feature(feat.BORDERS, edgecolor='black')
# Set plot bounds
ax.set_extent([235., 290., 20., 55.])

start_time = datetime(2017, 8, 21, 15)
end_time = datetime(2017, 8, 21, 21)
interval = timedelta(minutes=10)

# Read shapefiles with eclipse data
umbra_path = shapereader.Reader('../data/eclipse2017_shapefiles/w_upath17.shp')
center_path = shapereader.Reader('../data/eclipse2017_shapefiles_1s/ucenter17_1s.shp')
umbras = shapereader.Reader('../data/eclipse2017_shapefiles_1s/umbra17_1s.shp')

# Add the MetPy Logo
fig = add_logo(fig, x=0, y=98, size='large')

times = []
artists = []
time = start_time
while time <= end_time:
    times.append(time)
    time = time + interval

# Plot a shaded umbra path
ax.add_geometries(list(umbra_path.geometries()), ccrs.PlateCarree(),
                  edgecolor='None', facecolor='black', alpha=0.5)

# Plot the path center
ax.add_geometries(list(center_path.geometries()), ccrs.PlateCarree(),
                  edgecolor='None', facecolor='red', alpha=0.5)

# Time that the 1 second umbras file begins
umbras_start_time = datetime(2017, 8, 21, 17, 12, 0)
umbra_shapes = list(umbras.geometries())
for time in times:
    print(time)
    umbra_number = (time - umbras_start_time).seconds

    delta_df = get_temperature_change(df, time, timedelta(hours=1),
                                      timedelta(minutes=10))
    longitude = delta_df['lon']
    latitude = delta_df['lat']
    temperature = delta_df['temp_change']
    # Plot stations as colored dots
    sc = ax.scatter(longitude, latitude, c=temperature,
                    transform=ccrs.PlateCarree(),
                    cmap=plt.get_cmap('coolwarm'), norm=plt.Normalize(-10, 10))

    text_time = ax.text(0.99, 0.01, time.strftime('%d %B %Y %H:%M:%SZ'),
                        horizontalalignment='right', transform=ax.transAxes,
                        color='white', fontsize='x-large',
                        weight='bold', animated=True)
    text_time.set_path_effects(outline_effect)

    if umbra_number >= 0:
        try:
            scu = ax.add_geometries(umbra_shapes[umbra_number],
                                    ccrs.PlateCarree(), edgecolor='black',
                                    facecolor='#f4d942', alpha=0.5)
            artists.append((sc, scu, text_time))
        except:
            # No umbra for this time
            artists.append((sc, text_time))


cb = plt.colorbar(sc, orientation='horizontal', fraction=0.035,
                  pad=0.01, aspect=40)
cb.set_label(u'Temperature Change \N{DEGREE FAHRENHEIT}', fontsize=14)
cb.ax.tick_params(labelsize=12)

anim = ArtistAnimation(fig, artists, interval=400., blit=False)

anim.save('../animations/surface_temperature_change_1hr.mp4')
