#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cut an LCHEAPO file into pieces

Used to remove bad/empty blocks
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import sdpchain
from lcheapo import (LCDataBlock, LCDiskHeader, LCDirEntry)
import argparse
import queue
import os
import textwrap
import copy         # for deepcopy of argparse dictionary
import logging      # for logging information
import datetime
import sys

def main():

    global warnings
    # Prepare variables

    # GET ARGUMENTS
    args = getOptions()
    
    for filename in args.infiles:
        with fp.open(filename) as fp:
            _print_Info(fp)
    sdpchain.make_process_steps_file(
        'lccut',
        'Cut an LCHEAPO file into pieces',
        versionString,
        " ".join(sys.argv),
        startTimeStr,
        returnCode,
        args.base_directory,
        exec_messages=msgs,
        exec_parameters=parameters)


def getOptions():
    """
    Parse user passed options and parameters.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("infiles", metavar="inFileName", nargs='+',
                        help="Input filename(s)")
    args = parser.parse_args()
    return args






if __name__ == '__main__':
    main()
