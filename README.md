# sonar-ice-detect
-------------------------------------------------

## Table of Contents 
- [Data Field Information](#data-field-information)
  - [Header Variables](#header-variables)
  - [Intensity Variables](#intensity-variables)
  - [Derived Variables](#derived-variables)  
  - [Coordinate System Definition](#coordinate-system-definition)
- [Pseudocode for Parsing an Ensemble](#pseudocode-for-parsing-an-ensemble)
- [Miscellaneous Notes](#miscellaneous-notes)
- [List of TODOs](#list-of-todos)

<!-- 
-------------------------------------------------
Most Recent Changes:
- add hook for bearing bias for the micron sonar 
- add incidence angle attribute
- change coordinate system for bearing 
- add new attribute: "normalized max intensity" to account for 1/r decay 
- add ability to plot the whole intensity plot similar to seanet pro
- filter out values above surface reflection
- reorganized MicronEnsemble class to match pseudocode order of opertions 
- added more details to ReadMe document
- doc strings for time-series and micron-reader
-------------------------------------------------
 -->

-------------------------------------------------
## Data Field Information 

### Header Variables 
More info coming soon.

### Intensity Variables 
More info coming soon.

### Derived Variables 
More info coming soon.

### Coordinate System Definition
#### MicronEnsemble Coordinate System
| Angle       | Direction   | 
| ---         | ---         | 
| 0   degrees |  upwards    |
| 90  degrees |  starboard  |
| 180 degrees |  downwards  |
| -180 degrees|  downwards  |
| -90 degrees |  port       |

#### Original Micron Sonar Coordinate System
| Angle       | Direction   | 
| ---         | ---         | 
| 0   degrees |  upwards    |
| 90  degrees |  port       |
| 180 degrees |  downwards  |
| 270 degrees |  starboard  |


-------------------------------------------------
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


-------------------------------------------------
## Miscellaneous Notes
- The "Micron Sonar User Manual" and the "Seanet DumpLog Software Manual" documents where used extensively when creating this software. These references can be viewed in the `doc/` directory.
- The Micron Sonar receiver has an 80dB dynamic range and signal levels are processed internally such that one byte per intensity value yields a range: [0,255], which in turn maps to the dynamic range of the sonar: [0,80dB].


-------------------------------------------------
## List of TODOs

### `MicronEnsemble` TODOs
- manually set `intensity_len` constant value for all ensemble files. find the max value that can be expected by examining the sonar data file 
- convert `status` and `Hdctrl` to binary and process for status (reject values that are not OK). see some initial code for doing this in the Python notebook. 
  - investigate why status value is 144? (if 144 is int -> 8 bits, if 144 is hex -> requires 9 bits) (call Tritech about this?)
 
### `MicronTimeSeries` TODOs
- add ice detection/classification to the ensemble (perhaps just runs on the most recent swath)
- better plan for object inheritance between the Micron Sonar and the Pathfinder? -- probably an unnecessary effort given how many subtle differences between the two instruments and their data products. That said, trying to use a similar design architecture between the two are useful for readability and usability. 

### `micron_reader` TODOs
- write docstrings for functions 

