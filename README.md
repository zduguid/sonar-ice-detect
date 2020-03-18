# sonar-ice-detect
<!---------------------------------------------->

## Table of Contents 
- [Data Field Information](#data-field-information)
  - [Header Variables](#header-variables)
  - [Intensity Variables](#intensity-variables)
  - [Derived Variables](#derived-variables)  
  - [Ice Classification Variables](#ice-classification-variables)
  - [Coordinate System Definition](#coordinate-system-definition)
- [Pseudocode for Parsing an Ensemble](#pseudocode-for-parsing-an-ensemble)
- [Miscellaneous Notes](#miscellaneous-notes)
- [List of TODOs](#list-of-todos)


<!-----------------------------------------------
Most Recent Changes:
- defined different ice-categories and quantities (with setter functions)
- added vertical range field to the ensemble 
- moved plotting functions out of jupyter notebook and into micron_plotter
- add helper functions for setting labels for bearing ranges 

Changes to Make before Commit:
------------------------------------------------>


<!---------------------------------------------->
## Data Field Information 

### Header Variables 
More info coming soon.

### Intensity Variables 
More info coming soon.

### Derived Variables 
More info coming soon.

### Ice Classification Variables 
More info coming soon.

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


<!---------------------------------------------->
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


<!---------------------------------------------->
## Miscellaneous Notes
- The "Micron Sonar User Manual" and the "Seanet DumpLog Software Manual" documents where used extensively when creating this software. These references can be viewed in the `doc/` directory.
- The Micron Sonar receiver has an 80dB dynamic range and signal levels are processed internally such that one byte per intensity value yields a range: [0,255], which in turn maps to the dynamic range of the sonar: [0,80dB].


<!---------------------------------------------->
## List of TODOs

### `MicronEnsemble` TODOs
- dont use `ice-per` classification? -- may not make sense for small scanning window that the scanning sonar is able to view. instead, ice percentage can be computed in a post-processing effort with geo-referenced swaths over a larger area of survey  
- how to normalize with respect to gain and distance from transducer? (already have distance factored into the normalized max intensity)
- manually set `intensity_len` constant value for all ensemble files. find the max value that can be expected by examining the sonar data file 
- convert `status` and `Hdctrl` to binary and process for status (reject values that are not OK). see some initial code for doing this in the Python notebook. 
    - investigate why status value is 144? (if 144 is int -> 8 bits, if 144 is hex -> requires 9 bits) (call Tritech about this?)
 
### `MicronTimeSeries` TODOs
- add ice detection/classification to the ensemble (perhaps just runs on the most recent swath)
- write function to combine two different time-series 
- write function to save time_series to csv file 
- write function to parse time_series from CSV file 
    - write new Micron class that is the superclass to the Ensemble and TimeSeries, this allows same definition of variable names 
- compute `ice_roughness` and `ice_slope` calculations 
- collect groups of ensembles into "swaths" which are used for classification. Note that the classification function should operate in a wide variety of polling strategies. Perhaps the TimeSeries object can keep track of a running list of "most recent" swath collected (with time bounds potentially?) that keep track of most recently seen bearing_ref_world values. Then a function that classifies ice-types will run on the most recent swath.
- better plan for object inheritance between the Micron Sonar and the Pathfinder? -- probably an unnecessary effort given how many subtle differences between the two instruments and their data products. That said, trying to use a similar design architecture between the two are useful for readability and usability. 

### `micron_reader` TODOs
