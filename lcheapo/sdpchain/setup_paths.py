#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN compatibility functions
"""
import os


def setup_paths(args):
    """
    Set up paths using SDPCHAIN standards

    :parm args: argparse namespace with the following fields
                 - base_dir: base directory
                 - infiles: list of input files
                 - in_dir: directory containing input files
                 - out_dir directory containing output files
                infiles is a list, the rest are strings
                the process-steps file will be opened or appended in base_dir
                in_dir and out_dir are absolute paths, or relative to base_dir
    :return in_path, out_path: path for input and output files
    :rtype: tuple
    """
    in_filename_path = _choose_path(args.base_directory, args.input_directory)
    out_filename_path = _choose_path(args.base_directory,
                                     args.output_directory)
    if not os.path.exists(out_filename_path):
        print("output directory '{}' does not exist, creating...".format(
            out_filename_path))
        os.mkdir(out_filename_path)
    elif not os.path.isdir(out_filename_path):
        print("output directory '{}' is a file!, changing to base dir".format(
            out_filename_path))
        out_filename_path = args.base_directory
    return in_filename_path, out_filename_path


def _choose_path(base_dir, sub_dir):
    """ Sets up absolute path to sub-directory """
    if os.path.isabs(sub_dir):
        return sub_dir
    return os.path.join(base_dir, sub_dir)
