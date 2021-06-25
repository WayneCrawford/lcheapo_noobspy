===================
lcheapo
===================

Python tools for processing LCHEAPO 2000 data files

All tools except `lcdump` and `lcinfo` create/append to a process-steps file
according to the SDPCHAIN rules

If you want to plot the data, or convert to SeisCompData structure miniSEED files, go to lcheapo_obspy_

.. _lcheapo_obspy: https://github.com/WayneCrawford/lcheapo_obspy

Overview
======================

Command-line programs:
----------------------

:lcdump: dump raw information from LCHEAPO files
:lcinfo: return basic information about an LCHEAPO file
:lccut: extract section of an LCHEAPO file
:lcfix: fix common bugs in an LCHEAPO file
:lcheader: create an LCHEAPO header + directory
:sdpcat: concatenate data files
:sdpstep: run a command line tool and save info to process-steps file

Modules:
----------------------

:lcheapo: functions accessing different parts of LCHEAPO 2000 files

Other subdirectories
======================

`lcheapo/_examples/`
------------------------------------------------------------

Should contain example information files and scripts:
