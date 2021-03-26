#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cut an LCHEAPO file into pieces

Used to remove bad/empty blocks, blocks start with 0 and are 512-bytes
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import argparse
# import os
from datetime import datetime as dt
import sys
from math import floor
from pathlib import Path

from . import sdpchain
from .version import __version__
# from .lcheapo import (LCDataBlock, LCDiskHeader, LCDirEntry)

BLOCK_SIZE = 512
MAX_BLOCK_READ = 2048   # max number of blocks to read at once


def main():
    start_time_str = dt.strftime(dt.utcnow(), '%Y-%m-%dT%H:%M:%S')
    return_code = 0
    exec_messages = []

    # GET ARGUMENTS
    args = getOptions()

    # Verify output filename
    if not args.out_fname:
        # Create output filename
        base = Path(args.in_fname).stem
        ext = Path(args.in_fname).suffix
        args.out_fname = f'{base}_{args.start:d}_{args.end:d}{ext}'
    out_path = Path(args.out_dir) / args.out_fname
    if out_path.exists():
        print('output file {out_path} exists already, quitting...')
        sys.exit(2)

    with open(Path(args.in_dir) / args.in_fname, 'rb') as fp:
        # Set/validate last block to read
        fp.seek(0, 2)   # End of file
        last_file_block = floor(fp.tell()/BLOCK_SIZE)-1
        if args.end:
            if args.end > last_file_block:
                args.end = last_file_block
        else:
            args.end = last_file_block
        # Quit if start block is after EOF and/or end block
        if args.start > last_file_block:
            return_code = 2
            msg = 'Error: --start block [{:d}] is beyond EOF [{:d}]'.format(
                args.start, last_file_block)
            print(msg)
            exec_messages.append(msg)
        elif args.start > args.end:
            return_code = 3
            msg = 'Error: --start block [{:d}] is beyond --end [{:d}]'.format(
                args.start, args.end)
            print(msg)
            exec_messages.append(msg)
        else:
            msg = 'Writing blocks {:d}-{:d} to {}'.format(
                args.start, args.end, args.out_fname)
            print(msg)
            exec_messages.append(msg)
            with open(out_path, 'wb') as of:
                start_block = args.start
                fp.seek(start_block * BLOCK_SIZE, 0)
                while start_block <= args.end:
                    if (args.end-start_block+1) < MAX_BLOCK_READ:  # NEAR EOF
                        of.write(fp.read((args.end
                                          - start_block
                                          + 1) * BLOCK_SIZE))
                        break
                    else:
                        of.write(fp.read(MAX_BLOCK_READ * BLOCK_SIZE))
                        start_block += MAX_BLOCK_READ
    # Save/append process information to process_steps file
    sdpchain.make_process_steps_file(
        args.in_dir,
        args.out_dir,
        'lccut',
        __doc__,
        __version__,
        " ".join(sys.argv),
        start_time_str,
        return_code,
        exec_messages=exec_messages,
        exec_parameters='')


def getOptions():
    """
    Parse user passed options and parameters.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("in_fname", help="Input filename")
    parser.add_argument("--of", dest="out_fname", default="",
                        help="""
                        Output filename.  If not provided, writes to
                        {root}_{start}_{end}.{ext}, where {ext} is the last
                        pathname component of {in_file_name} and {root} is
                        the rest""")
    parser.add_argument("--start", type=int, default=0,
                        help="start block to write out (0 if not specified)")
    parser.add_argument("--end", type=int, default=0,
                        help=""" last block to write out (end of file if not
                        specified)""")
    parser.add_argument("-d", "--directory", dest="base_dir",
                        default='.', help="Base directory for files")
    parser.add_argument("-i", "--input", dest="in_dir", default='.',
                        help="path to input files (abs, or rel to base)")
    parser.add_argument("-o", "--output", dest="out_dir", default='.',
                        help="path for output files (abs, or rel to base)")
    args = parser.parse_args()

    args.in_dir, args.out_dir = sdpchain.setup_paths(args.base_dir,
                                                     args.in_dir,
                                                     args.out_dir)
    return args


if __name__ == '__main__':
    main()
