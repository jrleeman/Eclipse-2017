from datetime import datetime
import glob
import os
import sys
from siphon.catalog import TDSCatalog

#
# Only change these start/end times. Goes up to the last hour, but does
# not include it.
#
start_time = datetime(2017, 8, 21, 15)
end_time = datetime(2017, 8, 21, 21)

channel = int(sys.argv[1])

# Delete everything in the channel folder.
path = os.path.join('..', 'data', 'satellite',
                    'Channel{:02d}'.format(channel))
files = glob.glob(os.path.join(path, '*'))
for item in files:
    os.remove(item)

# String format of the date storage on THREDDS
date_str = start_time.strftime('%Y%m%d')

base_url= 'http://thredds-test.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/CONUS/Channel'


cat = TDSCatalog('{}{:02d}/{}/catalog.xml'.format(base_url,channel, date_str))
datasets = cat.datasets.filter_time_range(start_time, end_time)
for i, ds in enumerate(datasets):
    print('Downloading {}'.format(ds.name))
    ds.download(os.path.join('..', 'data', 'satellite',
                             'Channel{:02d}'.format(channel),
                             '{:03d}_GOES16_CONUS_{}'.format(i, ds.name[22:28])))
