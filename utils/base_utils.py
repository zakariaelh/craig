from numbers import Number
import requests
import logging 
import datetime
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import pandas as pd
import numpy as np
from cachier import cachier
from credentials import API_KEY

from constants import CACHE_DIR

logging.root.setLevel(logging.DEBUG)

def requests_retry_session(
    retries=3,
    backoff_factor=1,
    status_forcelist=(500, 502, 504),
    session=None,
    ):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# data utils 

def next_weekday(weekday=0):
    # 0 = Monday, 1=Tuesday, 2=Wednesday...
    d = datetime.datetime.now()
    d = d.replace(hour=0, minute=0, second=0, microsecond=0)
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    next_wd = d + datetime.timedelta(days=days_ahead,hours=9)
    # convert to timestamp (epoch)
    epoch = int(next_wd.strftime("%s"))
    return epoch

def geometric_mean(l):
    if 0 in l:
        return 0 
    else:
        return np.exp(np.mean(np.log(l)))
    
    
def format_sqft(x):
    """Converts sqft input into integer."""
    if isinstance(x, Number):
        return int(x) + A
    elif x[:x.find('ft2')].isnumeric():
        return int(x[:x.find('ft2')])
    else:
        return None
        
def format_price(x):
    """Converts price input into integer."""
    if isinstance(x, Number):
        return int(x)
    elif x[(x.find('$')+1):].isnumeric():
        return int(x[(x.find('$')+1):])
    else:
        return None
    
def exclude_smalldesc(df_res, thresh = 100):
    """
    Excludes listings with small descriptions.
    
    :params df_res: pd Dataframe with column called "body"
    :params thresh: exclude listing whose description length is below thresh
    """
    
    small_desc = df_res.body.apply(lambda x: len(str(x))) <= thresh
    df_res = df_res[~small_desc]
    if sum(small_desc) > 0:
        logging.info({'msg': 'Number of rows removed because the description is below {thresh}: {n_rows}'.format(
            thresh = thresh,
            n_rows = sum(small_desc)
        )})
    
    return df_res

def clean_area(df_res):
    """
    Cleans the price column by turning it to integer and removing rows with 0.
    
    :params df_res: pd dataframe with column called "area" 
    """
    # format area column 
    df_res['area'] = df_res.area.apply(format_sqft)

    # remove rows with area = 0
    row_0 = (df_res.area == 0)
    df_res = df_res[~row_0]
    if sum(row_0) > 0:
        logging.info({'msg': 'Number of rows removed because they have 0 in area are: {n_rows}'.format(
            n_rows = sum(row_0)
        )})
        
    return df_res


def clean_price(df_res):
    """
    Cleans the price column by formating it and turning it to integer and removing rows with 0.
    
    :params df_res: pd dataframe with column called "price" 
    """
    # format area column 
    df_res['price'] = df_res.price.apply(format_price)

    # remove rows with area = 0
    row_0 = (df_res.price == 0)
    df_res = df_res[~row_0]
    
    # spit logs if rows are being removed
    if sum(row_0) > 0:
        logging.info({'msg': 'Number of rows removed because they have 0 in price are: {n_rows}'.format(
            n_rows = sum(row_0)
        )})
        
    return df_res

def remove_None(df_res, l_NONE_COLUMNS = ['price', 'area', 'geotag']):
    # rows with None in them 
    row_None = df_res[l_NONE_COLUMNS].isnull().any(1)
    df_res = df_res[~row_None]

    # spit logs if rows are being removed
    if sum(row_None) > 0:
        logging.info({'msg': 'Number of rows removed because they have None in {l_NONE_COLUMNS} are: {n_rows}'.format(
            l_NONE_COLUMNS = l_NONE_COLUMNS,
            n_rows = sum(row_None)
        )})
        
    return df_res

def get_lat(x):
    """Converts geotag into lat"""
    if x is None:
        return None
    else:
        return x[0]

def get_lng(x):
    """Converts geotag into lng"""
    if x is None:
        return None
    else:
        return x[1]


@cachier(stale_after=datetime.timedelta(days=30), cache_dir=CACHE_DIR)
def get_travel_info(origin, destination, mode='walking'):
    """
    Returns the distance and duration from origin to destination using mode of transportation.
    
    :params origin: tuple (lat, lng) of origin
    :params destination: tuple (lat, lng) of destination
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?&origins={lat_origin}%2C{lng_origin}&destinations={lat_dest}%2C{lng_dest}&units=metric&mode={mode}&key={key}"
    request_url = base_url.format(
        lat_origin=origin[0],
        lng_origin=origin[1],
        lat_dest=destination[0],
        lng_dest=destination[1],
        mode=mode,
        key=API_KEY
    )
    if mode == "transit":
        request_url = "&".join([
            request_url, 
            "transit_routing_preference=less_walking",
            "departure_time={}".format(next_weekday()) # next monday 9am 
        ])
        
    res = requests_retry_session(retries=3).get(request_url)
    
    try:
        dist_meters = res.json()['rows'][0]['elements'][0]['distance']['value'] # distance in meters
        dist = round(dist_meters / 1000, 2) # convert to km 
    except Exception as e:
        logging.critical({
            'error': e,
            'request' : res.json()
        })
        dist = None
    
    try:
        duration_seconds = res.json()['rows'][0]['elements'][0]['duration']['value'] # distance in meters
        duration = int(duration_seconds / 60) # converts to min 
    except Exception as e:
        logging.critical({
            'error': e,
            'request' : res.json()
        })
        duration = None
        
    # sleep in order not to stay below quota
    time.sleep(1.5)

    return dist, duration 


