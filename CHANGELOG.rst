VERSIONS (changes are to lcfix unless otherwise noted)
 0.2:
  - Handles spliced datafiles with zero-filled gaps:
    + Adds dates to headers in gap
    + Verifies that gap is the right size
      (no time tear afterwards)
  - Handles incomplete datafiles
    + Warns the user that the data do not go as far as the
      directory claims
    + Changes the "directoryEntries" value in the header
0.3:
  - Output starts with block #
  - Output is streamlined for zero- filled gaps
  - Confirm channel #: consecutive and < 4)
  - Changed block# reported to conform to lcdump.py (tell()/512-1)
  - Expanded BUG2 to handle 2 consecutive bad times/channel
    (called BUG #2b)
  - Time tears (MUST BE FIXED) are saved to timeTears.txt
  - Bug #1s repeating every 500 blocks are identified as Bug #3
    (can reduce the text output by a lot!)
0.4:
  - Expanded BUG #2 to handle up to 3 consecutive bad times/channel
    (BUG #2c)
0.45:
  - Add --dryrun option (don't output fixed LCHEAPO file)
  - Add check of non-time header values
0.46:
  - By default, program names output file
0.5:
  - Creates a JSON file with execution information
  - Handles multiple lcheapo input files (should be different fragments of
    same station, still only write one JSON file)
0.51:
  - Names the JSON file based on the input filename (each input file
    gets its own JSON)
  - Add -F (forceTimes) option: to force time tags to be consecutive (only
    use if all time tears are proven wrong)
0.52:
  - The JSON file is ALWAYS named process-steps.json
  - If there is already a process-steps.json, new information is appended
0.6:
  - If multiple files specified, assume all are sections of same instrument
    file, add header from first file to all others, output names include
    timestamp of start of data
  - If there is already a process-steps.json, new information is appended
0.61:
  - Corrected process-steps.json to have steps as list, not dictionary
0.62:
  - Fixed bug with "warnings" variable
0.63:
  - Fixed bug making last directory entry for originally headerless files
0.64:
  - Updated process-steps.json file to match process-steps.schema.json
0.65:
  - Shifts to "force time stamp" for last 3 samples: avoids reading
    beyond EOF
0.66:
  - Added '-d', '-i' and '-o' options to match SDPCHAIN programs
0.67:
  - Recognize '*.header.*' files as header+directory, without data
  - DOESN"T WORK CORRECTLY!! CAT HEADER TO FIRST DATA!!!!

v0.70
------

Last version that only works on Python 2.7
- First version using unittest
- Added sdpchain.py (for process-steps.json files)

v0.71
------

Converted to Python 3.6
- Numerous flake8 fixes
- lcdump argparser replaces optparser

v0.72
-------

Repairs bug in old software version (8.07J) used on 2-channel SPOBSs (SPOBS1) in which the directory
length was marked as 16386 blocks when it is actually 14336

  - 0.72.5: fixed error where a file named {SOMETHING}.fix.lch would be
    overwritten
  - 0.72.6: made lcfix counters a class.  Fixed a crash when
    muxChannel == numChannels (1 more than is possible).  Removed
    handling of zero-filled blocks (gives error now)
  - 0.72.7: lcheader now creates a process-steps.json file