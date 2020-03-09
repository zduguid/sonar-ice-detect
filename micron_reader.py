# micron_reader.py
# 
# Reads a time series of Micron Sonar data from a csv file.
#   2020-03-15  zduguid@mit.edu         initial implementation 

import glob
import os
import sys
import time
import pandas as pd
import numpy as np
from MicronEnsemble import MicronEnsemble
from MicronTimeSeries import MicronTimeSeries


def micron_reader(filepath, location, date, 
                  save=True, plot=False,
                  plot_angle_spacing=5):
    """Reads a Micron Sonar time series from a saved csv file. 

    This function assumes that the saved csv file was generated from 
    Tritech's Seanet DumpLog software. The manual for this software can be 
    found in the 'doc' directory in this repository.

    Args: 
        filepath: the file path to the Micron Sonar csv file to read.
        location: the location where data was collected (ex: "Woods Hole MA")
        date: tuple of integers (year,month,day) (ex: 2020,01,24)
        save: boolean flag to save the parsed data or not.
        plot: boolean flag to plot the parsed data or not. 
        plot_angle_spacing: plotting parameter to indicate the spacing 
            between range-intensity to be generated. For example, if this 
            parameter is 2, every other angle parsed will be plotted. 
    """

    # plotting parameters 
    plot_current_delta    = 0
    plot_previous_angle   = None
    plot_angles_seen      = set([])
    plot_peak_width_alpha = 0.3

    # open the csv file 
    csv_file = open(filepath)
    header  = csv_file.readline().split(',') 

    # for line in csvfile:  
    csv_row = csv_file.readline().split(',')

    # ignore the empty row at the end of the file 
    # if (len(csv_row) == 1):
    #     break

    ensemble = MicronEnsemble(csv_row, date)
    return(ensemble)
