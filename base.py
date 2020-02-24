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
                 site=None,
                 area=None,
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
        if filters is None:
            assert not None in [site, n_beds, price_min, price_max, area_min], 'Please make sure either all args are filled or filters are provided'

        self.site = site if site is not None else filters['site']
        self.area = area if area is not None else filters['area']
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
        
        
    def pull_data(self):
        # filters
        filters={'min_price': self.price_min,
          'max_price': self.price_max,
          'min_bedrooms': self.n_beds,
          'max_bedrooms': self.n_beds,
          'min_ft2': self.area_min,
          'posted_today': self.posted_today
         }

        res = self._pull_data_fromcraig(
            filters=filters, 
            site=self.site, 
            area=self.area, 
            limit=self.limit)

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
        df_res = exclude_smalldesc(df_res, thresh=10)
        
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

        :params destination: dict with keys (lat, lng) of destination or dict with keys refering to names of destinations
        and values dicts with (lat, lng) as keys
        :params mode: can take one or a subset of ["walking", "transit", "bicycling", "driving"]
        """
        destination = self.destination if destination is None else destination
        mode = self.mode if mode is None else mode

        assert self.df_res is not None 
        assert self.df_res.shape[0] != 0, "df_res has no data"
        assert isinstance(destination, dict), "destination is either must be dict, {} given".format(type(destination))
        assert type(mode) in [list, str], "mode is either a list or a str"
        
        if type(destination) == tuple:
            d_destinations = {"default": destination}
        else:
            d_destinations = destination
        if type(mode) == str:
            l_modes = [mode]
        else:
            l_modes = mode

        self.d_destinations = d_destinations
        self.l_modes = l_modes

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
                

    def get_travel_score(self):
        """Gets aggregate scores for each destination and travel score for each destination and modes."""
        assert isinstance(self.d_destinations, dict), "You must run enrich_traveldata to get travel data"
        assert isinstance(self.l_modes, list), "You must run enrich_traveldata to get travel data"

        for dest_name in self.d_destinations.keys():
            for mode_ in self.l_modes:
                # get the score of going to dest_name using mode_
                col_name = '_'.join(["duration", dest_name, mode_])
                score_name = '_'.join([mode_, dest_name, "score"])
                self.df_res[score_name] = self.df_res[col_name].apply(
                    lambda x: self.get_column_score(val=x, val_name=mode_)
                    )

            # the travel score is the max of all mode scores
            travel_score_name = '_'.join(["travel", dest_name, "score"])
            # list of all
            l_mode_scores = ['_'.join([mode_, dest_name, "score"]) for mode_ in self.l_modes]
            # the travel score is the max of all mode scores
            self.df_res[travel_score_name] = self.df_res[l_mode_scores].max(axis=1)

    def get_ppsqft_score(self):
        """Gets the score of the ppsqft column."""
        col_name = "ppsqft"
        score_name = "ppsqft_score"
        self.df_res[score_name] = self.df_res[col_name].apply(
            lambda x: self.get_column_score(val=x, val_name="ppsqft")
            )

    def get_aggregate_score(self):
        """Aggregate scores is the geometric means of adhoc and travel scores."""
        l_adhoc_scores = ["ppsqft_score"]
        l_travel_scores = ['_'.join(["travel", dest_name, "score"]) for dest_name in self.d_destinations.keys()]
        l_all_scores =  l_adhoc_scores + l_travel_scores
        self.df_res['score'] = self.df_res[l_all_scores].apply(geometric_mean, axis = 1)

    def score(self):
        assert self.df_res is not None, 'You must first run pull_data and enrich_traveldata to get scores'
        # adhoc scores
        # ppsqft
        self.get_ppsqft_score()

        # travel scores
        self.get_travel_score()
        
        # total score is the geometric mean of ppsqft score, travel Uber score and travel Dropbox score 
        self.get_aggregate_score()

        # sort values by score
        self.df_res.sort_values(['score'], ascending = False, inplace = True)
        
        # only consider scores with values higher than 0
        self.url_considered = self.df_res[self.df_res.score != 0].url.to_list()
        
        # top 5 listings
        self.url_top = self.df_res.url.head(5).to_list()

    @staticmethod
    @cachier(stale_after=datetime.timedelta(days=30), cache_dir=CACHE_DIR)
    def _pull_data_fromcraig(filters, site, area, day=datetime.date.today(), limit=None):
        # TODO: add assertion if site and area exist

        # create craig class
        cl_h = CraigslistHousing(
            site=site,
            area=area,
            filters=filters
            )
        res_gen = cl_h.get_results(limit=limit, include_details=True, geotagged=True)
        res = list(res_gen)
        return res

    @staticmethod
    def normalize_val(val, min_bound, max_bound):
        """
        Get normalized value [0, 1]. (1: is good and 0 is bad)
        :params val: the value you want to normalize
        :params min_bound: the minimum value (if val <= min_val then score = 1)
        :parmas max_bound: the maximum value (if val >= max_val then score = 0)

        :output norm_val: value between [0, 1]
        """
        # get raw normaliZed value
        raw_norm_score = 1 - (val - min_bound) / (max_bound - min_bound)
        # set bounds between 0 and 1
        normalized_score = max(0, min(1, raw_norm_score))
        return normalized_score

    def get_column_score(self, val, val_name):
        min_val = SCORE_BOUNDS.get(val_name).get('min')
        max_val = SCORE_BOUNDS.get(val_name).get('max')
        norm_val = self.normalize_val(val, min_bound=min_val, max_bound=max_val)
        return norm_val

    def run_all(self):
        # pull data 
        _ = self.pull_data()
        # format data 
        self.format_data()
        # enrich travel data 
        self.enrich_traveldata()
        # get score 
        self.score()