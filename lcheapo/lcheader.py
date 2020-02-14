#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create/modify an LCHEAPO data file header
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import sys
import os
import argparse
from datetime import datetime, timedelta

from .lcheapo import (LCDiskHeader, LCDirEntry)
# from . import sdpchain

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
version = {}
with open(os.path.join(os.path.dirname(__file__), "version.py")) as fp:
    exec(fp.read(), version)

PROGRAM_NAME = "lcheader"
bytes_per_block = 512
dirs_per_block = 16
blocks_per_dirEntry = 14336
samples_per_block = 166


def main():
    """main function"""
    opts = __getOptions()

    if opts.input_file:
        h = __read_header(opts.input_file)
    else:
        h = __generic_header()
    h, params = __get_parameters(h, opts.no_questions)
    if opts.dry_run:
        sys.exit(2)
    with open(params['filename_prefix']+'.header.raw.lch', 'wb') as fp:
        # Pre-blank file
        if opts.noDirectory:
            fp.write(b'\x00' * bytes_per_block * h.dirStart)
        else:
            fp.write(b'\x00' * bytes_per_block * h.dataStart)

        # Write header
        h.seekHeaderPosition(fp)
        h.writeHeader(fp)
        if opts.noDirectory:
            sys.exit(0)

        # Write directory
        d = __prep_dirEntry(h.sampleRate)
        dt = params['wake_time']
        dirCount = 0
        samples_per_dirEntry = samples_per_block * blocks_per_dirEntry / \
            h.numberOfChannels
        dir_timeoffset = timedelta(seconds=samples_per_dirEntry / h.sampleRate)
        blocknum = h.dataStart
        d.seekBlock(fp, h.dirStart)
        while dt < params['end_time']:
            d = __make_dirEntry(d, blocknum, dt)
            d.writeDirEntry(fp)
            dt += dir_timeoffset
            dirCount += 1
            blocknum += blocks_per_dirEntry
        h.dirCount = dirCount
        h.seekHeaderPosition(fp)
        h.writeHeader(fp)
    # process_step.write()
    sys.exit(0)


def __getOptions():
    """
    Parse user passed options and parameters
    """
    # usageStr = "%prog [-h] [-V]"
    parser = argparse.ArgumentParser(
        description="Create/modify an LCHEAPO data file header",
        )
    parser.add_argument("-V", "--version", default=False, action="store_true",
                        help="Display Program Version")
    parser.add_argument("-n", "--noDirectory", default=False,
                        action="store_true", help="Print disk header")
    parser.add_argument("--dry_run", default=False, action="store_true",
                        help="don't save to disk")
    parser.add_argument("--no_questions", default=False, action="store_true",
                        help="make a generic header, no questions", )
    parser.add_argument("-i", "--input_file",
                        help="input header file to modify")
    args = parser.parse_args()

    # Get the filename (the arguments)
    if args.version:
        print("{} - Version: {}".format(PROGRAM_NAME, version['__version__']))
        sys.exit(0)
    return args


def __get_parameters(h, no_questions=False):
    """Imitate LCHEAPO parameter menu, return values"""
    params = dict(wake_time=datetime(2017, 1, 1, 5, 0, 0),
                  end_time=datetime(2018, 1, 1, 5, 0, 0),
                  filename_prefix="generic")
    while not __validate_params(h, params, no_questions):
        h.description = __get_string("Description (Cruise_InstModel_SN_Site)",
                                     h.description)
        h.sampleRate = __get_int("Sample Rate",
                                 h.sampleRate,
                                 [31, 62, 125, 250, 500, 1000, 2000, 4000])
        h.realSampleRate = h.getRealSampleRate(h.sampleRate)
        h.numberOfChannels = __get_int("Number of Channels",
                                       h.numberOfChannels,
                                       [1, 2, 3, 4])

        params['wake_time'] = __get_datetime("Wake Time", params['wake_time'])
        if params['end_time'] < params['wake_time']:
            params['end_time'] = params['wake_time'] + timedelta(days=365)
        params['end_time'] = __get_datetime("End Time", params['end_time'])
        params['filename_prefix'] = __get_string("Output Filename Prefix",
                                                 params['filename_prefix'])

    datalen = params['end_time'] - params['wake_time']
    datalen_seconds = datalen.days * 86400 + datalen.seconds + \
        datalen.microseconds / 1.e6
    datalen_blocks = int(datalen_seconds * h.sampleRate / samples_per_block) *\
        h.numberOfChannels
    h.writeBlock = h.dataStart + datalen_blocks
    return h, params


