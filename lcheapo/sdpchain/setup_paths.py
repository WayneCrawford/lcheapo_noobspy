#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN compatibility functions
"""
from pathlib import Path


def setup_paths(args, verbose=True):
    """
    Set up paths using SDPCHAIN standards

    param args: a NameSpace object (usually created by argparser) with the
                attributes base_dir, in_dir and out_dir
    :return in_dir, out_dir: base_dir-adjusted paths
    
    The rules are:
        - base_dir is the root for in_dir and out_dir)
        - in_dir is the directory for input files.  An absolute path or relative
                   to base_dir
        - out_dir is the directory to output to.
        - in_dir and out_dir are absolute paths or relative to base_dir
    """
    if not hasattr(args, "base_dir"):
        raise NameError('args has no base_dir attribute')
    if not hasattr(args, "in_dir"):
        raise NameError('args has no in_dir attribute')
    if not hasattr(args, "out_dir"):
        raise NameError('args has no out_dir attribute')
    in_path = _choose_path(args.base_dir, args.in_dir)
    out_path = _choose_path(args.base_dir, args.out_dir)
    # print(f"{in_path=}, {out_path=}, {Path(in_path).is_dir()=}", flush=True)
    assert Path(in_path).is_dir() is True
    assert not Path(out_path).is_file()
    if Path(out_path).exists() is False:
        if verbose:
            print(f"out_dir '{out_path}' does not exist, creating...")
        Path(out_path).mkdir(parents=True)
    return in_path, out_path


def _choose_path(base_dir, sub_dir):
    """ Sets up absolute path to sub-directory """
    if Path(sub_dir).is_absolute():
        return sub_dir
    return str(Path(base_dir) / sub_dir)
