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
# import os
from datetime import datetime as dt
import sys
from pathlib import Path
import shutil

from .process_steps import ProcessStep
from .setup_paths import setup_paths
from .version import __version__


def sdpcat():
    # GET ARGUMENTS
    args = getOptions()
    process_step = ProcessStep(
        'sdpcat',
        " ".join(sys.argv),
        app_description = __doc__,
        app_version = __version__,
        parameters=args)

    args.in_dir, args.out_dir = setup_paths(args)
    # VERIFY THAT INPUT FILES EXIST AND OUTPUT FILE DOESN'T
    if len(args.input_files) < 2:
        print("You only provided 1 input file: this is just a copy!")
    for file in args.input_files:
        f = Path(args.in_dir) / file
        assert Path(f).is_file()
    assert (Path(args.out_dir) / args.output_file).exists() is False

    with open(Path(args.out_dir) / args.output_file, mode="wb") as destination:
        for file in args.input_files:
            with open(Path(args.in_dir) / file, mode="rb") as source:
                shutil.copyfileobj(source, destination)

    # Save/append process information to process_steps file
    process_step.exit_status = 0
    process_step.write(args.in_dir, args.out_dir)


def getOptions():
    """
    Parse user passed options and parameters.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--of", dest="output_file", required=True, help="Output filename")
    parser.add_argument("--ifs", dest="input_files", required=True, nargs='+',
                        help="Input filenames")
    parser.add_argument("-d", "--directory", dest="base_dir",
                        default='.', help="Base directory for files")
    parser.add_argument("-i", "--input", dest="in_dir", default='.',
                        help="path to input files (absolute, or relative to "
                             "base)")
    parser.add_argument("-o", "--output", dest="out_dir", default='.',
                        help="path for output files (absolute, or relative to "
                             "base)")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    sdpcat()
