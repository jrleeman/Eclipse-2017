import json
import os
import time
from datetime import datetime
from urllib.request import urlopen

#
# Only change these start/end times. Goes up to the last hour, but does
# not include it.
#
start_time = datetime(2017, 8, 8, 0) # 15
end_time = datetime(2017, 8, 9, 0) # 21

def download_data(uri, max_attempts=6):
    """Fetch the data from the IEM
    The IEM download service has some protections in place to keep the number
    of inbound requests in check.  This function implements an exponential
    backoff to keep individual downloads from erroring.
    Args:
      uri (string): URL to fetch
    Returns:
      string data
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            data = urlopen(uri, timeout=300).read()
            if data is not None and not data.startswith(b'ERROR'):
                return data
        except Exception as exp:
            print('download_data(%s) failed with %s' % (uri, exp))
            time.sleep(5)
        attempt += 1

    print('Exhausted attempts to download, returning empty data')
    return ''



base_url = 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'

request_url = base_url + 'data=all&tz=Etc/UTC&format=comma&latlon=yes&'

request_url += start_time.strftime('year1=%Y&month1=%m&day1=%d&')
request_url += end_time.strftime('year2=%Y&month2=%m&day2=%d&')

states = """AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
 MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
 WA WI WV WY"""

# IEM quirk to have Iowa AWOS sites in its own labeled network
networks = ['AWOS']
for state in states.split():
    networks.append('%s_ASOS' % (state,))

# Outfile
path = os.path.join('..', 'data', 'surface_obs', 'ASOS_surface_obs.txt')
try:
    os.remove(path)  # Remove any old data sitting there.
except:
    pass
f = open(path, 'wb')

for network in networks:
    # Get metadata
    uri = ('https://mesonet.agron.iastate.edu/'
           'geojson/network/%s.geojson') % (network,)
    data = urlopen(uri)
    jdict = json.load(data)
    for site in jdict['features']:
        faaid = site['properties']['sid']
        sitename = site['properties']['sname']
        uri = '%s&station=%s' % (request_url, faaid)
        print(('Network: %s Downloading: %s [%s]'
               ) % (network, sitename, faaid))
        data = download_data(uri)
        f.write(data)
f.close()
