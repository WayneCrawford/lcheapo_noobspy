#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dump record information from an LCHEAPO file
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA @UnusedWildImport

import sys
from optparse import OptionParser
from .lcheapo import (LCDiskHeader, LCDirEntry, LCDataBlock)
# from future import *
import datetime as dt

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME = "lcdump"
VERSION = "0.2.2"
version_notes = """
    v0.2 (2015/01): WCC added format options
    v0.2.1 (2017/01): WCC added possibility to compare time with theoretical
    v0.2.2 (2017/03): WCC added directory printing
    """


def getOptions():
    """
    Parse user passed options and parameters.

    Uses the optparse library
    """
    usageStr = "%prog [-h] [-v] OBSfile.raw startblock numblocks"
    parser = OptionParser(usageStr)
    parser.add_option("-v", "--version", dest="version",
                      action="store_true",
                      help="Display Program Version", default=False)
    parser.add_option("-p", "--printHead", dest="printHeader",
                      action="store_true",
                      help="Print disk header", default=False)
    parser.add_option("-d", "--printDirectory", dest="printDirectory",
                      action="store_true",
                      help="Print disk directory", default=False)
    parser.add_option("-f", "--format", dest="format", type="int",
                      help="Output format: 0: prettyPrint [default], \
                      1=decimalDump, 2=hexDump",
                      default=0)
    parser.add_option("-t", dest="compareClock", default=False,
                      action='store_true',
                      help="Compare clock to expected value (overrides format)"
                      )
    (opt, arguments) = parser.parse_args()

    # Get the filename (the arguments)
    if opt.version:
        print("{} - Version: {}".format(PROGRAM_NAME, VERSION))
        sys.exit(0)

    if len(arguments) != 3:
        print("\n{} Error: Program requires an input file with raw data and \
            a start block.".format(PROGRAM_NAME))
        parser.print_help()
        sys.exit(-1)

    return arguments[0], int(arguments[1]), int(arguments[2]), opt


def main(inFilename, startBlock, nBlocks, opt):

    inFilename, block, nBlocks, opt = getOptions()

    fp = open(inFilename, 'r')
    if opt.printHeader | opt.compareClock | opt.printDirectory:
        lcHeader = LCDiskHeader()
        lcHeader.readHeader(fp)
        if opt.printHeader:
            lcHeader.printHeader()
        if opt.printDirectory:
            lcDir = LCDirEntry()
            lcDir.seekBlock(fp, lcHeader.dirStart)
            iDir = 0
            print("="*80)
            print(" {:25s} {:8s} {:15s} {:10s} {:12s} {:11s} {}".format(
                "DateTime", "MuxChan", "SPS", "block#",
                "numBlocks", "recordLen", "Flag"))
            print("="*80)
            while iDir < lcHeader.dirCount:
                lcDir.readDirEntry(fp)
                print(lcDir)
                iDir = iDir + 1

    if opt.format < 0 or opt.format > 2:
        print("Unknown header print format: {:d}".format(format))
        sys.exit(-1)

    if opt.compareClock:
        firstBlock = lcHeader.dataStart
        if firstBlock == 0:   # normal start block
            firstBlock = 2393
        lcStartData = LCDataBlock()
        lcStartData.seekBlock(fp, firstBlock)
        lcStartData.readBlock(fp)
        firstTime = dt.datetime(lcStartData.year+2000,
                                lcStartData.month,
                                lcStartData.day,
                                lcStartData.hour,
                                lcStartData.minute,
                                lcStartData.second,
                                lcStartData.msec*1000)
        print("First block = {:d}: Time = {} ".format(firstBlock,
              firstTime.strftime('%Y/%m/%d-%H:%M:%S.%f')[:-3]))
        sampRate = lcHeader.sampleRate
        if sampRate == 0:
            sampRate = 62.5
            print("Sample rate not in directory header, assuming 62.5")
        print(" {:^6s} : {:^2s} | {:^22s} | {:^24s} | {:^7s} ".format(
              "BLOCK", "CH", "EXPECTED TIME", "FOUND TIME", "DELTA"))
        print("-{:-^6s}-:-{:-^2s}-|-{:-^22s}-|-{:-^24s}-|-{:-^7s}-".format(
              "-", "-", "-", "-", "-"))

    block = startBlock
    lcData = LCDataBlock()
    lcData.seekBlock(fp, block)

    for i in range(0, nBlocks):
        lcData.readBlock(fp)
        print("Hi")
        print("Hi", end=' ')
        print("{:8d}:".format(startBlock + i), end=' ')
        if opt.compareClock:
            time = dt.datetime(lcData.year+2000,
                               lcData.month,
                               lcData.day,
                               lcData.hour,
                               lcData.minute,
                               lcData.second,
                               lcData.msec*1000)
            calcTime = firstTime + dt.timedelta(
                            seconds=((startBlock + i - firstBlock) / 4) *
                            lcData.numberOfSamples / sampRate)
            print("{:2d} |{} | {} | {:8.3f}".format(
                lcData.muxChannel,
                calcTime.strftime('%Y/%m/%d-%H:%M:%S.%f')[:-3],
                time.strftime('%Y/%m/%d-%H:%M:%S.%f')[:-3],
                (time-calcTime).total_seconds())
            )
            # print "%02d/%02d/%02d-%02d:%02d:%02d.%03d " %
            #  (lcData.year, lcData.month, lcData.day,lcData.hour,
            #   lcData.minute, lcData.second, lcData.msec),
            # print "F%03d CH%02d %4d samps U1=%03d U2=%03d" %
            #  (lcData.blockFlag, lcData.muxChannel, lcData.numberOfSamples,
            #   lcData.U1, lcData.U2)
        elif opt.format == 1:
            lcData.printDecimalDumpOfHeader(True)
        elif opt.format == 2:
            lcData.printHexDumpOfData()
        elif opt.format == 0:
            lcData.prettyPrintHeader()
        else:
            print("ERROR! Shouldn't get here!")


# ----------------------------------------------------------------------------------
# Run 'main' if the script is not imported as a module
# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
