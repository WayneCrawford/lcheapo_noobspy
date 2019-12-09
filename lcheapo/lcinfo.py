#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Return basic information about LCHEAPO files

By default, returns number of channels, samp_rate and start and end of each file
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
        'lcinfo',
        'Return basic information about LCHEAPO files',
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


def getTimeDelta(seconds=0.):
    """
    Convert seconds to a timedelta() object

    :param seconds: the number of seconds
    :type  seconds: float
    :return: timedelta
    :rtype:  class datetime.timedelta
    """
    days = int(seconds / 86400)
    seconds -= days * 86400
    hours = int(seconds / 3600)
    seconds -= hours * 3600
    minutes = int(seconds/60)
    seconds -= minutes * 60
    int_secs = int(seconds)
    seconds -= int_secs
    msec = int(seconds * 1000)
    return datetime.timedelta(days=days, hours=hours, minutes=minutes,
                              seconds=seconds, milliseconds=msec)


def _to_msec(tm):
    """
    Return the number of milliseconds corresponding to a timedelta object

    :param tm: timedelta
    :type  tm: class datetime.timedelta
    :return: milliseconds
    :rtype: int
    """
    return 1000 * ((tm.days * 86400) + tm.seconds) + \
        int(tm.microseconds / 1000.)


if __name__ == '__main__':
    main()
