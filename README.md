# sonar-ice-detect
<!---------------------------------------------------------------------------->

## Table of Contents 
- [Data Field Information](#data-field-information)
  - [Header Variables](#header-variables)
  - [Intensity Variables](#intensity-variables)
  - [Derived Variables](#derived-variables)  
  - [Ice Classification Variables](#ice-classification-variables)
  - [Coordinate System Definition](#coordinate-system-definition)
  - [Ensemble Size](#ensemble-size)
- [Pseudocode for Parsing an Ensemble](#pseudocode-for-parsing-an-ensemble)
- [Miscellaneous Notes](#miscellaneous-notes)
- [List of TODOs](#list-of-todos)


<!-------------------------------------
Most Recent Changes:
- change variable lists to tuples for better immutability and for ability to take a hash on the list of variables 
- change from_csv function to be a class method 
- add from_raw_csv file to time_series, remove micron_reader file 
- add from_directory and from_frames constructors to time series 
- add version property to time series 

Changes to Make before Commit:
- fix polar_plot function (need it to work with multiple resolutions)
  - plt.polar() seems like a promising option 
-------------------------------------->


<!---------------------------------------------------------------------------->
## Data Field Information 

<!------------------------------------>
### Header Variables 
More info coming soon.

#### Note on the Bearing Step Size
There is a discrepancy between the value given in the Micron Sonar data-field for the step-size of the ensemble and the actual difference in bearing between successive measurements. As shown in the table below, for all resolution settings, the actual difference in bearing between successive measurements is  twice the value of what is reported by the Micron Sonar. Note, the value by the Micron Sonar is in 1/16 Gradians according to the Tritech Seanet DumpLog documentation. I believe that this is due small error in the Tritech documentation or a (relatively) harmless bug in the Micron Sonar logging software. The discrepancy has been accounted for in the `MicronEnsemble` class, so now the steps attribute is consistent with the difference between successive bearing measurements. 

| Resolution Setting  | Steps [deg], Tritech Documentation | Steps [deg], Actual Observation | 
| ---:   |  :---      | :--- |
|ultra   | 0.45 deg   | 0.9  |
|high    | 0.9 deg    | 1.8  |
|medium  | 1.8 deg    | 3.6  |
|low     | 3.6 deg    | 7.2  |

<!------------------------------------>
### Intensity Variables 
More info coming soon.

<!------------------------------------>
### Derived Variables 
More info coming soon.

<!------------------------------------>
### Ice Classification Variables 
More info coming soon.

<!------------------------------------>
### Coordinate System Definition
#### MicronEnsemble Coordinate System
| Angle       | Direction   | 
| ---:        | ---         | 
| 0   degrees |  upwards    |
| 90  degrees |  starboard  |
| 180 degrees |  downwards  |
| -180 degrees|  downwards  |
| -90 degrees |  port       |

#### Original Micron Sonar Coordinate System
| Angle       | Direction   | 
| ---:        | ---         | 
| 0   degrees |  upwards    |
| 90  degrees |  port       |
| 180 degrees |  downwards  |
| 270 degrees |  starboard  |

<!------------------------------------>
### Ensemble Size 
Upon inspection of the Micron Sonar data, the number of intensity bins included in the ensemble is dependent on multiple settings, including the range setting and the resolution setting. The rule that dictates the number of intensity bins in a given file is not obvious. Unfortunately, the Micron Sonar user manual and Seanet DumpLog software manual do not touch on this subtlety.

To showcase the variance in the number of intensity bins, we kept all sonar settings constant while varying the range setting and we recorded the number of intensity bins that were included in the file. Note that the maximum range of the Micron Sonar is 75m, so any range setting at 80m or above does not obey the specification of the instrument. Interestingly, the largest number of intensity bins, 469, occurred for the 8m range case. No obvious pattern emerges that describes the number of intensity bins as a function of sensor range. 

| Range [m]   | # Intensity Bins|
| ---:        | ---             | 
| 2           | 434             |
| 6           | 465             |
| 8           | 469             |
| 10          | 461             |
| 20          | 460             |
| 30          | 461             |
| 50          | 461             |
| 80          | 461             |
| 100         | 455             |
| 120         | 450             |
| 150         | 462             |
| 180         | 458             |
| 200         | 455             |
| 250         | 435             |
| 300         | 442             |
| 350         | 421             |
| 400         | 428             |
| 800         | 422             |


<!---------------------------------------------------------------------------->
## Pseudocode for Parsing an Ensemble
1. Parse Header Variables
    1. Convert Header Variables to standard metric quantities when applicable.
    1. Perform coordinate transformation for bearing variables
    1. Parse `status` and `hdctrl` bit encodings (Not implemented yet)
    1. Compute the `bin_size` variable so that the intensity values are parsed correctly. This is the only Derived Variable computed alongside the Header Variables.
1. Parse Intensity Variables
    1. Convert Intensity Variables to standard metric quantities.
    1. Filter out Intensity Variables within the blanking distance of the sonar.
    1. Filter out Intensity Variables that are due to surface or bottom reflections. 
1. Parse Derived Variables 
    1. Compute maximum intensity information, including normalized maximum intensity that multiplies the distance of maximum intensity bin by the distance between the transducer head and the maximum intensity bin. This normalized maximum intensity is computed to account for the decay of acoustic intensity with the inverse distance through the water column.
    1. Determine the peak of the signal by using the [Full Width Half Maximum (FWHM) method](https://en.wikipedia.org/wiki/Full_width_at_half_maximum).


<!---------------------------------------------------------------------------->
## Miscellaneous Notes
- The "Micron Sonar User Manual" and the "Seanet DumpLog Software Manual" documents where used extensively when creating this software. These references can be viewed in the `doc/` directory.
- The Micron Sonar receiver has an 80dB dynamic range and signal levels are processed internally such that one byte per intensity value yields a range: [0,255], which in turn maps to the dynamic range of the sonar: [0,80dB].
- The Micron Sonar classes in this repository and the Pathfinder classes in the `dvl-nav` repository have been designed to have a relatively similar structure and readability. However, as a result of many subtle differences between the two sensors, there is not a plan to connect the two sets of classes via a parent super-class. 
- As changes are made to MicronSonar class, more column variables may be added or removed. As a result, future versions may not be compatible with previous versions because the columns are no longer the same. To account for this, the user can either re-parse the raw CSV files and save the output with the new format, or the old files can be opened and adjusted to match the format of the new time series format.


<!---------------------------------------------------------------------------->
## List of TODOs

<!------------------------------------>
### MicronSonar TODOs
- make constant attributes of the class be ALL CAPS 

<!------------------------------------>
### MicronEnsemble TODOs
- dont use `ice-per` classification? -- may not make sense for small scanning window that the scanning sonar is able to view. instead, ice percentage can be computed in a post-processing effort with geo-referenced swaths over a larger area of survey  
- how to normalize with respect to gain and distance from transducer? (already have distance factored into the normalized max intensity)
- convert `status` and `Hdctrl` to binary and process for status (reject values that are not OK). see some initial code for doing this in the Python notebook. 
    - investigate why status value is 144? (if 144 is int -> 8 bits, if 144 is hex -> requires 9 bits) (contact Tritech about this?)
- what dictates the number of dbytes included in an ensemble? -- not obvious upon inspecting the data-files, but perhaps it will be easier to discern when using a low-level polling method. (contact Tritech about this?)
- why does the steps variable not match the difference between successive bearing measurements? (contact Tritech about this?)
 
<!------------------------------------>
### MicronTimeSeries TODOs
- when `ts.set_label_by_bearing()` is called, *sometimes* a `SettingFromCopy` warning is displayed. I believe this is a result of setting a value to a DataFrame via the `iloc` method. This seems to be a common issue discussed on Stack Overflow and other websites. The confusing part to me is that the warning seems to be displayed in a non-deterministic patter (i.e. it is not always displayed and there is not a clear patter that leads to this warning)
- compute `ice_roughness` and `ice_slope` calculations 
- collect groups of ensembles into "swaths" which are used for classification. Note that the classification function should operate in a wide variety of polling strategies. Perhaps the TimeSeries object can keep track of a running list of "most recent" swath collected (with time bounds potentially?) that keep track of most recently seen bearing_ref_world values. Then a function that classifies ice-types will run on the most recent swath.

<!------------------------------------>
### micron_plotter TODOs
- fix polar plot (scatter plot doesn't fill in the entire area)
- add radial distance markings to the polar plot 