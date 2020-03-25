# Micron.py
# 
# Superclass for Micron Sonar Data 
#   2020-03-25  zduguid@mit.edu         initial implementation 

import numpy as np

class MicronSonar(object):
    def __init__(self):
        """Parent class for Micron Sonar data

        Used to define Micron variables that are constant between different 
        Micron Sonar objects. 
        """
        # unit conversion multipliers 
        self.DEG_TO_RAD  = np.pi/180    # [deg] -> [rad]
        self.RAD_TO_DEG  = 180/np.pi    # [rad] -> [deg]
        self.GRAD_TO_DEG = 360/6400     # [1/16 Gradians] -> [deg]
        self.DM_TO_M     = 1/10         # [dm] -> [m]
        self.BIN_TO_DB   = 80/255       # [0,255] -> [0,80dB]

        # other constants 
        #   - the min_range parameter was taken from the sonar spec sheet
        #   - the roll_median_len and conv_kernel_len parameters were tuned to
        #     achieve the desired performance.
        self.ROLL_MEDIAN_LEN   = 5      # used for taking rolling median
        self.CONV_KERNEL_LEN   = 5      # used when taking convolution 
        self.BLANKING_DISTANCE = 0.35   # min-range of Micron Sonar in [m]
        self.REFLECTION_FACTOR = 1.5    # used for filtering out reflections 
        self.COS_EPSILON       = 1e-3   # used to avoid division by zero

        # tuple of variables automatically reported by Micron Sonar
        #   - DO NOT edit header_vars, sonar outputs exactly in this order
        self._header_vars = (
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
            'bearing',              # bearing relative to the transducer head 
            'dbytes'                # the number of retrieved intensity values
        )

        # tuple of variables derived from the intensity and header values
        #   - add variables to derived_vars as necessary
        self._derived_vars = (
            'year',                 # year that the data was recorded
            'month',                # month that the data was recorded
            'day',                  # day that the data was recorded
            'sonar_depth',          # sonar depth in [m]
            'sonar_altitude',       # sonar altitude in [m]
            'bearing_bias',         # bias in bearing (coming from vehicle)
            'bearing_ref_world',    # bearing reference to the horizontal plane
            'incidence_angle',      # incidence angle 
            'bin_size',             # size of each bin, in [m]
            'max_intensity',        # maximum intensity measured, in [dB]
            'max_intensity_bin',    # bin location of the maximum value 
            'max_intensity_norm',   # max intensity [dB] * distance [m]
            'peak_start_bin',       # bin location of the start of the peak
            'peak_start',           # distance from transducer to start of peak
            'peak_end_bin',         # bin location of the end of the peak
            'peak_end',             # distance from transducer to end of peak
            'peak_width_bin',       # bin width of the peak
            'peak_width',           # width of peak in terms of distance
            'vertical_range'        # vertical range from transducer head [m]
        )

        # tuple of variables related to the classification of ice
        #   + each variable has a classification (automated process) and
        #     labeled (manual process)
        #   + the goal is to use the labeled data to train a high-performance 
        #     classification system
        self._ice_vars = (
            'class_ice_category',   # classification result for ice-category
            'class_ice_presence',   # classification result for ice-presence
            'class_ice_percent',    # classification result for ice-percentage
            'class_ice_thickness',  # classification result for ice-thickness 
            'class_ice_slope',      # classification result for ice-slope
            'class_ice_roughness',  # classification result for ice-roughness
            'label_ice_category',   # user specified label  for ice-category
            'label_ice_presence',   # user specified label  for ice-presence
            'label_ice_percent',    # user specified label  for ice-percentage
            'label_ice_thickness',  # user specified label  for ice-thickness 
            'label_ice_slope',      # user specified label  for ice-slope
            'label_ice_roughness',  # user specified label  for ice-roughness
            'label_saltwater_flag'  # value 1 means saltwater, 0 freshwater
        )

        # bookkeep length of each variable type 
        self._header_len     = len(self.header_vars)
        self._derived_len    = len(self.derived_vars)
        self._ice_len        = len(self.ice_vars)
        self._intensity_len  = 500 
        
        # tuple of variables related to the intensity bins of the sonar
        self._intensity_vars = tuple(["bin_%s"%i for i in \
                                      range(self.intensity_len)])
        # bookkeep list of all ensemble variables
        self._label_list        = self.header_vars  + \
                                  self.derived_vars + \
                                  self.ice_vars     + \
                                  self.intensity_vars 
        self._intensity_index   = self.header_len   + \
                                  self.derived_len  + \
                                  self.ice_len
        self._label_set         = set(self.label_list)
        self._ensemble_size     = len(self.label_list)
        self._data_lookup       = {self.label_list[i]:i \
                                   for i in range(self.ensemble_size)}


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
    def label_list(self):
        return self._label_list
    
    @property
    def label_set(self):
        return self._label_set

    @property
    def data_lookup(self):
        return self._data_lookup

    @property
    def header_len(self):
        return self._header_len

    @property
    def derived_len(self):
        return self._derived_len
    
    @property
    def ice_len(self):
        return self._ice_len

    @property
    def intensity_len(self):
        return self._intensity_len

    @property
    def intensity_index(self):
        return self._intensity_index
    
    @property
    def ensemble_size(self):
        return self._ensemble_size
    
    