#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions to test the lcheapo functions
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import os
import unittest
import filecmp
import inspect
import difflib
import json


class TestLCHEAPOMethods(unittest.TestCase):
    """
    Test suite for nordic io operations.
    """
    def setUp(self):
        self.path = os.path.dirname(os.path.abspath(inspect.getfile(
            inspect.currentframe())))
        self.testing_path = os.path.join(self.path, "data")
        self.exec_path = os.path.split(self.path)[0]

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
            step["execution"].pop("date", None)
            step["execution"].pop("commandline", None)
            step["execution"]["parameters"].pop("base_directory", None)
            step["execution"]["parameters"].pop("output_directory", None)
            step["execution"]["parameters"].pop("input_directory", None)
        return tree

    def assertTextFilesEqual(self, first, second, msg=None):
        first_f = open(first)
        first_str = first_f.read()
        second_f = open(second)
        second_str = second_f.read()
        first_f.close()
        second_f.close()

        if first_str != second_str:
            first_lines = first_str.splitlines(True)
            second_lines = second_str.splitlines(True)
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

    def test_dump(self):
        """
        Test lcdump outputs.
        """
        # WRITEOUT OF DATA HEADERS
        cmd = os.path.join(self.exec_path, 'lcdump.py') + ' ' +\
            os.path.join(self.testing_path, 'BUGGY.raw.lch') +\
            ' 5000 100  > temp_test.out'
        os.system(cmd)
        self.assertTextFilesEqual(
            'temp_test.out',
            os.path.join(self.testing_path, 'BUGGY_lcdump_5000_100.txt')
            )
        os.remove('temp_test.out')

        # WRITEOUT OF FILE HEADER

        # WRITEOUT OF DIRECTORY

    def test_fix_buggy(self):
        """
        Test lcfix on a typical (buggy) file
        """
        # Run the code
        cmd = os.path.join(self.exec_path, 'lcfix.py') + \
            ' -d ' + self.path + ' -i data BUGGY.raw.lch > temp'
        os.system(cmd)
        os.remove('temp')
        # print(os.listdir('.'))

        # Check that the appropriate files were created
        assert not os.path.exists('BUGGY.fix.timetears.txt')

        # Compare binary files (fix.lch)
        outfname = 'BUGGY.fix.lch'
        assert os.path.exists(outfname)
        self.assertBinFilesEqual(
            outfname,
            os.path.join(self.testing_path, outfname))
        os.remove(outfname)

        # Compare text files (fix.txt)
        outfname = 'BUGGY.fix.txt'
        assert os.path.exists(outfname)
        self.assertTextFilesEqual(
            outfname,
            os.path.join(self.testing_path, outfname))
        os.remove(outfname)

        # Compare text files (process-steps.json)
        outfname = 'process-steps.json'
        assert os.path.exists(outfname)
        new_outfname = 'BUGGY.' + outfname
        os.rename(outfname, new_outfname)
        self.assertProcessStepsFilesEqual(
            new_outfname,
            os.path.join(self.testing_path, new_outfname))
        os.remove(new_outfname)

    def test_fix_bad(self):
        """
        Test lcfix on a bad (full of time tears) file
        """
        # Run the code
        cmd = os.path.join(self.exec_path, 'lcfix.py') + \
            ' -d ' + self.path + ' -i data BAD.bad.lch > temp'
        os.system(cmd)
        os.remove('temp')

        # Confirm that no lch file was created
        assert not os.path.exists('BAD.fix.lch')

        # Compare text files (fix.txt)
        outfname = 'BAD.fix.txt'
        assert os.path.exists(outfname)
        self.assertTextFilesEqual(
            outfname,
            os.path.join(self.testing_path, outfname))
        os.remove(outfname)

        # Compare text files (fix.timetears.txt)
        outfname = 'BAD.fix.timetears.txt'
        assert os.path.exists(outfname)
        self.assertTextFilesEqual(
            outfname,
            os.path.join(self.testing_path, outfname))
        os.remove(outfname)

        # Compare process-steps files
        outfname = 'process-steps.json'
        assert os.path.exists(outfname)
        new_outfname = 'BAD.' + outfname
        os.rename(outfname, new_outfname)
        self.assertProcessStepsFilesEqual(
            new_outfname,
            os.path.join(self.testing_path, new_outfname))
        os.remove(new_outfname)

    def test_header(self):
        """
        Test lcheader
        """
        # Run the code
        cmd = os.path.join(self.exec_path, 'lcheader.py') +\
            ' --no_questions'
        os.system(cmd)

        outfname = 'generic.header.raw.lch'
        # Check that the appropriate file was created
        assert os.path.exists(outfname)

        # Compare output binary file (fix.lch)
        self.assertBinFilesEqual(
            outfname,
            os.path.join(self.testing_path, outfname))
        os.remove(outfname)


def suite():
    return unittest.makeSuite(TestLCHEAPOMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
