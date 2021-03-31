#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Concatenate files and create/append process-step.json file

Uses python standard library's shutil.copyfileobj()
"""
# from __future__ import (absolute_import, division, print_function,
#                         unicode_literals)
# from future.builtins import *  # NOQA @UnusedWildImport

import argparse
import os
from datetime import datetime as dt
import sys
from pathlib import Path
import shutil

from .process_steps import make_process_steps_file
from .setup_paths import setup_paths
from ..version import __version__


def sdpcat():
    start_time_str = dt.strftime(dt.utcnow(), '%Y-%m-%dT%H:%M:%S')
    return_code = 0
    # exec_messages = []

    # GET ARGUMENTS
    args = getOptions()

    args.in_dir, args.out_dir = setup_paths(args.base_dir,
                                            args.in_dir,
                                            args.out_dir)
    # VERIFY THAT INPUT FILES EXIST AND OUTPUT FILE DOESN'T
    if len(args.ifs) < 2:
        print("You only provided 1 input file: this is just a copy!")
    for file in args.ifs:
        f = Path(args.in_dir) / file
        assert Path(f).is_file()
    assert (Path(args.out_dir) / args.of).exists() is False

    with open(Path(args.out_dir) / args.of, mode="wb") as destination:
        for file in args.ifs:
            with open(Path(args.in_dir) / file, mode="rb") as source:
                shutil.copyfileobj(source, destination)

    # Save/append process information to process_steps file
    make_process_steps_file(
        args.in_dir,
        args.out_dir,
        'sdpcat',
        __doc__,
        __version__,
        " ".join(sys.argv),
        start_time_str,
        return_code,
        exec_parameters={'in_files': args.ifs,
                         'out_files': args.of,
                         'base_dir': args.base_dir,
                         'in_dir': args.in_dir,
                         'out_dir': args.out_dir}
    )


def getOptions():
    """
    Parse user passed options and parameters.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--of", required=True, help="Output filename")
    parser.add_argument("--ifs", required=True, nargs='+',
                        help="Input filenames")
    parser.add_argument("-d", "--directory", dest="base_dir",
                        default='.', help="Base directory for files")
    parser.add_argument("-i", "--input", dest="in_dir", default='.',
                        help="path to input files (absolute, or relative to base)")
    parser.add_argument("-o", "--output", dest="out_dir", default='.',
                        help="path for output files (absolute, or relative to base)")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    sdpcat()
