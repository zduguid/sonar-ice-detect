# micron_plotter.py
# 
# Plotting utilities for Micron Sonar
#   2020-03-16  zduguid@mit.edu         initial implementation  

import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.cm as cm
import matplotlib.pyplot as plt



def plot_ensemble(ensemble, location, output_file=None):
    """Plots and Intensity in dB vs. Distance from transducer in meters
    
    Also highlights the peak width selection, which is one of the primary
    features used for classifying different ice situations. 
    
    Args: 
        ensemble: a Micron Ensemble to be visualized.
        location: string location where the data was collected.
        output_file: save name for the generated plot.
    """
    # constants 
    deg_in_quadrant = 90
    ylim_max        = 25

    if ensemble.peak_width_bin == 0:  peak_alpha = 0
    else:                             peak_alpha = 0.3

    months = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',  5:'May',  6:'Jun',
              7:'Jul', 8:'Aug', 9:'Sep',10:'Oct', 11:'Nov', 12:'Dec'}

    # generate plots
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(15,8))
    ax.plot(ensemble.intensity_data, linewidth=3, color='tab:blue')
    plt.axvspan(ensemble.peak_start_bin, ensemble.peak_end_bin, 
        alpha=peak_alpha, color='tab:purple')

    # generate titles 
    fig.suptitle('Micron Sonar Ensemble, %s, %i %s %i' % 
                    (location, ensemble.day, months[ensemble.month], 
                     ensemble.year), 
                 fontsize=22, fontweight='bold')

    incidence = "Incidence: %3i$^\circ$   " % (abs(ensemble.bearing_ref_world))
    bearing   = "Bearing: %3i$^\circ$   "   % (ensemble.bearing)
    intensity = "Intensity: %2d dB   "      % (ensemble.max_intensity)
    peak      = "Peak Width: %.2f m"        % (ensemble.peak_width)

    ax.set_title(incidence+bearing+intensity+peak, 
        fontsize=18, fontname='Courier New')

    # generate ticks and label axes 
    num_ticks = 11
    xticks = np.arange(0, ensemble.dbytes, ensemble.dbytes/(num_ticks-1))
    xticks = np.append(xticks, ensemble.dbytes)
    xtick_labels = ["%.1f" % (e*ensemble.bin_size) for e in xticks]
    ax.set_ylim(0, ylim_max)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xtick_labels)
    ax.set_xlabel('Distance from Transducer [m]')
    ax.set_ylabel('Intensity [dB]')
    ax.legend(['Intensity', 'Rolling Median','FWHM'], loc='best')

    # save the file if specified
    if output_file:
        plt.savefig("../figs/%s.png" % (output_file))
    plt.close()



def plot_polar(time_series, separator=None, pad=0.2, output_file=None, 
    sonar_depth=None):
    """Generates a plot in polar coordinates of a Micron Time-Series

    It is recommended to first crop the time series such that only one swath 
    is plotted in polar coordinates. Doing so may greatly speed up plotting 
    time.

    Args: 
        time_series: a Micron Time-Series to be visualized
        separator: bearing angle separation between two different ice types.
        pad: half the angular width of the separator when visualized
        output_file: save name for the generated plot.
    """
    depth_factor  = time_series.REFLECTION_FACTOR
    deg_to_rad    = time_series.DEG_TO_RAD
    min_depth     = time_series.BLANKING_DISTANCE
    ultra_steps   = 0.9
    deg_in_circle = 360
    bin_size      = time_series.df['bin_size'][0]
    steps         = time_series.df['steps'][0]
    interpolation = int(steps/ultra_steps) - 1

    # plot only first swath 
    swath = time_series.crop_on_bearing(single_swath=True)     

    # filter out appropriate ranges 
    bin_idx     = swath.intensity_index
    bin_labels  = swath.df.columns[bin_idx:]
    sub_cols    = ['bearing_ref_world'] + list(bin_labels)
    df          = swath.df[sub_cols]

    # melt data-frame into three columns: bearing, range, intensity 
    new_cols   = ['bearing_ref_world'] + \
                 [int(label[4:])*bin_size for label in bin_labels]
    df.columns = new_cols
    df = pd.melt(df, id_vars=['bearing_ref_world'], var_name='range',
                 value_name='intensity')

    # collected interpolated data in a list of new data frames 
    frames = []
    unique_bearings = sorted(list(set(df.bearing_ref_world)))

    # parse the left and right bearing increments to interpolate between them
    for i in range(len(unique_bearings)-1):
        df_left  = df[df.bearing_ref_world==unique_bearings[i]]
        df_right = df[df.bearing_ref_world==unique_bearings[i+1]]
        intensity_left  = np.array(df_left.intensity)
        
        # interpolate between the left and the right side if same size
        try:
            intensity_delta = np.array(df_right.intensity) - np.array(df_left.intensity)
        except ValueError:
            intensity_delta = np.zeros(len(intensity_left))
        
        # interpolate to match resolution of the ultra-high setting 
        for j in range(1, interpolation+1):
            new_angle      = unique_bearings[i] + j*ultra_steps
            range_data     = np.array(df_left.range)
            bearing_data   = new_angle*np.ones(len(range_data))
            intensity_data = intensity_left + (j/interpolation)*intensity_delta
            frames.append(pd.DataFrame(
                data={'bearing_ref_world' : bearing_data,
                      'range'             : range_data,
                      'intensity'         : intensity_data})
            )

    # combine interpolated data and given data 
    df = pd.concat([df] + frames)

    # initialize plot format 
    sns.set(font_scale = 1.5)
    fig = plt.figure(figsize=(15,15))
    ax  = fig.add_subplot(111, projection='polar')
    ax.set_xticks(deg_to_rad * np.linspace(180,  -180, 24, endpoint=False))

    # plot the data 
    area = np.asarray(100*df['range'] + 10).astype(np.float64)
    img  = ax.scatter(df['bearing_ref_world']*deg_to_rad, df['range'], s=area, 
                      c=df['intensity'],cmap='viridis')

    if sonar_depth: 
        ax.set_rmax(sonar_depth*depth_factor)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetalim(-np.pi, np.pi)
    ax.set_title('Micron Sonar Swath, Woods Hole MA', 
                 fontsize=22, fontweight='bold')

    # set colorbar ticks and labels 
    fraction    = 0.025
    increment   = 5
    cbar_max    = math.ceil(np.max(df['intensity'])/increment)*increment
    cbar_ticks  = range(0,cbar_max,increment)
    cbar_labels = ["%2d dB" %(i) for i in cbar_ticks]
    cbar = fig.colorbar(img, fraction=fraction, ticks=cbar_ticks)
    cbar.ax.set_yticklabels(cbar_labels)

    # add orange divider at the boundary 
    if separator is not None:
        plt.axvspan((separator-pad)*deg_to_rad, 
                    (separator+pad)*deg_to_rad,         
                    color='tab:orange', alpha=0.6)
        
    # save the figure
    # if output_file: 
    plt.savefig('/Users/zduguid/Desktop/dat/tmp-polar.png')



