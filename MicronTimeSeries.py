# MicronTimeSeries.py
# 
# Represents a Micron Sonar time series of ensemble measurements.
#   2020-03-13  zduguid@mit.edu         initial implementation 

import csv
import numpy as np
import math
import pandas as pd 
from datetime import datetime
from os import listdir
from os.path import isfile, join
from MicronSonar import MicronSonar
from MicronEnsemble import MicronEnsemble


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


    @classmethod
    def from_csv(cls, filepath):
        """Constructor of a Micron Time Series from a processed CSV file

        Note that this function parses CSV files that have been saved with 
        MicronTimeSeries.save_as_csv(), not CSV files that are logged 
        by the Micron Sonar directly. For the latter case, use the static method from_raw_csv() instead.
        
        Args: 
            filepath: the filepath to the csv file to be opened and parsed.

        Returns:
            Micron Sonar Time Series object.
        """
        # parse the DataFrame from the provided CSV file
        name   = filepath.split('/')[-1].split('.')[0]
        new_df = pd.read_csv(filepath, header=0, index_col=0, parse_dates=True)
        ts     = cls(name)
        print('>> Parsing: %s' % (name))

        # raise error if the given CSV columns do not match 
        if ts.label_list != tuple(new_df.columns):
            raise ValueError("bad csv file for: from_csv(%s)" % (name))

        ts._df = new_df
        return ts


    @classmethod
    def from_csv_directory(cls, filepath, name=None):
        """Constructor of a Micron Time Series from a directly of CSV files
        """
        print("Parsing folder of CSV files")
        # acquire a list of all files in the provided directory 
        file_list   = [f for f in listdir(filepath) if 
                       isfile(join(filepath, f)) and f.split('.')[-1] == 'csv']
        frames      = [cls.from_csv(filepath+f).df for f in file_list]
        ts          =  cls.from_frames(frames, name)
        print('>> Finished Parsing!')
        return ts


    @classmethod
    def from_frames(cls, frames, name=None):
        """Constructor of a Micron Time Series from a list of DataFrame objects
        """
        if name: ts = cls(name)
        else:    ts = cls()

        # check to make sure all provided DataFrames have the same columns 
        for df in frames:
            if ts.label_list != tuple(df.columns):
                raise ValueError("bad csv file for: from_frames(%s)" % (df))

        # combine the DataFrames together 
        ts._df = pd.concat(frames)
        return ts


    @classmethod
    def from_raw_csv(cls, filepath, date, bearing_bias=0, 
        constant_depth=None, constant_altitude=None):
        """Constructor of a Micron Time Series from a raw Micron CSV file 

        This function assumes that the saved csv file was generated from the
        Micron Sonar directly (or converted to CSV format from Tritech's
        Seanet DumpLog software), not an already parsed Time Series object.
        For the latter, use the TimeSeries.from_csv() class method.

        Args: 
            filepath: the file path to the Micron Sonar csv file to read.
            date: tuple of integers (year,month,day) (ex: 2020,01,24)
            bearing_bias: bias in the sonar head (positive means rolling right)
            constant_depth: Depth in [m] that the sonar is operating
            constant_altitude: Altitude in [m] that the sonar is operating

        Returns:
            Micron Sonar Time Series object.
        """
        count   = 0
        notify  = 100
        file    = filepath.split('/')[-1].split('.')[0]
        print('Parsing: %s' % (file))

        # open the csv file 
        csv_file = open(filepath)
        header   = csv_file.readline().split(',') 

        # initialize a time series object 
        ts = cls(file)

        # add all ensembles to the time series 
        for line in csv_file:  
            count   += 1
            csv_row  = csv_file.readline().split(',')

            # ignore the empty row at the end of the file 
            if (len(csv_row) == 1):
                break

            # parse the Micron Sonar ensemble
            ensemble = MicronEnsemble(
                csv_row, date, bearing_bias, sonar_depth=constant_depth,
                sonar_altitude=constant_altitude
            )
            
            # add the parsed ensemble to the time series 
            ts.add_ensemble(ensemble)
            if (count % notify == 0):
                print("  >> Ensembles Parsed: %5d" % (count))

        # convert the list of ensembles into a DataFrame and then return
        ts.to_dataframe()
        print('  >> Finished Parsing!')
        return ts


    def add_ensemble(self, ensemble):
        """Adds a Micron Sonar ensemble to the growing list of ensembles.

        Args: 
            ensemble: a Micron Sonar ensemble  
        """
        self._ensemble_list.append(ensemble.data_array)


    def to_dataframe(self):
        """Converts the current list of ensembles into a DataFrame.

        Note: calling this function will invoke pd.concat(), which creates a 
        copy of the whole DataFrame in memory. As a result, if this function 
        is called many times, there will be significant slowdown. Instead,
        consider collecting ensembles into the ensemble_list until a suitable 
        number of ensembles have been collected, and then intermittently call 
        the to_dataframe function.
        """
        # convert available ensembles to DataFrame
        if self.ensemble_list:
            ts      = np.array(self.ensemble_list)
            cols    = self.label_list
            t_index = self.data_lookup['date_time']
            t       = ts[:,t_index]
            index   = pd.DatetimeIndex([datetime.fromtimestamp(v) for v in t])
            new_df  = pd.DataFrame(data=ts, index=index, columns=cols)

            # concatenate new ensembles with existing DataFrame if possible
            if self.df is None:
                self._df = new_df
            else:
                self._df = pd.concat([self.df, new_df])

            # reset the ensemble list once added to the DataFrame
            self._ensemble_list = []
        else:
            print("WARNING: No ensembles to add to DataFrame.")


    def save_as_csv(self, name=None, directory='./'):
        """Saves the DataFrame to csv file. 

        Args:
            name: name used when saving the file.
            directory: string directory to save the DataFrame to.
        """
        # update name if not given
        if name is None:
            name = self.name 

        # add ensembles to the DataFrame if they haven't been added yet
        if self.ensemble_list:
            self.to_dataframe()

        # save DataFrame to csv file
        if self.df is not None:
            self.df.to_csv(directory+name+'.CSV')
        else:
            print("WARNING: No data to save.")


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


    def crop_on_bearing(self, left_angle=-180, right_angle=180,
        single_swath=False):
        """Crops DataFrame based on bearing value of sonar ensembles.  

        Allows the option of down-selecting a single swath from the data file.

        Args:
            left_angle: the left-most bearing to be included in the cropped 
                DataFrame. Default value includes full bearing window.
            
            right_angle: the right-most bearing to be included in the cropped
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
        if right_angle > left_angle:
            ts._df = self.df[(self.df.bearing_ref_world >= left_angle) & 
                             (self.df.bearing_ref_world <= right_angle)].copy()
        else: 
            ts._df = self.df[(self.df.bearing_ref_world >= left_angle) | 
                             (self.df.bearing_ref_world <= right_angle)].copy()

        # down-select one complete swath within the bearing window provided
        if single_swath:
            steps  = self.df.steps[0]
            steps += -0.1
            swath  = math.ceil(abs(right_angle-left_angle)/steps)*2
            ts._df = ts.df[:swath]

        return ts

