# MicronTimeSeries.py
# 
# Represents a Micron Sonar time series of ensemble measurements.
#   2020-03-13  zduguid@mit.edu         initial implementation 
 

import csv
import numpy as np
import math
import pandas as pd 
from datetime import datetime
from MicronSonar import MicronSonar


class MicronTimeSeries(MicronSonar):
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
        # use the parent constructor for defining Micron Sonar variables
        super().__init__()

        # initialize the DataFrame and ensemble list parameters 
        self._name          = name
        self._df            = None
        self._ensemble_list = []


    @property
    def name(self):
        return self._name

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
                self.df.to_csv(directory+self.name+'.CSV')
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
        self.df.loc[((self.df.bearing >= bearing_min + pad) & 
                     (self.df.bearing  < bearing_max - pad)), var] = val


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


    def crop_on_bearing(self, left_bearing=-180, right_bearing=180,
        single_swath=False):
        """Crops DataFrame based on bearing value of sonar ensembles.  

        Allows the option of down-selecting a single swath from the data file.

        Args:
            left_bearing: the left-most bearing to be included in the cropped 
                DataFrame. Default value includes full bearing window.
            
            right_bearing: the right-most bearing to be included in the cropped
                DataFrame. Default value includes full bearing window.
            
            single_swath: Boolean flag that determines if a single swath is 
                selected from the DataFrame. 
        """
        if single_swath: 
            name = self.name + '_swath'
        else:            
            name = self.name + '_cropped'
        ts = MicronTimeSeries(name)

        # crop bearing differently depending on relative value of bearings 
        if right_bearing > left_bearing:
            ts._df = self.df[(self.df.bearing_ref_world >= left_bearing) & 
                             (self.df.bearing_ref_world <= right_bearing)]
        else: 
            ts._df = self.df[(self.df.bearing_ref_world >= left_bearing) | 
                             (self.df.bearing_ref_world <= right_bearing)]

        # down-select one complete swath within the bearing window provided
        if single_swath:
            steps  = self.df.steps[0]
            steps += -0.1
            swath  = math.ceil(abs(right_bearing-left_bearing)/steps)*2
            ts._df = ts.df[:swath]

        return(ts)

