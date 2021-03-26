#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create/append process-steps.json file
"""
from pathlib import Path
import json


class ProcessSteps():
    """
    Create/append process-steps.json file
    """
    def __init__(self, app_name, app_description, app_version,
                 exec_cmdline, exec_date, exec_return_code,
                 args, exec_tools=[]):
        """
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
        :param base_directory: where to write/append process-steps.json
        :type  base_directory: string
        :return: return code 0
        :rtype:  numeric
        """
        self.app_name = app_name
        self.app_description = app_description
        self.app_version = app_version
        self.exec_cmdline = exec_cmdline
        self.exec_date = exec_date
        self.exec_messages = []
        self.exec_tools = exec_tools
        self.exec_parameters = self._extract_parameters(args)
        self.base_directory = args.base_directory
        self.exec_tools = exec_tools

    def log(self, text):
        """
        Write text to screen and add to exec_messages list
        """
        print(text)
        self.exec_messages.append(text)

    def write(self, return_code):
        """
        Write the process-steps file

        :param return_code: return code of run
        :type  return_code: int
        """
        step = {'application': dict(name=self.app_name,
                                    description=self.app_description,
                                    version=self.app_version),
                'execution': dict(commandline=self.exec_cmdline,
                                  date=self.exec_date,
                                  messages=self.exec_messages,
                                  parameters=self.exec_parameters,
                                  tools=self.exec_tools,
                                  return_code=return_code)}
        # if debug:
        #     print(json.dumps(step, indent=4, separators=(',', ': ')))
        filename = Path(self.base_directory) / 'process-steps.json'
        try:
            fp = open(filename, "r")
        except FileNotFoundError:  # File not found
            tree = {"steps": [step]}
        else:   # File found
            try:
                tree = json.load(fp)
            except Exception:
                newfilename = _unique_path(Path(filename).parents,
                                           'process-steps{:02d}.txt')
                print(f'{filename} exists but unreadable. '
                      f'Writing to {newfilename}')
                filename = newfilename
                tree = {}
            if 'steps' in tree:
                tree['steps'].append(step)
            else:
                tree['steps'] = [step]
            fp.close()
        # if debug:
        #     json.dumps(tree, indent=4, separators=(',', ': '))
        fp = open(filename, "w")
        json.dump(tree, fp, sort_keys=True, indent=2)   # For real
        fp.close


def make_process_steps_file(in_dir: str, out_dir: str,
                            app_name: str, app_description: str,
                            app_version: str, exec_cmdline: str,
                            exec_date: str, exec_return_code: int,
                            exec_messages: list=[], exec_parameters: dict={},
                            exec_tools: list=[], debug: bool=False):
    """
    Make or append to a process-steps.json file

    :param in_dir: directory to read file from
    :type in_dir: str
    :param out_dir: directory to write file to
    :type out_dir: str
    :param app_name: the application name
    :type  app_name: str
    :param app_description: one-line description of the application
    :type  app_description: str
    :param app_version: application versionString
    :type  app_version: str
    :param exec_cmdline: the command line
    :type  exec_cmdline: str
    :param exec_date: start time of program execution
    :type  exec_date: str
    :param exec_return_code: return code of run
    :type  exec_return_code: numeric
    :param exec_messages: messages from execution
    :type  exec_messages: list of strings
    :param exec_parameters: execution parameters
    :type  exec_parameters: dictionary
    :param exec_tools: applications called by the main application
    :type  exec_tools: list of strings
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
    filename = 'process-steps.json'
    in_file = Path(in_dir) / filename
    try:
        fp = open(in_file, "r")
    except FileNotFoundError:  # File not found
        tree = {"steps": [step]}
    else:   # File found
        try:
            tree = json.load(fp)
        except Exception:
            newfilename = _unique_path(Path(out_dir).parents,
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
    fp = open(Path(out_dir) / filename, "w")
    json.dump(tree, fp, sort_keys=True, indent=2)   # For real
    fp.close


def _unique_path(directory, name_pattern):
    counter = 0
    while True:
        counter += 1
        path = directory / name_pattern.format(counter)
        if not path.exists():
            return path
