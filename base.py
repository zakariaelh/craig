import logging
import datetime

import pandas as pd
from craigslist import CraigslistHousing

from utils.base_utils import * 
from constants import *
from cachier import cachier

logging.root.setLevel(logging.DEBUG)

class HousingCrawler(object):
    def __init__(self, 
                 n_beds=None, 
                 price_min=None, 
                 price_max=None, 
                 area_min=None, 
                 posted_today=True, 
                 filters=None,
                 destination=None,
                 mode=None,
                 limit=None
                ):
        """filters take precedence"""
        self.n_beds = n_beds if n_beds is not None else filters['min_bedrooms']
        self.price_min = price_min if price_min is not None else filters['price_min']
        self.price_max = price_max if price_max is not None else filters['price_max']
        self.area_min = area_min if area_min is not None else filters['min_ft2']
        self.posted_today = posted_today
        self.filters = filters
        self.destination = destination
        self.mode = mode 
        self.limit = limit
        
        # others attributes 
        self.res = None # results of crawling 
        self.df_res = None # results in dataframe 
        
        if filters is None:
            assert not None in [self.n_beds, self.price_min, self.price_min, self.area_min], 'Please make sure either all args are filled or filters are provided'
        
    @staticmethod
    @cachier(stale_after=datetime.timedelta(days=30), cache_dir=CACHE_DIR)
    def _pull_data_fromcraig(filters, day=datetime.date.today(), limit=None):
        # create craig class
        cl_h = CraigslistHousing(
            site='sfbay', 
            area='sfc',
            filters=filters
            )
        res_gen = cl_h.get_results(limit=limit, include_details=True, geotagged=True)
        res = list(res_gen)
        return res
        
    def pull_data(self):
        # filters
        filters={'min_price': self.price_min,
          'max_price': self.price_max,
          'min_bedrooms': self.n_beds,
          'max_bedrooms': self.n_beds,
          'min_ft2': self.area_min,
          'posted_today': self.posted_today
         }

        res = self._pull_data_fromcraig(filters, limit=self.limit)
        logging.info({'msg': 'Number of listings for {n_beds} bedrooms is: {n_obs}'.format(
            n_beds=self.n_beds,
            n_obs=len(res)
        )})
        # add to self
        self.res = res
        return res
    
    def format_data(self):
        assert self.res is not None
        df_res = pd.DataFrame.from_dict(self.res)
        
        # exclude listing with small description 
        df_res = exclude_smalldesc(df_res, thresh=100)
        
        # list of columns that we care about 
        l_COLUMNS = ['id', 'url', 'datetime', 'created', 'last_updated', 'geotag', 'price', 'area', 'bedrooms', 'bathrooms']
        
        # only keep column we care about 
        df_res = df_res[l_COLUMNS]
        
        # clean area column 
        df_res = clean_area(df_res)

        # clean price column
        df_res = clean_price(df_res)

        # remove rows with None 
        df_res = remove_None(df_res)

        # calculate the price per sqft 
        df_res['ppsqft'] = df_res.price / df_res.area

        # get lat, lng 
        df_res['lat'] = df_res.geotag.apply(get_lat)
        df_res['lng'] = df_res.geotag.apply(get_lng)

        # we add a column of rounded latlng for caching purpose 
        df_res['geotag_rounded'] = df_res.geotag.apply(
            lambda x : (round(x[0], 4), round(x[1], 4))
            )

        # sort by ppsqft
        df_res.sort_values(['ppsqft'], inplace = True)
        
        self.df_res = df_res     
        
    def enrich_traveldata(self, destination=None, mode=None):
        """
        Adds columns about the distance and duration to destination based on mode of transport.

        :params destination: tuple with (lat, lng) of destination or dict with keys refering to names of destinations 
        and values being tuples
        :params mode: can take one or a subset of ["walking", "transit", "bicycling", "driving"]
        """
        destination = self.destination if destination is None else destination
        mode = self.mode if mode is None else mode

        assert self.df_res is not None 
        assert self.df_res.shape[0] != 0, "df_res has no data"
        assert type(destination) in [tuple, dict], "destination is either a tuple or a dict, {} given".format(type(destination))
        assert set([type(i) for i in destination.values()]) == set([tuple]) if type(destination) == dict else True, "all keys to destination must be tuples"
        assert type(mode) in [list, str], "mode is either a list or a str"
        
        if type(destination) == tuple:
            d_destinations = {"default": destination}
        else:
            d_destinations = destination
        if type(mode) == str:
            l_modes = [mode]
        else:
            l_modes = mode

        for dest_name, dest_lat_lng in d_destinations.items():
            for mode_ in l_modes:
                # column for distance_duration columns (temporaty column)
                dist_dur_colname = "_".join(["dist_dur", str(dest_name), str(mode_)])
                
                logging.info(
                    {
                    'msg': 'pulling travel data for traveling to {dest_name} using {mode_}'.format(
                        dest_name=dest_name,
                        mode_=mode_
                        )
                    }
                )
                self.df_res[dist_dur_colname] = self.df_res.geotag_rounded.apply(
                    lambda x: get_travel_info(x, destination=dest_lat_lng, mode=mode_)
                )
                
                # distance column
                dist_colname = "_".join(["distance", str(dest_name), str(mode_)])
                self.df_res[dist_colname] = self.df_res[dist_dur_colname].apply(lambda x: x[0])
                
                # duration column
                dur_colname = "_".join(["duration", str(dest_name), str(mode_)])
                self.df_res[dur_colname] = self.df_res[dist_dur_colname].apply(lambda x: x[1])
                
                # drop dist_dur column 
                self.df_res.drop([dist_dur_colname], axis=1, inplace=True)
                
    def score(self):
        assert self.df_res is not None, 'You must first run pull_data and enrich_traveldata to get scores'
        # ppsqft score 
        self.df_res["ppsqft_score"] = (1 - (self.df_res.ppsqft - MIN_PPSQFT) / (MAX_PPSQFT - MIN_PPSQFT)).apply(lambda x: max(x, 0))
        
        # Uber Travel Score is the best score between walking and transit 
        self.df_res["walking_Uber_score"] = (1 - (self.df_res.duration_Uber_walking - MIN_WALKING) / (MAX_WALKING - MIN_WALKING )).apply(lambda x: max(x, 0))
        self.df_res["transit_Uber_score"] = (1 - (self.df_res.duration_Uber_transit - MIN_TRANSIT) / (MAX_TRANSIT - MIN_TRANSIT)).apply(lambda x: max(x, 0))
        self.df_res["travel_Uber_score"] = self.df_res[["walking_Uber_score", "transit_Uber_score"]].max(axis =1)
        
        # Dropbox travel score is the bestscore between walking and cycling 
        self.df_res["walking_Dropbox_score"] = (1 - (self.df_res.duration_Dropbox_walking - MIN_WALKING) / (MAX_WALKING - MIN_WALKING)).apply(lambda x: max(x, 0))
        self.df_res["cycling_Dropbox_score"] = (1 - (self.df_res.duration_Dropbox_cycling - MIN_CYCLING) / (MAX_CYCLING - MIN_CYCLING)).apply(lambda x: max(x, 0))
        self.df_res["travel_Dropbox_score"] = self.df_res[["walking_Dropbox_score", "cycling_Dropbox_score"]].max(axis =1)
        
        # total score is the geometric mean of ppsqft score, travel Uber score and travel Dropbox score 
        self.df_res['score'] = self.df_res[['ppsqft_score', 'travel_Uber_score', 'travel_Dropbox_score']].apply(geometric_mean, axis = 1)
        self.df_res.sort_values(['score'], ascending = False, inplace = True)
        
        # considered listings 
        self.url_considered = self.df_res[self.df_res.score != 0].url.to_list()
        
        # top 10 listings 
        self.url_top = self.df_res.url.head(5).to_list()
                    
    def run_all(self):
        # pull data 
        _ = self.pull_data()
        # format data 
        self.format_data()
        # enrich travel data 
        self.enrich_traveldata()
        # get score 
        self.score()