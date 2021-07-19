#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create/append process-steps.json file
"""
from pathlib import Path
from dataclasses import dataclass, field
import json
import argparse
import copy
from datetime import datetime as dt


@dataclass
class ProcessStep:
    """
    Create an SDPChain process step
    
    Arguments:
        app_name (str): the application name
        cmdline (str): the full command line
        
    Attributes:
        date(datetime.datetime): datetime at which the command was called
        exit_status (int): command exit status
        app_description (str)
        app_version (str)
        parameters (dict or argparse.NameSpace): execution parameters
        messages (list of str): execution messages
        tools (list of str): tools used by the application
        output_files (list of str): files output by the program (and not
            in parameters)
        output_file (str): file output during execution (and not in parameters)
    """
    app_name: str
    cmdline: str
    date: dt = dt.utcnow()
    exit_status: int = None
    app_description: str = 'No description found'
    app_version: str = "Unknown"
    parameters: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    output_files: list = field(default_factory=list)
    output_file: str = ''

    def __post_init__(self):
        # If parameters provided by argparser
        if isinstance(self.parameters, argparse.Namespace):
            self.parameters = copy.deepcopy(vars(self.parameters))

    def log(self, text, write_to_screen=False):
        """
        add text to messages list
        """
        if write_to_screen:
            print(text)
        self.messages.append(text)

    def write(self, in_dir, out_dir, filename='process-steps.json', quiet=False):
        """
        Write the Process Step to a process-steps file

        :param in_dir: directory containing input process-steps file
        :param out_dir: directory in which to create out process-steps file
        """
        self._modify_parameters()
        step = {'application': dict(name=self.app_name,
                                    description=self.app_description,
                                    version=self.app_version),
                'execution': dict(command_line=self.cmdline,
                                  date=self.date.strftime('%Y-%m-%dT%H:%M:%S'),
                                  messages=self.messages,
                                  parameters=self.parameters,
                                  tools=self.tools,
                                  exit_status=self.exit_status)
        }
 
        # READ FILE FROM INPUT DIRECTORY
        in_file = Path(in_dir) / filename
        out_file = Path(out_dir) / filename
        tree = {}
        try:
            fp = open(in_file, "r")
        except FileNotFoundError:  # File not found
            pass
        else:   # File found
            try:
                tree = json.load(fp)
            except Exception:
                # Couldn't read input file, don't overwrite it either
                if in_file == out_file:
                    out_file = _unique_path(Path(out_dir),
                                                'process-steps{:02d}.json')
                if not quiet:
                    print('{} is unreadable. {} will lack previous steps'
                          .format(in_file, out_file))
            fp.close()
        if 'steps' in tree:
            tree['steps'].append(step)
        else:
            tree['steps'] = [step]
        # WRITE FILE TO OUTPUT DIRECTORY
        if out_file.exists():
            out_file = _unique_path(Path(out_dir),
                                    'process-steps{:02d}.json')
        with open(out_file, "w") as fp:
            json.dump(tree, fp, sort_keys=True, indent=4)

    def _modify_parameters(self):
        """
        Modify execution parameters to conform to schema
        
        puts parameters['in_dir', 'out_dir', base_dir] in 
        parameters['directory_paths']{['input'], ['output'], 'base'}
        
        puts output_files in parameters['output_files']
        puts output_file in parameters['output_file']
        """
        
        ep = self.parameters   # make a shortcut
        # base_dir, in_dir and out_dir all go into directory_paths
        if 'base_dir' in ep or 'in_dir' in ep or 'out_dir' in ep:
            ep['directory_paths'] = {}
            dp = ep['directory_paths']
            if 'base_dir' in ep:
                dp['base'] = ep['base_dir']
                del ep['base_dir']
            if 'in_dir' in ep:
                dp['input'] = ep['in_dir']
                del ep['in_dir']
            if 'out_dir' in ep:
                dp['output'] = ep['out_dir']
                del ep['out_dir']
        
        # output_files go into parameters['output_files']
        if self.output_files:
            if 'output_files' in ep:
                ep['output_files'] = ep['output_files'].extend(self.output_files)
            else:
                ep['output_files'] = self.output_files
        if self.output_file:
            if 'output_file' in ep:
                ep['output_files'] = [ep['output_file'], self.output_file]
                del ep['output_file']
            else:
                ep['output_file'] = self.output_file

def _unique_path(directory, name_pattern):
    counter = 0
    while True:
        counter += 1
        path = directory / name_pattern.format(counter)
        if not path.exists():
            return path