def __validate_params(h, params, no_questions):
    """Validate header parameters"""
    if no_questions:
        return True

    print('**** PARAMETERS ****')
    print('         Description: {}'.format(h.description))
    print('         Sample Rate: {:d} ({:.1f} real)'.format(h.sampleRate,
                                                            h.realSampleRate))
    print('  Number of Channels: {}'.format(h.numberOfChannels))
    print('           Wake Time: {}'.format(params['wake_time'].isoformat()))
    print('            End Time: {}'.format(params['end_time'].isoformat()))
    print('     Output Filename: {}'.format(params['filename_prefix'] +
                                            '.header.raw.lch'))
    resp = input('Is this acceptable? [y/N]: ')
    if not resp:
        return False
    if resp[0].lower() == 'y':
        return True
    return False


def __read_header(filename):
    """Read in header from an LCHEAPO file"""
    h = LCDiskHeader()
    with open(filename, 'r') as fp:
        h.seekHeaderPosition(fp)
        h.readHeader(fp)
    return h


def __generic_header():
    """Create a generic lcheapo header"""

    default_data_startblock = 3586
    default_dir_startblock = 8
    default_data_type = 2
    default_data_type_string = "Uncompressed (24-Bit)"

    h = LCDiskHeader()

    # UNUSED OR STANDARD VALUES
    h.dataType = default_data_type
    h.diskSize = 0    # GB
    h.ramSize = 8     # MB
    h.softwareVersion = '9.08a-OLD'
    h.dirStart = default_dir_startblock
    h.dataStart = default_data_startblock
    # h.dirSize=(h.dataStart-h.dirStart-1)*dirs_per_block
    # Modified to work with lc2ms v1
    h.dirSize = (h.dataStart - h.dirStart) * dirs_per_block - 1
    (h.slowStart, h.slowSize, h.slowBlock, h.slowByte) = (0, 0, 0, 0)
    (h.logStart, h.logSize, h.logBlock, h.logByte) = (0, 0, 0, 0)
    (h.slowDataRate, h.slowStartChannel, h.slowNumberOfChannels) = (0, 0, 0)
    (h.readBlock, h.startChannel, h.diskNumber) = (0, 0, 0)
    (h.numberOfWindows, h.readByte, h.writeByte) = (0, 0, 0)

    # These should be modified after writing directory
    h.dirBlock, h.dirCount = (0, 0)

    # USER-SPECIFIED VALUES
    h.description = 'generic lcheapo header'
    h.sampleRate = 125
    h.numberOfChannels = 4
    h.writeBlock = h.dataStart

    # Additions which cannot be written to file
    h.realSampleRate = h.getRealSampleRate(h.sampleRate)
    h.dataTypeString = default_data_type_string
    return h


def __prep_dirEntry(sample_rate):
    """Prepare lcheapo directory entry object"""
    d = LCDirEntry()
    d.recordLength = 0  # Unused
    d.sampleRate = sample_rate
    d.numBlocks = blocks_per_dirEntry
    d.flag = 0x49
    d.muxChannel = 0
    d.U1 = 0            # Unused
    return d


def __make_dirEntry(d, blocknum, dt):
    """Put time in lcheapo directory entry"""
    d.blockNumber = blocknum
    d.changeTime(dt)
    return d


def __get_string(question, default):
    """Read a string from the command line"""
    resp = input("{} [{}]: ".format(question, default))
    if not resp:
        return default
    return resp


def __get_datetime(question, default):
    """Read a datetime from the command line"""
    resp = input("{} [{}]: ".format(question, default.isoformat()))
    if not resp:
        return default
    else:
        try:
            resp = datetime.strptime(resp, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                resp = datetime.strptime(resp, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                print('Invalid input: {}'.format(resp))
                resp = __get_datetime(question, default)
    return resp


def __get_int(question, default, possibles=False):
    """Read an int from the command line"""
    resp = input("{} [{:d}]: ".format(question, default))
    if not resp:
        return default
    else:
        try:
            resp = int(resp)
        except ValueError:
            print('Invalid input: {}'.format(resp))
            resp = __get_int(question, default, possibles)
        if isinstance(possibles, list):
            if resp not in possibles:
                print('Input must be one of: {}'.format(str(possibles)))
                resp = __get_int(question, default, possibles)
    return resp


def __get_float(question, default, possibles=False):
    """Read a float from the command line"""
    resp = input("{} [{:d}]: ".format(question, default))
    if not resp:
        return default
    else:
        try:
            resp = float(resp)
        except ValueError:
            print('Invalid input: {}'.format(resp))
            resp = __get_float(question, default, possibles)
        if isinstance(possibles, list):
            if resp not in possibles:
                print('Input must be one of: {:d}'.format(possibles))
                resp = __get_float(question, default, possibles)
    return resp


# ---------------------------------------------------------------------------
# Run 'main' if the script is not imported as a module
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    main()
