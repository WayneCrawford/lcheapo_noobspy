#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN compatibility functions
"""
from os import mkdir
from pathlib import Path


def setup_paths(base_dir, in_dir, out_dir):
    """
    Set up paths using SDPCHAIN standards

    :parm base_dir: base directory (for process-steps.json file and as
                    a basis for in_dir and out_dir)
    :param in_dir: directory for input files.  absolute path or relative
                   to base_dir
    :param out_dir: directory for ourput files.  absolute path or relative
                   to base_dir
                 - out_dir directory containing output files
    :return in_dir, out_dir: base_dir-adjusted paths
    """
    # print(f"{base_dir=}, {in_dir=}, {out_dir=}", flush=True)
    in_path = _choose_path(base_dir, in_dir)
    out_path = _choose_path(base_dir, out_dir)
    # print(f"{in_path=}, {out_path=}, {Path(in_path).is_dir()=}", flush=True)
    assert Path(in_path).is_dir() is True
    assert not Path(out_path).is_file()
    if Path(out_path).exists() is False:
        print(f"out_dir '{out_path}' does not exist, creating...")
        Path(out_path).mkdir(parents=True)
    return in_path, out_path


def _choose_path(base_dir, sub_dir):
    """ Sets up absolute path to sub-directory """
    if Path(sub_dir).is_absolute():
        return sub_dir
    return str(Path(base_dir) / sub_dir)
