#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN compatibility functions
"""
from pathlib import Path
import json


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
    :param app_version: application versionString
    :type  app_version: string
    :param exec_cmdline: the command line
    :type  exec_cmdline: string
    :param exec_date: start time of program execution
    :type  exec_date: string
    :param exec_messages: messages from execution
    :type  exec_messages: list of strings
    :param exec_parameters: execution parameters
    :type  exec_parameters: dictionary
    :param exec_tools: applications called by the main application
    :type  exec_tools: list of strings
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
    filename = Path(base_directory) / 'process-steps.json'
    try:
        fp = open(filename, "r")
    except FileNotFoundError:  # File not found
        tree = {"steps": [step]}
    else:   # File found
        try:
            tree = json.load(fp)
        except Exception:
            newfilename = unique_path(Path(filename).parents,
                                      'process-steps{:02d}.txt')
            print('{filename} exists but unreadable. Writing to {newfilename}')
            filename = newfilename
            tree = {}
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
    
    def unique_path(directory, name_pattern):
        counter = 0
        while True:
            counter += 1
            path = directory / name_pattern.format(counter)
            if not path.exists():
                return path

