#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SDPCHAIN argparse wrapper
"""
from os import mkdir
from pathlib import Path
import argparse
import sys

# from .version import __version__


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, add_infile=False, add_infiles=False, add_outfile=False,
                 add_outfiles=False, force_outfile=False, **kwargs):
        """
        Create argparse instance with -d, -i, -o options already specified

        infile(s) are added without
        outfile is added as --of
        outfiles is added as --ofs
        force_outfile (-F) overwrites the outfile if it exists already

        for in_path, out_path, in_file, in_files, out_file, out_files, returns
        the entered values in attributes with the above names, and the fully
        expanded values in full_{NAME} for each of the above names

        Also validates that the infile(s) exist and that the outfile(s) do not
        """
        assert not (add_infile and add_infiles)
        assert not (add_outfile and add_outfiles)

        super(ArgumentParser, self).__init__(**kwargs)

        if add_infile:
            self.add_argument("infile", help="Input filename")
        elif add_infiles:
            self.add_argument("infiles", help="Input filenames")

        if add_outfile:
            self.add_argument("--of", dest="outfile", required=True,
                              help="Output filename")
        elif add_outfiles:
            self.add_argument("--ofs", dest="outfiles", required=True,
                              help="Output filenames")

        self.add_argument("-d", "--directory", dest="base_dir",
                          default='.', help="Base directory for files")
        self.add_argument("-i", "--input", dest="in_dir", default='.',
                          help="path to input files (abs, or rel to base)")
        self.add_argument("-o", "--output", dest="out_dir", default='.',
                          help="path for output files (abs, or rel to base)")

        if force_outfile:
            self.add_argument("-F", "--force_outfile", action="store_true",
                              help="Force overwrite of output files")

    def parse_args(self, **kwargs):
        """
        Parse arguments, processing in_dir and out_dir relative to base_dir
        
        Also sets up input and output file paths, verifies the existence of
        input files, the non-existence of output files, and copies any
        process-steps.json file in the input directory to the base directory
        (should we also copy to the output directory?)
        """
        args = self.parse_args(**kwargs)
        full_in, full_out = setup_paths(args.base_dir, args.in_dir,
                                        args.out_dir)
        # Save full paths to "full_*"
        args.setattr('full_in_dir', full_in)
        args.setattr('full_out_dir', full_out)
        
        # if there is a process-steps file in the input directory, copy it
        # to the base directory
        if args.in_dir:
            if (Path(full_in_dir) / "process-steps.json").is_file() and
                    not (Path(base_dir) / "process-steps.json").exists():
                shutil.copy2(Path(full_in_dir) / "process-steps.json",
                             Path(args.base_dir) / "process-steps.json")

        # Create full path versions of input files and verify their existence
        if getattr(args, "infile", None) is not None:
            args.setattr("full_infile", Path(full_in) / args.infile)
            if not args.full_infile.is_file():
                print('input file {args.infile} does not exist, quitting')
                sys.exit(2)
        elif getattr(args, "infiles", None) is not None:
            args.setattr("full_infiles",
                         [Path(full_in) / f for f in args.infiles])
            for f in args.full_infiles:
                if not f.is_file():
                    print('input file {f.name} does not exist, quitting')
                    sys.exit(2)

        # Create full path versions of output files and verify non-existence
        if getattr(args, 'force_outfile', False) is True:
            if getattr(args, "outfile", None) is not None:
                args.setattr("full_outfile", Path(full_out) / args.outfile)
                if args.full_outfile.exists():
                    print('output file {args.outfile} exists, quitting')
                    sys.exit(2)
            elif getattr(args, "outfiles", None) is not None:
                args.setattr("full_outfiles",
                             [Path(full_out) / f for f in args.outfiles])
                for of in args.full_outfiles:
                    if of.exists():
                        print('output file {of.name} exists, quitting')
                        sys.exit(2)

        return args


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
    in_path = _choose_path(base_dir, in_dir)
    out_path = _choose_path(base_dir, out_dir)
    assert Path(in_path).is_dir()
    if Path(out_path).exists() is False:
        print(f"out_dir '{out_path}' does not exist, creating...")
        mkdir(out_path)
    elif Path(out_path).is_file():
        print("out_dir '{out_path}' is a file! Will use  base dir")
        out_path = base_dir
    return in_path, out_path


def _choose_path(base_dir, sub_dir):
    """ Sets up absolute path to sub-directory """
    if Path(sub_dir).is_absolute():
        return sub_dir
    return str(Path(base_dir) / sub_dir)
