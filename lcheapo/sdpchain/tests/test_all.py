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


class TestMethods(unittest.TestCase):
    """
    Test suite for sdpchain operations.
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

    def test_sdpcat(self):
        """
        Test sdpcat on two files
        """
        # Run the code
        system('sdpcat --ifs test.header.lch test.nimportequoi '
               '--of test.out -i data')

        # Compare binary files (test.out)
        outfname = 'test.out'
        assert Path(outfname).exists()
        self.assertBinFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare text files (process-steps.json)
        outfname = 'process-steps.json'
        assert Path(outfname).exists()
        self.assertProcessStepsFilesEqual(
            outfname,
            Path(self.testing_path) / 'process-steps_sdpcat.json')
        Path(outfname).unlink()


def suite():
    return unittest.makeSuite(TestMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
