# MicronEnsemble.py
#
# Represents a Micron Sonar ensemble.
#   2020-03-13  zduguid@mit.edu         initial implementation 

import datetime
import dateutil
import math
import numpy as np
import pandas as pd 
from MicronSonar import MicronSonar

class MicronEnsemble(MicronSonar):
    def __init__(self, csv_row, date, bearing_bias=0, sonar_depth=None, 
        sonar_altitude=None):
        """Constructor of a Micron Sonar ensemble

        The Micron Sonar User Manual and Seanet DumpLog Software Manual were 
        used to write this code.

        Args: 
            csv_row: A list of strings that represent one ensemble from the
                Micron Sonar without any additional processing. The first 15
                values of the list are header variables, and then the
                remaining variables are acoustic intensity  values.
            date: A tuple of integers representing (year,month,day). The date 
                argument should match the date of which the data is recorded.
            bearing_bias: Optional argument to represent the bias of the 
                scanning sonar in units of degrees while the data was being 
                collected. The bearing bias may be due to the vehicle rolling, 
                or from an error in the mounting configuration. Positive 
                bearing bias corresponds with the vehicle rolling right due to 
                a banking right turn and negative bearing bias corresponds 
                with the vehicle rolling left due to a banking left turn.
            sonar_depth: depth in [m] of the sonar transducer head, used for 
                filtering out surface reflections in the intensity bins.
            sonar_altitude: altitude in [m] of the sonar transducer head, used 
                for filtering out bottom reflections in the intensity bins.
        """
        # use the parent constructor for defining Micron Sonar variables
        super().__init__()

        # initialize Micron Ensemble data array based on number of variables
        self._data_array     = np.zeros(self.ensemble_size)

        # parse header and acoustic intensities, compute derived variables 
        self.set_data('sonar_depth', sonar_depth)
        self.set_data('sonar_altitude', sonar_altitude)
        self.parse_header(csv_row, date, bearing_bias)
        self.parse_intensity_bins(csv_row)
        self.parse_derived_vars()
    

    @property
    def data_array(self):
        return self._data_array
    
    @property
    def intensity_data(self):
        return self.data_array[self.intensity_index:]


    def get_data(self, var):
        """Getter method for a give variable in the data array"""
        if (var not in self.label_set):
            raise ValueError("bad variable for: get(%s)" % (var))
        else:
            return(self.data_array[self.data_lookup[var]])


    def set_data(self, var, val, attribute=True):
        """Setter method for a variable-value pair to be put in the array"""
        if (var not in self.label_set):
            raise ValueError("bad variable for: set(%s, %s)" % (var, str(val)))
        self._data_array[self.data_lookup[var]] = val 
        if attribute: setattr(self, var, val)


    def parse_header(self, csv_row, date, bearing_bias):
        """Parses the header variables of the Micron Sonar ensemble

        Args: 
            csv_row: a list of strings representing an ensemble of data.
            date: a tuple of (year,month,day) values
            bearing_bias: a number that represents the bias of the sonar angle 
                when the data was collected. Positive bearing bias corresponds 
                with the vehicle rolling right due to a banked right turn. 
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

        # set the bearing bias to compute the bearing correctly 
        self.set_data('bearing_bias', bearing_bias)

        # convert header values to standard metric values 
        self.convert_to_metric('range_scale', self.dm_to_m)
        self.convert_to_metric('left_lim',    self.grad_to_deg)
        self.convert_to_metric('right_lim',   self.grad_to_deg)
        self.convert_to_metric('steps',       self.grad_to_deg*2)
        self.convert_to_metric('bearing',     self.grad_to_deg)
        self.convert_to_metric('ad_low',      self.bin_to_db)
        self.convert_to_metric('ad_span',     self.bin_to_db)

        # update coordinate system of Micron Sonar bearing 
        #   - includes bearing bias correction 
        bearing   = self.reorient_bearing(self.get_data('bearing'), bias=False)
        ref_world = self.reorient_bearing(self.get_data('bearing'), bias=True)
        left_lim  = self.reorient_bearing(self.get_data('left_lim'))
        right_lim = self.reorient_bearing(self.get_data('right_lim'))
        self.set_data('bearing',            bearing)
        self.set_data('bearing_ref_world',  ref_world)
        self.set_data('left_lim',           left_lim)
        self.set_data('right_lim',          right_lim)

        # compute incidence angle based upon bearing after corrected 
        #   - incidence angle is defined as the angle deviation away from 
        #     the sonar pointing directly upwards to the ocean (or ice) surface
        incidence_angle = abs(self.get_data('bearing_ref_world'))
        self.set_data('incidence_angle', incidence_angle)

        # compute the bin size in order to parse intensity bins correctly
        self.set_data('bin_size', self.range_scale / self.dbytes)


    def parse_intensity_bins(self, csv_row):
        """Parses acoustic intensity values and adds them to the data array"""
        # more intensity bins are received than the size of the array
        if self.dbytes > self.intensity_len:
            raise ValueError("bad number of bins: %d" % (self.dbytes))

        # add intensity values to the data array 
        for i in range(self.intensity_len):
            bin_label = 'bin_' + str(i)
            # parse the intensity value directly from the array 
            if (i+1) < self.dbytes: 
                bin_val   = float(csv_row[i+self.header_len])
            # keep extra bins set to zero  
            else:
                break
            self.set_data(bin_label, bin_val, attribute=False)
        
        # convert intensity bins from [0,255] -> [0,80dB]
        self.convert_to_metric('intensity', self.bin_to_db, intensity=True)

        # filter out blanking distance and surface/bottom reflections 
        self.filter_blanking_distance()
        self.filter_reflections()


    def parse_derived_vars(self):
        """Computes the derived quantities for the ensemble"""
        # compute bin size, max intensity, and max intensity bin
        self.set_data('max_intensity',     np.max(self.intensity_data))
        self.set_data('max_intensity_bin', np.argmax(self.intensity_data))

        # determine the peak of the signal according to the FWHM method
        peak_start_bin, peak_end_bin = self.get_peak_width()
        peak_width_bin = peak_end_bin - peak_start_bin
        self.set_data('peak_start_bin',  peak_start_bin)
        self.set_data('peak_end_bin',    peak_end_bin)
        self.set_data('peak_width_bin',  peak_width_bin)
        self.set_data('peak_start',      peak_start_bin * self.bin_size)
        self.set_data('peak_end',        peak_end_bin   * self.bin_size)
        self.set_data('peak_width',      peak_width_bin * self.bin_size)

        # compute the normalized max intensity using peak_start variable
        max_intensity_norm = self.max_intensity * self.peak_start
        self.set_data('max_intensity_norm', max_intensity_norm)

        # compute vertical range from slant range and bearing 
        self.get_vertical_range()

        # set ice classifications and labels to np.nan
        #   + classifications are made based on swaths not single ensembles
        #   + labels are specified manually 
        for ice_var in self.ice_vars:
            self.set_data(ice_var, np.nan)


    def convert_to_metric(self, variable, multiplier, attribute=True, 
        intensity=False):
        """Converts variable to standard metric value using the multiplier"""
        if not intensity:
            value = self.get_data(variable)
            self.set_data(variable, value * multiplier, attribute)
        else:
            self._data_array[self.intensity_index:] *= multiplier


    def reorient_bearing(self, bearing_deg, bias=False):
        """Reorient bearing from Micron Sonar default to custom orientation 

        Accounts for the bearing bias, which is passed to the constructor of 
        a MicronEnsemble object. See ReadMe for more in-depth explanation 
        of coordinate system.

        Args:
            bearing_deg = the bearing in degrees recorded by the Micron Sonar.
            bias: boolean to include the bearing bias or not in calculation 

        Returns:
            Bearing that has been rotated and flipped into a new orientation.
        """
        # constants 
        deg_in_circle    = 360
        deg_in_half      = 180
        bearing_deg     *= -1
        if bearing_deg  <= -deg_in_half:
            bearing_deg += deg_in_circle

        # if given, include bearing bias term (possible due to vehicle roll)
        if bias: 
            bearing_deg += self.get_data('bearing_bias')
        return(bearing_deg)


    def filter_blanking_distance(self):
        """Filters out the intensity values within blanking distance"""
        blanking_dist_bin = math.ceil(self.blanking_distance/self.bin_size)
        self._data_array[self.intensity_index : 
                         self.intensity_index + blanking_dist_bin] = 0


    def filter_reflections(self):
        """Filters out surface and bottom reflections"""
        # epsilon defined to detect when cosine is sufficiently close to zero
        epsilon  = 1e-3
        cos_bear = abs(np.cos(self.bearing_ref_world * self.deg_to_rad))

        def filter_at_dist(dist):
            """Inner function for filtering array values"""
            bin_index = np.max(math.floor(dist/self.bin_size))
            self._data_array[self.intensity_index + bin_index:] = 0

        # filter-out surface reflections when depth is known
        if ((self.sonar_depth) and 
            (abs(self.bearing_ref_world) < 90) and
            (cos_bear >= epsilon)):
            filter_at_dist(self.sonar_depth*self.reflection_factor/cos_bear)
        
        # filter-out bottom reflections when depth is known
        if ((self.sonar_altitude) and 
            (abs(self.bearing_ref_world) > 90) and
            (cos_bear >= epsilon)):
            filter_at_dist(self.sonar_altitude*self.reflection_factor/cos_bear)


    def get_peak_width(self):
        """Computes the width of the dominant peak of the ensemble

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
        left_of_max   = bin_threshold[             :max_bin_index]
        right_of_max  = bin_threshold[max_bin_index:             ]

        # extract the start and end peak values 
        if (len(left_of_max) == 0) or (len(right_of_max) == 0):
            peak_start_bin = np.nan
            peak_end_bin   = np.nan 
        else:
            peak_start_bin = len(left_of_max) - np.argmax(left_of_max[::-1]==0)
            peak_end_bin   = np.argmax(right_of_max==0) + max_bin_index
        
        return(peak_start_bin, peak_end_bin)


    def get_vertical_range(self):
        """Computes the vertical range using slant range and bearing"""
        cos_bearing = np.cos(self.bearing_ref_world * self.deg_to_rad)

        # compute vertical range depending on the cosine of the bearing 
        if cos_bearing < 0:
            vertical_range = np.nan
        else:
            vertical_range = self.peak_start*cos_bearing

        # set the vertical range value 
        self.set_data('vertical_range', vertical_range)

