MSG_SHELL = """
<html>
<body>
Hello,
<br>
<p>
See below the best listings posted on Craigslist yesterday, sorted based on the agreed score. Please note that some of the listings might have been deleted by the OP.
</p>
<p>
<b> 3 Bed listings </b>
<ul style="list-style-type:square;">
   {l_li_3}
</ul>
</p>

<p>
<b> 2 Bed listings </b>
<ul style="list-style-type:square;">
   {l_li_2}
</ul>
</p>
Thank you!
<br>
Zak
</body>
</html>
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

MIN_PPSQFT, MAX_PPSQFT = (2, 7)
MIN_WALKING, MAX_WALKING = (0, 30)
MIN_CYCLING, MAX_CYCLING = (0, 30)
MIN_TRANSIT, MAX_TRANSIT = (0, 30)
