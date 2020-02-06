#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
print out blocks with bad time header values
"""
from lcheapo import (LCDataBlock, LCDiskHeader)

fname = '../tests/data/BUGGY.raw.lch'


def _read_and_print_dataheader(fp, block_num, title):
    lcData = LCDataBlock()
    lcData.seekBlock(fp, block_num)
    lcData.readBlock(fp)
    print(f'{title:12s} = {block_num:10d}: ', end='')
    lcData.prettyPrintHeader(annotated=True)


with open(fname, 'rb') as fp:
    # Get first data block number from the header
    lcHeader = LCDiskHeader()
    lcHeader.seekHeaderPosition(fp)
    lcHeader.readHeader(fp)
    first_data_block = lcHeader.dataStart
    # first_data_block = 0   # Force to start in header (bad "headers")
    # lcHeader.printHeader()

    # Figure out last data block number
    fp.seek(0, 2)                # Seek end of file
    last_data_block = int(fp.tell() / 512) - 1

    # Print out first and last data blocks
    _read_and_print_dataheader(fp, first_data_block, 'First block')
    _read_and_print_dataheader(fp, last_data_block, 'Last block')

    # Run through data blocks, printing out ones with bad times
    lcData = LCDataBlock()
    lcData.seekBlock(fp, first_data_block)
    n_bad = 0
    for i in range(first_data_block, last_data_block + 1):
        lcData.readBlock(fp)
        if lcData.year > 50:     # > 50 is 1950-1999
            n_bad += 1
            print(f'{i:10d}: ', end='')
            lcData.prettyPrintHeader(annotated=True)
    print(f'{n_bad:d} bad header times')
