v0.1
------

The Original, used for AlpArray deployment cruise

v0.2
------

Slightly modified for MayOBS cruise

v0.3
------

- Changed name to seaplan, split files by task type. 
- Changed input file structure to separate station names from actions.  
- Rewrote algorithm structure to calculate first, then print, then plot
- Added some more options to parameter file

v0.4
------

- Several parameter file changes
- Implemented json schema validator
- Order of columns in CSV file is now directly read from the file
- Some plot things fixed
- Remove obspy dependence
- Make etopo work again