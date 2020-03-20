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
Notes:
- red color:  cc0000
- blue color: 0000cc

Most Recent Changes:
- hard-coded size of array to ensure arrays are all the same size 
- added salt-water flag 
- added ability to save and open csv files 

Changes to Make before Commit:
-------------------------------------->


<!---------------------------------------------------------------------------->
## Data Field Information 

<!------------------------------------>
### Header Variables 
More info coming soon.
`resolution`  `ultra (8), high (16), medium (32), low(64)`

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


<!---------------------------------------------------------------------------->
## List of TODOs

<!------------------------------------>
### `MicronEnsemble` TODOs
- dont use `ice-per` classification? -- may not make sense for small scanning window that the scanning sonar is able to view. instead, ice percentage can be computed in a post-processing effort with geo-referenced swaths over a larger area of survey  
- how to normalize with respect to gain and distance from transducer? (already have distance factored into the normalized max intensity)
- manually set `intensity_len` constant value for all ensemble files. find the max value that can be expected by examining the sonar data file 
- convert `status` and `Hdctrl` to binary and process for status (reject values that are not OK). see some initial code for doing this in the Python notebook. 
    - investigate why status value is 144? (if 144 is int -> 8 bits, if 144 is hex -> requires 9 bits) (call Tritech about this?)
- what dictates the number of dbytes included in an ensemble? -- not obvious upon inspecting the data-files, but perhaps it will be easier to discern when using a low-level polling method. 
 
<!------------------------------------>
### `MicronTimeSeries` TODOs
- add ice detection/classification to the ensemble (perhaps just runs on the most recent swath)
- if data in ensemble_list is from different time points or is not currently in the DataFrame, add them (make this more like a "union" function between self.df and self.column_list
- write function to combine two different time-series 
- write function to save time_series to csv file 
- write function to parse time_series from CSV file 
    - write new Micron class that is the superclass to the Ensemble and TimeSeries, this allows same definition of variable names 
- compute `ice_roughness` and `ice_slope` calculations 
- collect groups of ensembles into "swaths" which are used for classification. Note that the classification function should operate in a wide variety of polling strategies. Perhaps the TimeSeries object can keep track of a running list of "most recent" swath collected (with time bounds potentially?) that keep track of most recently seen bearing_ref_world values. Then a function that classifies ice-types will run on the most recent swath.
- better plan for object inheritance between the Micron Sonar and the Pathfinder? -- probably an unnecessary effort given how many subtle differences between the two instruments and their data products. That said, trying to use a similar design architecture between the two are useful for readability and usability. 

<!------------------------------------>
### `micron_reader` TODOs
