# micron_reader.py
# 
# Reads a time series of Micron Sonar data from a csv file.
#   2020-03-13  zduguid@mit.edu         initial implementation 

import glob
import os
import sys
import time
import pandas as pd
import numpy as np
import MicronEnsemble
import MicronTimeSeries


def micron_reader(filepath, location, date, 
                  bearing_bias=0,
                  constant_depth=None,
                  constant_altitude=None,
                  labels=None):
    """Reads a Micron Sonar time series from a saved csv file. 

    This function assumes that the saved csv file was generated from 
    Tritech's Seanet DumpLog software. The manual for this software can be 
    found in the 'doc' directory in this repository.

    Args: 
        filepath: the file path to the Micron Sonar csv file to read.
        location: the location where data was collected (ex: "Woods Hole MA")
        date: tuple of integers (year,month,day) (ex: 2020,01,24)
        constant_depth: Depth in [m] that the sonar is operating
        constant_altitude: Altitude in [m] that the sonar is operating
    Returns:
        Micron Sonar Time Series object with the DataFrame already computed.
    """
    counter = 0
    print_increment = 100
    filename = filepath.split('/')[-1]
    print('Parsing: %s' % (filename))

    # plotting parameters 
    plot_current_delta    = 0
    plot_previous_angle   = None
    plot_angles_seen      = set([])
    plot_peak_width_alpha = 0.3

    # open the csv file 
    csv_file = open(filepath)
    header   = csv_file.readline().split(',') 

    # initialize a time series object 
    time_series = MicronTimeSeries.MicronTimeSeries()

    # add all ensembles to the time series 
    for line in csv_file:  
        counter+= 1
        csv_row = csv_file.readline().split(',')

        # ignore the empty row at the end of the file 
        if (len(csv_row) == 1):
            break

        # parse the Micron Sonar ensemble
        ensemble = MicronEnsemble.MicronEnsemble(
            csv_row, date, bearing_bias, sonar_depth=constant_depth,
            sonar_altitude=constant_altitude
        )
        
        # add the parsed ensemble to the time series 
        time_series.add_ensemble(ensemble)
        if (counter%print_increment == 0):
            print("  >> Ensembles Parsed: %5d" % (counter))

    # convert the list of ensembles into a DataFrame and then return
    time_series.to_dataframe()
    print('  >> Finished Parsing!')
    return(time_series)
