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
import subprocess
from datetime import datetime
from argparse import Namespace

import lcheapo.sdpchain as sdpchain


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
        self.maxDiff=None
        self.assertDictEqual(first_tree, second_tree)
        # assert first_tree == second_tree

    def _remove_changeable_processes(self, tree):
        for step in tree["steps"]:
            step["application"].pop("version", None)
            step["execution"].pop("date", None)
            step["execution"].pop("command_line", None)
            step["execution"]["parameters"].pop("base_dir", None)
            step["execution"]["parameters"].pop("out_dir", None)
            step["execution"]["parameters"].pop("in_dir", None)
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

    def test_process_steps(self):
        """
        Test ProcessSteps class
        """
        pc = sdpchain.ProcessStep(
            'my_app',
            'my_app -a hehe -b hoho',
            datetime(2019, 6, 5, 12, 52, 56),
            exit_status=0,
            app_description="crappy app",
            app_version="0.0",
            parameters = dict(a='hehe', b='hoho'),
            messages = ['That hurts!', 'Stop!'])
        pc.log('ouch!')
        pc.write('.', '.', filename='process-steps_test.json')
        self.assertProcessStepsFilesEqual(
            'process-steps_test.json',
            Path(self.testing_path) / 'process-steps_test.json')
        Path('process-steps_test.json').unlink()

    def test_process_steps_empty(self):
        """
        Verify that an empty process_steps file doesn't kill the rest
        """
        pc = sdpchain.ProcessStep(
            'my_app',
            'my_app -a hehe -b hoho',
            datetime(2019, 6, 5, 12, 52, 56),
            exit_status=0,
            app_description="crappy app",
            app_version="0.0",
            parameters = dict(a='hehe', b='hoho'),
            messages = ['That hurts!', 'Stop!'])
        pc.log('ouch!')
        filename = 'process-steps_empty.json'
        pc.write(self.testing_path, '.', filename=filename, quiet=True)
        self.assertProcessStepsFilesEqual(
            filename,
            Path(self.testing_path) / 'process-steps_test.json')
        Path(filename).unlink()

    def test_setup_paths(self):
        """
        Test setup of sdpchain paths
        """
        test_path = Path('hahahahahahahaha')
        if test_path.exists():
            return
        in_path = test_path / 'in_dir'
        out_path = test_path / 'out_dir'
        test_path.mkdir()
        in_path.mkdir()
        ns = Namespace
        ns.base_dir = str(test_path)
        ns.in_dir = 'in_dir'
        ns.out_dir = 'out_dir'
        new_in, new_out = sdpchain.setup_paths(ns, verbose=False)
        self.assertEqual(new_in, str(test_path / 'in_dir'))
        self.assertEqual(new_out, str(test_path / 'out_dir'))
        self.assertTrue(out_path.is_dir())
        out_path.rmdir()
        in_path.rmdir()
        test_path.rmdir()

    def test_sdpcat(self):
        """
        Test sdpcat on two files
        """
        # This shouldn't be necessary
        if Path('process-steps.json').exists():
            Path('process-steps.json').unlink()

        # Run the code
        system('sdpcat --ifs test.header.lch test.nimportequoi '
               '--of test.out -i data')

        # Compare binary files (test.out)
        outfname = 'test.out'
        self.assertTrue(Path(outfname).exists())
        self.assertBinFilesEqual(
            outfname,
            Path(self.testing_path) / outfname)
        Path(outfname).unlink()

        # Compare text files (process-steps.json)
        outfname = 'process-steps.json'
        self.assertTrue(Path(outfname).exists())
        target = Path('process-steps_sdpcat.json')
        Path(outfname).rename(target)
        self.assertProcessStepsFilesEqual(
            target,
            Path(self.testing_path) / 'process-steps_sdpcat.json')
        target.unlink()

    def test_sdpstep(self):
        """
        Test sdpstep
        """
        # Run the code
        system('sdpstep "cp data/A.txt C.txt"')
        Path("process-steps.json").unlink()
        self.assertTextFilesEqual("data/A.txt", "C.txt")
        Path("C.txt").unlink()

    def test_sdpstep_msmod(self):
        """
        Test sdpstep with msmod, which is what we often want to use
        """
        # Run the code
        system('sdpstep "msmod --net ZZ --quality Q -o outdata.mseed data/indata.mseed "')
        Path("process-steps.json").unlink()
        self.assertBinFilesEqual("data/outdata.mseed", "outdata.mseed")
        Path("outdata.mseed").unlink()

    def test_sdpstep_fail_notool(self):
        """
        Make sure sdpstep step fails smart if tool does not exist
        """
        self.assertFalse(sdpchain.is_tool("qwiovnksahweuhsdhuskjsda"))


    # def test_sdpstep_fail_redirection(self):
    #     """
    #     Make sure sdpstep step fails smart if tool does not exist
    #     """
    #     # Run the code
    #     args = 'sdpstep "cat A B > C"'.split()
    #     kwargs = dict(check=True)
    #     # self.assertRaises(ValueError, system, *args)
    #     self.assertRaises(subprocess.CalledProcessError, subprocess.run,
    #                       *args, **kwargs)
    #     Path("process-steps.json").unlink()


def suite():
    return unittest.makeSuite(TestMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
