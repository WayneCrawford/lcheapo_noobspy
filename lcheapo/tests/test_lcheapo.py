#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions to test the lcheapo functions
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

from os import system
import unittest
import filecmp
import inspect
import difflib
import json
from pathlib import Path


class TestLCHEAPOMethods(unittest.TestCase):
    """
    Test suite for nordic io operations.
    """
    def setUp(self):
        self.path = Path(inspect.getfile(
            inspect.currentframe())).resolve().parent
        self.testing_path = self.path / "data"

    def assertProcessStepsFilesEqual(self, first, second, msg=None):
        with open(first, "r") as fp:
            first_tree = json.load(fp)
            first_tree = self._remove_changeable_processes(first_tree)
        with open(second, "r") as fp:
            second_tree = json.load(fp)
            second_tree = self._remove_changeable_processes(second_tree)
        assert first_tree == second_tree

    def _remove_changeable_processes(self, tree):
        for step in tree["steps"]:
            step["application"].pop("version", None)
            step["execution"].pop("date", None)
            step["execution"].pop("commandline", None)
            step["execution"]["parameters"].pop("base_directory", None)
            step["execution"]["parameters"].pop("output_directory", None)
            step["execution"]["parameters"].pop("input_directory", None)
        return tree

    def assertTextFilesEqual(self, first, second, msg=None):
        with open(first) as f:
            str_a = f.read()
        with open(second) as f:
            str_b = f.read()

        if str_a != str_b:
            first_lines = str_a.splitlines(True)
            second_lines = str_b.splitlines(True)
            delta = difflib.unified_diff(
                first_lines, second_lines,
                fromfile=first, tofile=second)
            message = ''.join(delta)

            if msg:
                message += " : " + msg

            self.fail("Multi-line strings are unequal:\n" + message)

    def assertBinFilesEqual(self, first, second, msg=None):
        """ Compares two binary files """
        self.assertTrue(filecmp.cmp(first, second))

    def test_lcdump(self):
        """
        Test lcdump outputs.
        """
        # WRITEOUT OF DATA HEADERS
        cmd = f'lcdump {Path(self.testing_path) / "BUGGY.raw.lch"} 5000 100  > temp_test.out'
        system(cmd)
        self.assertTextFilesEqual(
            'temp_test.out',
            Path(self.testing_path) / 'BUGGY_lcdump_5000_100.txt')
        Path('temp_test.out').unlink()

        # WRITEOUT OF FILE HEADER

        # WRITEOUT OF DIRECTORY

    def test_lcfix_buggy(self):
        """
        Test lcfix on a typical (buggy) file
        """
        # Run the code
        cmd = f'lcfix -d {self.path} -i data BUGGY.raw.lch > temp'
        system(cmd)
        Path('temp').unlink()

        # Check that the appropriate files were created
        assert not Path('BUGGY.fix.timetears.txt').exists()

        # Compare binary files (fix.lch)
        outfname = 'BUGGY.fix.lch'
        assert Path(outfname).exists()
        self.assertBinFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare text files (fix.txt)
        outfname = 'BUGGY.fix.txt'
        assert Path(outfname).exists()
        self.assertTextFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare text files (process-steps.json)
        outfname = 'process-steps.json'
        assert Path(outfname).exists()
        new_outfname = 'BUGGY.' + outfname
        Path(outfname).rename(new_outfname)
        self.assertProcessStepsFilesEqual(
            new_outfname,
            Path(self.testing_path) / new_outfname)
        Path(new_outfname).unlink()

    def test_lcfix_bad(self):
        """
        Test lcfix on a bad (full of time tears) file
        """
        # Run the code
        cmd = f'lcfix -d {self.path} -i data BAD.bad.lch > temp'
        system(cmd)
        Path('temp').unlink()

        # Confirm that no lch file was created
        assert not Path('BAD.fix.lch').exists()

        # Compare text files (fix.txt)
        outfname = 'BAD.fix.txt'
        assert Path(outfname).exists()
        self.assertTextFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare text files (fix.timetears.txt)
        outfname = 'BAD.fix.timetears.txt'
        assert Path(outfname).exists()
        self.assertTextFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare process-steps files
        outfname = 'process-steps.json'
        assert Path(outfname).exists()
        new_outfname = 'BAD.' + outfname
        Path(outfname).rename(new_outfname)
        self.assertProcessStepsFilesEqual(
            new_outfname,
            Path(self.testing_path) / new_outfname)
        Path(new_outfname).unlink()

    def test_lccut(self):
        """
        Test lccut
        """
        # Run the code
        cmd = f'lccut -d {self.path} -i data BUGGY.fix.lch --start 5000 --end 5099 > temp'
        system(cmd)
        Path('temp').unlink()
        Path('process-steps.json').unlink()

        # Compare binary files (fix.timetears.txt)
        outfname = 'BUGGY.fix_5000_5099.lch'
        assert Path(outfname).exists()
        self.assertBinFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

    def test_lcinfo(self):
        """
        Test lcinfo
        """
        # Run the code
        cmd = f'lcinfo -d {self.path} -i data BUGGY.fix.lch > temp'
        system(cmd)

        # Compare text files
        self.assertTextFilesEqual(
            'temp',
            Path(self.testing_path) / 'BUGGY.info.txt')
        Path('temp').unlink()

    def test_lcheader(self):
        """
        Test lcheader
        """
        # Run the code without any questions
        cmd = f'lcheader --no_questions'
        system(cmd)

        outfname = 'generic.header.lch'
        # Check that the appropriate file was created
        assert Path(outfname).exists()

        # Compare output binary file (fix.lch)
        self.assertBinFilesEqual(outfname,
                                 Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Run the code with all specified
        cmd = f'lcheader -d MOMARL_SPOBS2_04_LSVEL -s 62.5 -c 4 -w 2019-02-04T04:53:30.024 -e 2019-06-14T04:04:29 -o LSVEL.header.lch > LSVEL.txt'
        system(cmd)
        outfname = 'LSVEL.header.lch'
        assert Path(outfname).exists()
        self.assertBinFilesEqual(outfname,
                                 Path(self.testing_path) / outfname)
        Path(outfname).unlink()
        outfname = 'LSVEL.txt'
        self.assertTextFilesEqual(outfname,
                                  Path(self.testing_path) / outfname)
        Path(outfname).unlink()
        Path('process-steps.json').unlink()


def suite():
    return unittest.makeSuite(TestLCHEAPOMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
