SDPCHAIN
===========

Seismology Data Preparation Module

Routines and classes providing a consistent interface for Python programs using
the SDPCHAIN protocol, which includes:

- Creation or appending to a process-steps.json file at each step
- command-line arguments -d (base directory) -i (onput directory) and -o
  (output directory), plus optional arguments (infile) or (infiles), -of
  (outfile) or -ofs (outfiles), -f (force output file)
  
if the input directory has a process-steps file, it is copied to the base
directory and appended to.

Classes
---------------------

:ProcessSteps: object to hold information for a process-steps file
:ArgParser: argparse:argparser instance prefilled with the SDPCHAIN command-
            line arguments.  Once parsed, the optional infile, infiles, outfile
            and outfiles attributes are adusted for their relation to the
            base and input/output directories and any process-steps.json file
            in the input directory is copied to the base directory (quits
            if there is already one there)

Command-line Routines
---------------------

These routines allow one to perform common functions while following the
SDPCHAIN rules (process-steps file, -i, -o, -d)
:sdp-process: run a standard command-line program 
:sdpcat: concatenate binary files