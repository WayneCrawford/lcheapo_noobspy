"""
Seismology Data Preparation Module

Routines and classes providing a consistent interface for Python programs using
the SDPCHAIN protocol, which includes:

- Create or append to a process-steps.json file at each step
    - the process-steps file is read from the input directory and written
      to the output directory.  If both directories are the same the new step
      is appended to the existing file
- command-line arguments:
    - -d (base directory)
    - -i (onput directory), can be relative to base directory
    - -o (output directory), can be relative to base directory
    - optional (input_file) or (input_files), will have input directory pre-pended
    - optional -of (output_file) or -ofs (output_files), will have output dir pre-pended
    - optional -f, forces writing of output file if it already exists
  
Classes
---------------------

:ProcessSteps: Holds process-step information and saves/appends to file

NOT YET VERIFIED
:ArgParser: argparse:argparser instance prefilled with the SDPCHAIN command-
            line arguments.  Once parsed, the optional infile, infiles, outfile
            and outfiles attributes are adusted for their relation to the
            base and input/output directories and any process-steps.json file
            in the input directory is copied to the base directory (quits
            if there is already one there)

Command-line Routines
---------------------

These routines perform common functions while following the
SDPCHAIN rules (process-steps file, -i, -o, -d)
:sdpstep: run a standard command-line program 
:sdpcat: concatenate binary files
"""
from .setup_paths import setup_paths
from .process_steps import ProcessStep
from .sdpcat import sdpcat
from .sdpstep import main as sdpstep, is_tool
from ..version import __version__
name = "sdpchain"
