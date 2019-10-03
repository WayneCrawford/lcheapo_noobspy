#!/usr/bin/python2.7
"lcFix.py --  Fix errors in lcheapo files."

from __future__ import print_function
from lcheapo import *
from argparse import ArgumentParser
import Queue
#import math

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME     = "lcPutHeaders"
VERSION          = "0.1"

                
##############################################################################
# Name          : getOptions
# Purpose       : To obtain the command line options (if any are given)
# Notes         : Uses the optparse library functions
##############################################################################
def getOptions():
    "Parse user passed options and parameters."
    descriptionStr = """Create LCHEAPO files from multiple file segments.
    The first input file must be a valid LCHEAPO file (with header)
    The remaining files are just data blocks.
    
    Outputs files with headers: the start time is injected into the filenames
    Makes each file start with Channel 0, because subsequent processing programs assume that.
    
    NOTE: Should probably also make a version that takes only "data block" files and adds
    a custom header (user inputs description field, sample rate and number of channels,
     use standard values for rest)
    
    BUG: if there are less directory entries in the first file than there should be
    for one of the files, will not create new entries (in fact, leaves all directory
    work for lcFix, which can only remove directory entries, not add them).
"""
    parser = ArgumentParser(description=descriptionStr)
    parser.add_argument("inputfiles", type=str, nargs='+', help="input files", default=False)
    parser.add_argument("--version", dest="version",
                      action = "store_true", help="Display Program Version", default=False)
    parser.add_argument("-s","--sitename", dest="sitename",default='temp',
                      help="Specify site name (all output files will start with this, default='temp')")
    parser.add_argument("-v", "--verbose", dest="verbosity",
                      action = "count", help="Be verbose (-v = kind of, -vv = very", default=0)
    parser.add_argument("-d", "--dryrun", dest="dryrun",
                      action = "store_true", default=False,
                      help="Dry Run: do not output files")
    arguments = parser.parse_args()
    
    # Get the filename (the arguments)
    if arguments.version:
        print("%s - Version: %s" % (PROGRAM_NAME, VERSION))
        sys.exit(0)
        
    if len(arguments.inputfiles) <= 2:
		if len(arguments.inputfiles) <=1:
			print("\n%s Error: Program requires at least one inputfile." % PROGRAM_NAME)
		else:
			print("\n%s Error: No point running this program with just one input file!" % PROGRAM_NAME)
		parser.print_help()
		sys.exit(-1)

    return arguments


def stopProcess(commandQ):
    if not commandQ:
        return False
    try:
        if commandQ.get(0) == "Stop":
            print("RECEIVED 'STOP' MESSAGE")
            return True
    except Queue.Empty:
        pass
    
    return False

##############################################################################
# Name          : main
##############################################################################
def main(args, commandQ=None, responseQ=None):

	# Set argument variables
	inFileNames=args.inputfiles
	verbosity=args.verbosity
	dryrun=args.dryrun
	sitename=args.sitename
	for iFile in range(len(inFileNames)):
		inFileName=inFileNames[iFile]
		ifp1 = open(inFileName, 'r')
		lcData = LCDataBlock()
		
		#=========================================================================
		if iFile==0:	# First file, extract header
			lcHeader, lcDir = (LCDiskHeader(), LCDirEntry())
			lcHeader.seekHeaderPosition(ifp1)
			lcHeader.readHeader(ifp1)
			lcHeader.printHeader()
			firstBlock = lcHeader.dataStart
			print("\n=========================================================================================")
			print(" INFILE                                  |     FIRSTBLOCK |    LASTBLOCK | OUTFILE")
			print("-----------------------------------------+----------------+--------------+-----------------")
		else:
			firstBlock=0	# dataBlocks will start at the very beginning
			# determine last block without using directory
		#=========================================================================

		ifp1.seek(0,2)				# Seek end of file
		lastBlock=ifp1.tell()/512	# Is this right?
		
		if stopProcess(commandQ):
			return
	

		# ---------------------------------
		# Copy the lcData blocks
		# ---------------------------------
		origFirstBlock=firstBlock
		lcData.seekBlock(ifp1,origFirstBlock)
		lcData.readBlock(ifp1)
		i=0
		while lcData.muxChannel != 0:
			i+=1
			lcData.readBlock(ifp1)
		firstBlock=origFirstBlock+i
		lcData.seekBlock(ifp1,firstBlock)	# Step back one so that next read is here
		
		for i in range(firstBlock, lastBlock):
			lcData.readBlock(ifp1)	# Read next block	
			if i==firstBlock:
				# Get first time, make filename, write header
				t=lcData.getDateTime()
				timestring=t.strftime("%Y%m%d%H%M%S")
				outFileName=sitename+'-'+timestring+'.lch'
				print("%40s | %12d+%1d | %12d | %20s " % (inFileName,origFirstBlock,firstBlock-origFirstBlock, lastBlock, outFileName))
				if not dryrun:
					ofp1 = open(outFileName, 'w')
					lcHeader.seekHeaderPosition(ofp1)
					lcHeader.writeHeader(ofp1)
					firstBlock_of=lcHeader.dataStart
					lcData.seekBlock(ofp1,firstBlock_of)
			if not dryrun:
				lcData.writeBlock(ofp1)
	
		# -----------------------
		# Close the files
		# -----------------------
		ifp1.close()
		if not dryrun:
			ofp1.close()
	print ("Processed %d files" % iFile)
	
	
# ----------------------------------------------------------------------------------
# Check for script invocation (run 'main' if the script is not imported as a module)
# ----------------------------------------------------------------------------------
if __name__ ==  '__main__':
    args = getOptions()
    
    commandQ=Queue.Queue(0)
    responseQ = Queue.Queue(0)
    main(args, commandQ, responseQ)
