"""Produces animation of GOES 16 ABI channel."""
import glob
import os
import sys
from datetime import datetime

import cartopy.crs as ccrs
import cartopy.feature as cfeat
from cartopy.io import shapereader
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.animation import ArtistAnimation
from metpy.plots import add_logo
from netCDF4 import Dataset
import numpy as np


def get_channel_dataset_names(channel):
    """Get dataset names associated with the channel."""
    return glob.glob(os.path.join('..', 'data', 'satellite',
                                  'Channel{:02d}/*'.format(channel)))


def channel_histogram(channel):
    """Produce a histogram of the ABI values."""
    dataset_names = get_channel_dataset_names(channel)
    first_ds = Dataset(dataset_names[0])
    last_ds = Dataset(dataset_names[-1])

    fig = plt.figure(figsize=(10, 7))
    ax = plt.subplot(1, 1, 1)
    ax.hist(first_ds.variables['Sectorized_CMI'][:].compressed().flatten(),
            bins=255, alpha=0.5)
    ax.hist(last_ds.variables['Sectorized_CMI'][:].compressed().flatten(),
            bins=255, alpha=0.5)
    ax.set_title('Channel {}'.format(channel))
    path = os.path.join('..', 'plots', 'GOES16_Histograms')
    plt.savefig(os.path.join(path, 'GOES_Channel_{:02d}_Histogram.png'.format(channel)))


def make_channel_animation(channel):
    """Create the animation."""
    datasets = get_channel_dataset_names(channel)

    # Pull out projection information from the first file,
    # assume it stays the same through the animation
    ds = Dataset(datasets[0])
    data_var = ds.variables['Sectorized_CMI']
    proj_var = ds.variables[data_var.grid_mapping]

    # Create a Globe specifying a spherical earth with the correct radius
    globe = ccrs.Globe(ellipse='sphere', semimajor_axis=proj_var.semi_major,
                       semiminor_axis=proj_var.semi_minor)

    # Create the LCC projection
    proj = ccrs.LambertConformal(central_longitude=proj_var.longitude_of_central_meridian,
                                 central_latitude=proj_var.latitude_of_projection_origin,
                                 standard_parallels=[proj_var.standard_parallel],
                                 globe=globe)

    # Set up a feature for the state/province lines. Tell cartopy not to fill in the polygons
    state_boundaries = cfeat.NaturalEarthFeature(category='cultural',
                                                 name='admin_1_states_provinces_lakes',
                                                 scale='50m', facecolor='none')

    # Read shapefiles with eclipse data
    center_path = shapereader.Reader('../data/eclipse2017_shapefiles_1s/ucenter17_1s.shp')

    # Create the figure and base map
    fig = plt.figure(figsize=(13.25, 10))
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    ax.coastlines(zorder=2)
    ax.coastlines(resolution='50m', color='black')
    ax.add_feature(state_boundaries, linestyle=':', edgecolor='black')
    ax.add_feature(cfeat.BORDERS, linewidth='2', edgecolor='black')

    # Plot the path center
    ax.add_geometries(list(center_path.geometries()), ccrs.PlateCarree(),
                      edgecolor='None', facecolor='red', alpha=0.5)

    # List used to store the contents of all frames.
    # Each item in the list is a tuple of (image, text)
    artists = []

    # How much to downsample (1 is no downsampling)
    downsample = 1

    # Get the animation parameters dictionary for this channel
    channel_params = animation_parameters[channel]

    for ds in datasets:
        # Load the NetCDF dataset
        nc = Dataset(ds)

        # Pull out the image data, x and y coordinates, and the time. Also go ahead and
        # convert the time to a python datetime
        x = nc.variables['x'][::downsample]
        y = nc.variables['y'][::downsample]
        timestamp = datetime.strptime(nc.start_date_time, '%Y%j%H%M%S')
        img_data = nc.variables['Sectorized_CMI'][::downsample]

        # Remove GOES artifact where center of eclipse is white
        img_data[np.where(img_data <= 0.0001)] = 0

        # Plot the image and the timestamp. We save the results of these plotting functions
        # so that we can tell the animation that these two things should be drawn as one
        # frame in the animation
        im = ax.imshow(img_data, extent=(x.min(), x.max(), y.min(), y.max()),
                       origin='upper', vmin=0.05, vmax=0.95)

        # Set colormap
        im.set_cmap(channel_params['cmap'])

        # Set norm
        im.set_norm(channel_params['norm'])
        # Add text (aligned to the right); save the returned object so we can manipulate it.
        text_time = ax.text(0.99, 0.01, timestamp.strftime('%d %B %Y %H%MZ'),
                            horizontalalignment='right', transform=ax.transAxes,
                            color='white', fontsize='x-large',
                            weight='bold', animated=True)

        text_channel = ax.text(0.5, 0.97, 'Experimental GOES-16 Ch.{}'.format(channel),
                               horizontalalignment='center', transform=ax.transAxes,
                               color='white', fontsize='large',
                               weight='bold', animated=True)

        # Make the text stand out even better using matplotlib's path effects
        outline_effect = [patheffects.withStroke(linewidth=2, foreground='black')]
        text_time.set_path_effects(outline_effect)
        text_channel.set_path_effects(outline_effect)

        # Add the MetPy Logo
        fig = add_logo(fig, x=25, y=25, size='large')

        # Stuff them in a tuple and add to the list of things to animate
        artists.append((im, text_time, text_channel))

    # Create the animation--in addition to the required args, we also state that each
    # frame should last 200 milliseconds
    anim = ArtistAnimation(fig, artists, interval=200., blit=False)
    anim.save(os.path.join('..', 'animations', 'GOES16',
                           'GOES16_Channel_{:02d}.mp4'.format(channel)))


# Grab the command line argument for the channel
channel = int(sys.argv[1])

print('Producing histogram of channel {}'.format(channel))
channel_histogram(channel)

animation_parameters = {1: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        2: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        3: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        4: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        5: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        6: {'cmap': 'Greys_r', 'norm': plt.Normalize(0, 1)},
                        7: {'cmap': 'Greys_r', 'norm': plt.Normalize(240, 360)},
                        8: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 260)},
                        9: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 270)},
                        10: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 280)},
                        11: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 320)},
                        12: {'cmap': 'Greys_r', 'norm': plt.Normalize(210, 290)},
                        13: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 330)},
                        14: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 330)},
                        15: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 330)},
                        16: {'cmap': 'Greys_r', 'norm': plt.Normalize(200, 290)}}

print('Animating channel {}'.format(channel))
make_channel_animation(channel)
