# MicronEnsemble.py
#
# Represents a Micron Sonar ensemble.
#   2020-03-15  zduguid@mit.edu         initial implementation 

import datetime
import dateutil
import math
import numpy as np
import pandas as pd 

class MicronEnsemble(object):
    def __init__(self, csv_row, date):
        """Constructor of a Micron Sonar ensemble.

        The Micron Sonar User Manual and Seanet DumpLog Software Manual were 
        used to write this code. The min_range parameter was taken from the 
        specification for the sonar. The roll_median_len and conv_kernel_len 
        parameters were tuned to achieve the desired performance.

        Args: 
            csv_row: A list of strings that represent one ensemble from the
                Micron Sonar. The first 15 values of the list are header 
                variables, and then the remaining variables are acoustic
                intensity  values.
            date: A tuple of integers representing (year,month,day). The date 
                argument should match the date of which the data is recorded.
        """
        # unit conversion multipliers 
        self.deg_to_rad  = np.pi/180    # [deg] -> [rad]
        self.rad_to_deg  = 180/np.pi    # [rad] -> [deg]
        self.grad_to_deg = 360/6400     # [1/16 Gradians] -> [deg]
        self.dm_to_m     = 1/10         # [dm] -> [m]
        self.bin_to_db   = 80/255       # [0,255] -> [0,80dB]

        # other constants 
        self.roll_median_len = 5        # used for taking rolling median
        self.conv_kernel_len = 5        # used when taking convolution 
        self.min_range       = 0.3      # min-range of Micron Sonar in [m]

        # header variables automatically saved by the Micron Sonar
        self._header_vars = [
            'line_header',          # line header (not important)
            'date_time',            # date and time the line was recorded
            'node',                 # node is 2 for imaging sonar
            'status',               # 2 byte bitset (see readme for more info)
            'hdctrl',               # 2 byte bitset (see readme for more info
            'range_scale',          # range value that the sonar was operating
            'gain',                 # gain setting used for the sonar 
            'slope',                # receiver slope, Time Variable Gain (TVG)
            'ad_low',               # used for formatting color of plots
            'ad_span',              # used for formatting color of plots
            'left_lim',             # left limit of swatch (left of zero) 
            'right_lim',            # right limit of swatch (right of zero)
            'steps',                # angular step size
            'bearing',              # bearing of the transducer head 
            'dbytes'                # the number of retrieved intensity values
            ]

        # variables that are derived from the intensity and header values
        self._derived_vars = [
            'year',                 # year that the data was recorded
            'month',                # month that the data was recorded
            'day',                  # day that the data was recorded
            'bin_size',             # size of each bin, in [m]
            'max_intensity_bin',    # bin location of the maximum value 
            'max_intensity',        # maximum intensity measured, in [dB]
            'peak_start_bin',       # bin location of the start of the peak
            'peak_start',           # distance from transducer to start of peak
            'peak_end_bin',         # bin location of the end of the peak
            'peak_end',             # distance from transducer to end of peak
            'peak_width_bin',       # bin width of the peak
            'peak_width'            # width of peak in terms of distance
            ]


        # bookkeep number of header, derived, and intensity variables 
        self.header_len      = len(self.header_vars)
        self.derived_len     = len(self.derived_vars)
        self.intensity_len   = int(csv_row[self.header_vars.index('dbytes')])
        self.bin_index       = self.header_len  + self.derived_len
        self.ensemble_size   = self.header_len  + \
                               self.derived_len + \
                               self.intensity_len
        self._intensity_vars = ["bin_" + str(i) for i in 
                                range(self.intensity_len)]
        self._data_array     = np.zeros(self.ensemble_size)
        self._label_list     = self.header_vars + \
                               self.derived_vars + \
                               self.intensity_vars
        self._label_set      = set(self.label_list)
        self.data_lookup     = {self.label_list[i]:i \
                                for i in range(len(self.label_list))}

        # parse header and acoustic intensities, compute derived variables 
        self.parse_header(csv_row, date)
        self.parse_intensity_bins(csv_row)
        self.parse_derived_vars()
    

    @property
    def data_array(self):
        return self._data_array

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
    def intensity_data(self):
        return self.data_array[self.bin_index:]


    def get_data(self, variable):
        """Getter method for a particular variable in the data array."""
        return(self.data_array[self.data_lookup[variable]])


    def set_data(self, var, val, attribute=True):
        """Setter method for a variable-value pair to be put in the array.

        Raises:
            ValueError if invalid variable is given in var
            ValueError if incorrect type is given by val
        """
        if (var not in self.label_set):
            raise ValueError("bad variable set set<%s, %s>" % (var, str(val)))
        self._data_array[self.data_lookup[var]] = val 
        if attribute: setattr(self, var, val)


    def convert_to_metric(self, variable, multiplier, attribute=True):
        """Converts variable to standard metric value using the multiplier"""
        value = self.get_data(variable)
        self.set_data(variable, value * multiplier, attribute)


    def convert_intensity_to_metric(self, multiplier):
        """Converts the array to standard metric values using the multiplier"""
        self._data_array[self.bin_index:] *= multiplier


    def filter_min_range_intensities(self):
        """Filters out the intensity values in the min range of the sonar."""
        min_range_index = math.ceil(self.min_range/self.bin_size)
        self._data_array[self.bin_index : self.bin_index + min_range_index] = 0


    def parse_header(self, csv_row, date):
        """Parses the header variables of the Micron Sonar ensemble. 

        Args: 
            csv_row: a list of strings representing an ensemble of data.
            date: a tuple of (year,month,day) values
        """
        # add header values to the data array 
        for i in range(len(self.header_vars)):

            # handle line header parameter (does not contain numerical type)
            if (i == self.header_vars.index('line_header')): 
                self.set_data('line_header', 1)
            
            # add year,month,day to DateTime object  
            elif (i == self.header_vars.index('date_time')): 
                (year, month, day) = date
                date_time = date_time = dateutil.parser.parse(csv_row[i])
                date_time = date_time.replace(year=year, month=month, day=day,
                                              microsecond=0)
                self.set_data('date_time', date_time.timestamp())
                self.set_data('year', year)
                self.set_data('month', month)
                self.set_data('day', day)

            # parse all other header variables (all others are numerical) 
            else:
                variable = self.header_vars[i]
                value = int(csv_row[i])
                self.set_data(variable, value)

        # convert header values to standard metric values 
        self.convert_to_metric('range_scale', self.dm_to_m)
        self.convert_to_metric('left_lim',    self.grad_to_deg)
        self.convert_to_metric('right_lim',   self.grad_to_deg)
        self.convert_to_metric('steps',       self.grad_to_deg)
        self.convert_to_metric('bearing',     self.grad_to_deg)
        self.convert_to_metric('ad_low',      self.bin_to_db)
        self.convert_to_metric('ad_span',     self.bin_to_db)

        # update coordinate system of Micron Sonar bearing 
        bearing   = self.reorient_bearing(self.get_data('bearing'))
        left_lim  = self.reorient_bearing(self.get_data('left_lim'))
        right_lim = self.reorient_bearing(self.get_data('right_lim'))
        self.set_data('bearing',   bearing)
        self.set_data('left_lim',  left_lim)
        self.set_data('right_lim', right_lim)


    def reorient_bearing(self, bearing_deg):
        """Reorient bearing from Micron Sonar default to custom orientation.   

        Micron Sonar Orientation: 
          0   degrees = upwards 
          90  degrees = port 
          180 degrees = downwards 
          270 degrees = starboard
        
        Custom Orientation:
          0   degrees = starboard
          90  degrees = upwards 
          180 degrees = port 
          270 degrees = downwards  
          
        Args:
            bearing_deg = the bearing in degrees recorded by the Micron Sonar.
        
        Returns:
            Bearing that has been rotated and flipped into a new orientation.
        """
        deg_in_circle   = 360
        deg_in_quadrant = 90
        bearing_deg  = bearing_deg % deg_in_circle
        bearing_deg += deg_in_quadrant
        return(bearing_deg % deg_in_circle)


    def parse_intensity_bins(self, csv_row):
        """Parses acoustic intensity values and adds them to the data array."""
        # add intensity values to the data array 
        for i in range(self.intensity_len):
            bin_val   = float(csv_row[i+self.header_len])
            bin_label = 'bin_' + str(i)
            self.set_data(bin_label, bin_val, attribute=False)
        
        # convert intensity bins from [0,255] -> [0,80dB]
        self.convert_intensity_to_metric(self.bin_to_db)


    def parse_derived_vars(self):
        """Computes the derived quantities for the ensemble."""
        # compute bin size, max intensity, and max intensity bin
        self.set_data('bin_size',          self.range_scale / self.dbytes)
        self.set_data('max_intensity',     np.max(self.intensity_data))
        self.set_data('max_intensity_bin', np.argmax(self.intensity_data))
        self.filter_min_range_intensities()

        # determine the peak of the signal according to the FWHM method
        peak_start_bin, peak_end_bin = self.get_peak_width()
        peak_width_bin = peak_end_bin - peak_start_bin
        self.set_data('peak_start_bin',  peak_start_bin)
        self.set_data('peak_end_bin',    peak_end_bin)
        self.set_data('peak_width_bin',  peak_width_bin)
        self.set_data('peak_start',      peak_start_bin * self.bin_size)
        self.set_data('peak_end',        peak_end_bin   * self.bin_size)
        self.set_data('peak_width',      peak_width_bin * self.bin_size)


    def get_peak_width(self):
        """Computes the width of the dominant peak of the ensemble. 

        Uses the Full Width Half Maximum (FWHM) method for extracting the width
        of the main signal peak. To account for narrow peaks in ensemble 
        intensity values, a rolling median filter and convolution filter 
        methods are applied. 
        """
        # get width of values that satisfy the threshold 
        bin_data = pd.DataFrame(self.intensity_data)
        bin_roll = bin_data.rolling(self.roll_median_len, center=True).median()
        bin_roll = bin_roll.replace(np.nan, 0).to_numpy().flatten()
        kernel   = np.ones(self.conv_kernel_len, dtype=int)
        
        # threshold the array based on half of the maximum intensity 
        bin_threshold = np.array(bin_roll)
        bin_threshold[bin_threshold <  np.max(bin_roll) / 2] = 0
        bin_threshold[bin_threshold >= np.max(bin_roll) / 2] = 1
        
        # convolve the threshold array to account for narrow valleys 
        bin_threshold = np.convolve(bin_threshold, kernel, mode='same')
        bin_threshold[bin_threshold > 0] = 1
        
        # separate the array into left and right sides of the maximum 
        max_bin_index = int(self.max_intensity_bin)
        left_of_max   = bin_threshold[:max_bin_index]
        right_of_max  = bin_threshold[max_bin_index:]

        # extract the start and end peak values 
        if (len(left_of_max) == 0):
            peak_start_bin = self.bin_index
            peak_end_bin   = self.bin_index 
        elif (len(right_of_max) == 0):
            peak_start_bin = self.ensemble_size
            peak_end_bin   = self.ensemble_size
        else:
            peak_start_bin = len(left_of_max) - np.argmax(left_of_max[::-1]==0)
            peak_end_bin   = np.argmax(right_of_max==0) + max_bin_index
        
        return(peak_start_bin, peak_end_bin)