def plot_incidence_curves(time_series, variable_size=False, output_file=None,
    axis_limits=False):
    """Plot Max Intensity Norm vs. Angle of Incidence for the time-series

    Args:
        time_series: a Micron Time-Series to be visualized.
        variable_size: boolean flag to plot points with varying size.
        output_file: save name for the generated plot.        
    """
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(15,8))
    pad_x = 2
    pad_y = 2
    y_max = 60
    x_max = 60

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def is_valid_label(s):
        return(is_number(s) and (float(s) in categories.keys()))

    def get_legend_items(handles, labels):
        valid = [is_valid_label(label) for label in labels]
        if False in valid[1:]:
            valid_index = valid[1:].index(False) + 1
        else: 
            valid_index = len(labels)
        new_labels  = [categories[float(l)] for l in labels[1:valid_index]]
        new_handles = [handles[i] for i in range(1,valid_index)]
        return(new_handles, new_labels)

    ice_categories = [
        (0,  'Water',           'tab:blue'),
        (10, 'Marginal Ice',    'tab:orange'),
        (20, 'Frazil Ice',      'tab:pink'),
        (21, 'Slushy Ice',      'tab:pink'),
        (22, 'Smooth Thin Ice', 'tab:red'),
        (23, 'Rough Thin Ice',  'tab:red'),
        (30, 'Smooth Thick Ice','tab:brown'),
        (31, 'Rough Thick Ice', 'tab:brown'),
        (32, 'Pressure Ridge ', 'tab:gray')
    ]

    categories = {num : label for (num, label, color) in ice_categories}
    palette    = {num : color for (num, label, color) in ice_categories}

    if variable_size: size = time_series.df.peak_width
    else:             size = None

    # plot scatter plot of incidence angle and intensity values
    ax = sns.scatterplot(
        x=time_series.df.incidence_angle, 
        # y=time_series.df.max_intensity_norm,
        y=time_series.df.max_intensity,
        size=size,
        hue=time_series.df.label_ice_category,
        palette=palette,
        legend='brief'
    )

    # set titles and labels
    ax.set_title('Incidence vs Intensity for Water and Ice', 
                 fontsize=22, fontweight='bold')
    ax.set_xlabel('Incidence Angle [deg]')
    ax.set_ylabel('Max Intensity [dB]')

    if axis_limits:
        ax.set_ylim(-pad_y, y_max+pad_y)
        ax.set_xlim(-pad_x, x_max+pad_x)

    # only keep numeric labels, convert number to ice category
    handles, labels = ax.get_legend_handles_labels()
    new_handles, new_labels = get_legend_items(handles,labels)
    ax.legend(new_handles, new_labels, title='Ice Category', loc='lower left')

    # save the figure
    # if output_file: plt.savefig("../figs/%s.png" % (output_file))
    plt.savefig('/Users/zduguid/Desktop/fig/tmp-incidence.png')



def plot_features(time_series):
    """Uses plotly to generate interactive 3D plots

    Args:
        time_series: a Micron Time-Series to be visualized
    """
    fig = px.scatter_3d(
        time_series.df, 
        x = 'bearing', 
        y = 'peak_width', 
        z = 'max_intensity',
        title = "Micron Sonar Time Series in Feature Space",
        opacity=0.5,
        labels={
            "bearing" : "Bearing Angle [deg]",  
            "peak_width"        : "Peak Width [m]", 
            "max_intensity"     : "max_intensity [dB]"
        }
        
    )
    fig.show()