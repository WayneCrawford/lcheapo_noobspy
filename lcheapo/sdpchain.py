#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN compatibility functions
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport


import os
import json
# import copy         # for deepcopy of argparse dictionary


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


def make_process_steps_file(app_name, app_description, app_version,
                            exec_cmdline, exec_date, exec_return_code,
                            base_directory,
                            exec_messages=[], exec_parameters={},
                            exec_tools=[], debug=False):
    """
    Make or append to a process-steps.json file

    :param app_name: the application name
    :type  app_name: string
    :param app_description: one-line description of the application
    :type  app_description: string
    :param app_version: applicatino versionString
    :type  app_version: string
    :param exec_cmdline: the command line
    :type  exec_cmdline: string
    :param exec_date: start time of program execution
    :type  exec_date: string
    :param exec_tools: applications called by the main application
    :type  exec_tools: list of strings
    :param exec_parameters: execution parameters
    :type  exec_parameters: dictionary
    :param exec_messages: messages from execution
    :type  exec_messages: list of strings
    :param exec_return_code: return code of run
    :type  exec_return_code: numeric
    :param base_directory: where to write/append process-steps.json
    :type  base_directory: string
    :return: return code 0
    :rtype:  numeric
    """

    application = dict(name=app_name,
                       description=app_description,
                       version=app_version)
    execution = dict(commandline=exec_cmdline,
                     date=exec_date,
                     messages=exec_messages,
                     parameters=exec_parameters,
                     tools=exec_tools,
                     return_code=exec_return_code)

    step = {'application': application, 'execution': execution}
    if debug:
        print(json.dumps(step, indent=4, separators=(',', ': ')))
    filename = os.path.join(base_directory, 'process-steps.json')
    try:
        fp = open(filename, "r")
    except FileNotFoundError:  # File not found
        tree = {"steps": [step]}
    else:   # File found
        tree = json.load(fp)
        if 'steps' in tree:
            tree['steps'].append(step)
        else:
            tree['steps'] = [step]
        fp.close()
    if debug:
        json.dumps(tree, indent=4, separators=(',', ': '))   # For testing
    fp = open(filename, "w")
    json.dump(tree, fp, sort_keys=True, indent=2)   # For real
    fp.close
