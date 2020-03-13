# MicronTimeSeries.py
# 
# Represents a Micron Sonar time series of ensemble measurements.
#   2020-03-13  zduguid@mit.edu         initial implementation 
 

import numpy as np
import pandas as pd 
from datetime import datetime


class MicronTimeSeries(object):
    def __init__(self):
        """Constructor of a Micron Sonar time series of ensembles.

        Please note that various Micron Sonar setting may vary from 
        ensemble to ensemble. For example, the range setting or 
        resolution setting may be updated adaptively during the 
        mission. 

        The time series data is stored in a pandas DataFrame object 
        for easy manipulation and access. That said, to avoid
        appending to a DataFrame (which is slow) the incoming 
        ensembles are collected in a python list and once the 
        to_datraframe function is called the pandas DataFrame is 
        created.
        """
        # initialize the data_arrays
        self._ensemble_list = []
        self._df = None

    @property
    def header_vars(self):
        return self._header_vars
    
    @property
    def derived_vars(self):
        return self._derived_vars
    
    @property
    def intensity_vars(self):
        return self._intensity_vars

    @property
    def label_list(self):
        return self._label_list

    @property
    def label_set(self):
        return self._label_set
    
    @property
    def data_lookup(self):
        return self._data_lookup

    @property
    def intensity_index(self):
        return self._intensity_index

    @property
    def ensemble_list(self):
        return self._ensemble_list
    
    @property
    def df(self):
        return self._df


    def to_dataframe(self):
        """Converts the current list of ensembles into a DataFrame.
        """
        ts      = np.array(self.ensemble_list)
        cols    = self.label_list
        t_index = self.data_lookup['date_time']
        t       = ts[:,t_index]
        index   = pd.DatetimeIndex([datetime.fromtimestamp(val) for val in t])

        # save to data-frame 
        self._df  = pd.DataFrame(data=ts, index=index, columns=cols)


    def add_ensemble(self, ensemble):
        """Adds a Micron Sonar ensemble to the growing list of ensembles.

        Args: 
            ensemble: a Micron Sonar ensemble  
        """
        # set attributes of the time series that are assumed constant
        #   - all the values associated with these labels will change
        #     from ensemble to ensemble but the labels themselves will
        #     not change 
        if not self.ensemble_list:
            self._header_vars       = ensemble.header_vars
            self._derived_vars      = ensemble.derived_vars
            self._intensity_vars    = ensemble.intensity_vars
            self._label_list        = ensemble.label_list
            self._label_set         = ensemble.label_set
            self._data_lookup       = ensemble.data_lookup
            self._intensity_index   = ensemble.intensity_index
        self._ensemble_list.append(ensemble.data_array)


