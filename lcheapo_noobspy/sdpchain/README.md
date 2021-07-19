SDPCHAIN
===========

Seismology Data Preparation Module

Routines and classes providing a consistent interface for Python programs using
the SDPCHAIN protocol, which includes:

- Create or append to a process-steps.json file at each step
    - the process-steps file is read from the input directory and written
      to the output directory.  If both directories are the same the new step
      is appended to the existing file
- command-line arguments:
    - -d (base_dir)
    - -i (in_dir), can be relative to base directory
    - -o (out_dir), can be relative to base directory
    - optional (input_file) or (input_files), will have input directory pre-pended
    - optional -of (output_file) or -ofs (output_files), will have output dir pre-pended
    - optional -f, forces writing of output file if it already exists

- For now, these parameters must have exactly the above names in the files that
  use SDPCHAIN, so that setup_paths and ProcessStep process them correctly.
  The new ArgParser subclass should eliminate this need, but pre-populating
  the argparser with base_dir, in_dir and out_dir, as well as optionally 
  input_file or input_files, output_file or output_files, and/or -f
  
Classes
---------------------

`ProcessSteps` object to hold information for a process-steps file

Command-line Routines
---------------------

These routines perform common functions while following the
SDPCHAIN rules (process-steps file, -i, -o, -d)

`sdpstep`: run a standard command-line program 

`sdpcat`: concatenate binary files

ToDo
----
Add `sdpcode`: change net and station codes?