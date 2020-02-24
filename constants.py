MSG_SHELL = """
<html>
<body>
Hello,
<br>
<p>
See below the best listings posted on Craigslist yesterday, sorted based on the agreed score. Please note that some of the listings might have been deleted by the OP.
</p>

{body}

Thank you!
<br>
Zak
</body>
</html>
"""

MSG_LINKS = """
<p>
<b> {title} </b>
<ul style="list-style-type:square;">
   {body_links}
</ul>
</p>
"""


d_COLUMNS = {'results' : ['id', 'url', 'datetime', 'created', 'last_updated', 'price', 'area',
       'bedrooms', 'bathrooms', 'ppsqft', 'lat', 'lng',
       'distance_Uber_cycling', 'duration_Uber_cycling',
       'distance_Uber_transit', 'duration_Uber_transit',
       'distance_Uber_walking', 'duration_Uber_walking',
       'distance_Dropbox_cycling', 'duration_Dropbox_cycling',
       'distance_Dropbox_transit', 'duration_Dropbox_transit',
       'distance_Dropbox_walking', 'duration_Dropbox_walking', 'ppsqft_score',
       'walking_Uber_score', 'transit_Uber_score', 'travel_Uber_score',
       'walking_Dropbox_score', 'cycling_Dropbox_score',
       'travel_Dropbox_score', 'score', 'datestr']}

CACHE_DIR = 'cache/'

SCORE_BOUNDS = {
  'ppsqft': {
    'min': 2,
    'max': 7
  },
  'walking': {
    'min': 8,
    'max': 30
  },
  'bicycling': {
    'min': 8,
    'max': 30
  },
  'transit': {
    'min': 8,
    'max': 30
  },
  'driving': {
    'min': 8,
    'max': 30
  },
}
