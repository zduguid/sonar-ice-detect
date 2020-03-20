# MicronTimeSeries.py
# 
# Represents a Micron Sonar time series of ensemble measurements.
#   2020-03-13  zduguid@mit.edu         initial implementation 
 

import csv
import numpy as np
import pandas as pd 
from datetime import datetime


class MicronTimeSeries(object):
    def __init__(self, name=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
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

        Args: 
            name: The name of the time-series. For example, name could be the 
                filename of the parsed Micron Sonar file. The name attribute 
                is used when saving a parsed time-series to CSV format. 
        """
        # initialize the data_arrays
        self._name              = 'MicronTimeSeries_' + name
        self._df                = None
        self._ensemble_list     = []
        self._header_vars       = []
        self._derived_vars      = []
        self._ice_vars          = []
        self._intensity_vars    = []
        self._label_list        = []
        self._label_set         = set([])
        self._data_lookup       = {}
        self._ensemble_size     = 0
        self._intensity_index   = 0

    @property
    def name(self):
        return self._name
    
    @property
    def header_vars(self):
        return self._header_vars
    
    @property
    def derived_vars(self):
        return self._derived_vars

    @property
    def ice_vars(self):
        return self._ice_vars
    
    @property
    def intensity_vars(self):
        return self._intensity_vars

    @property
    def ensemble_size(self):
        return self._ensemble_size
    
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
            self._ice_vars          = ensemble.ice_vars
            self._intensity_vars    = ensemble.intensity_vars
            self._label_list        = ensemble.label_list
            self._label_set         = ensemble.label_set
            self._data_lookup       = ensemble.data_lookup
            self._intensity_index   = ensemble.intensity_index
            self._ensemble_size     = len(self.label_list)
        self._ensemble_list.append(ensemble.data_array)


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


    def save_as_csv(self, directory='./'):
            """Saves the DataFrame to csv file. 

            Args:
                directory: string directory to save the DataFrame to
            """
            # convert to DataFrame if ensembles have been collected
            if self.ensemble_list and self.df is None:
                self.to_dataframe()
            # save DataFrame to csv file
            if self.df is not None:
                self.df.to_csv(directory+self.name)
            else:
                print("WARNING: No data to save")


    def from_csv(self, filepath):
        """Parse Micron Time Series from a parsed CSV file.

        Note that this function parses CSV files that have been saved with 
        "MicronTimeSeries.save_as_csv()", not CSV files that are logged 
        by the Micron Sonar directly. CSV files that are logged by the Micron 
        Sonar must first be parsed into a time series object using the 
        "micron_reader" file.
        
        Args: 
            filepath: the filepath to the csv file to be opened and parsed.
        """
        if self.df is None:
            # parse the DataFrame from the csv file 
            self._df = pd.read_csv(filepath, header=0, index_col=0, 
                                   parse_dates=True)

            # find indices that indicate change in variable type
            var_list = list(self.df.columns)
            head_idx = var_list.index('dbytes')+1
            ice_idx  = [i for i, s in enumerate(var_list) if s[:5]=='class'][0]
            bin_idx  = [i for i, s in enumerate(var_list) if s[:5]=='bin_0'][0]

            # parse variable lists from indices
            self._header_vars    = var_list[         : head_idx]
            self._derived_vars   = var_list[head_idx :  ice_idx]
            self._ice_vars       = var_list[ice_idx  :  bin_idx]
            self._intensity_vars = var_list[bin_idx  :         ]    

            self._label_list = self.header_vars  + \
                               self.derived_vars + \
                               self.ice_vars     + \
                               self.intensity_vars
            self._label_set       = set(self.label_list)
            self._ensemble_size   = len(self.label_list)
            self._intensity_index = bin_idx
            self._data_lookup     = {
                self.label_list[i]:i for i in range(self.ensemble_size)
            }
        else:
            print("WARNING: parsing from csv will erase existing data")


    def set_label_by_bearing(self, var, val, bearing_min, bearing_max, pad=0):
        """Set the ice label for a specific range of bearings

        The pad parameter is used for when it is difficult to label the exact
        transition angle between two different ice-types. By including a non-
        zero pad value, it is easier to avoid mislabeling ice types.

        Args:
            var: the ice label to update.
            val: the value for the ice label to be set to.
            bearing_min: the minimum bearing to be included in variable update.
            bearing_max: the maximum bearing to be included in variable update.
            pad: the amount that the bearing window is shrunk on either side.
        """
        if (var not in self.label_set):
            raise ValueError("bad var for: label(%s, %s)" % (var, str(val)))
        self.df.loc[(self.df.bearing >= bearing_min + pad) & 
                    (self.df.bearing  < bearing_max - pad), var] = val


    def reset_labels(self):
        """Reset the labeled ice parameters to np.nan"""
        # consider the entire bearing range 
        bearing_min = -180
        bearing_max =  180
        val         =  np.nan

        # extract label variables 
        labels = [var for var in self.ice_vars if var[:5]=="label"]
        for label in labels:
            self.set_label_by_bearing(label, val, bearing_min, bearing_max)


