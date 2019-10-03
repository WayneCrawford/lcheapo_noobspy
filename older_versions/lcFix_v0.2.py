#!/usr/bin/python2.7
"lcFix.py --  Fix errors in lcheapo files."

from lcheapo import *
from optparse import OptionParser
import Queue
import math

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME     = "lcfix"
VERSION          = "0.2"

                
##############################################################################
# Name          : getOptions
# Purpose       : To obtain the command line options (if any are given)
# Inputs        : none
# Outputs       : none
# Bidirectional : none
# Returns       : 
# Notes         : Uses the optparse library functions
##############################################################################
def getOptions():
    "Parse user passed options and parameters."
    usageStr = """%prog [-h] [-v] OBSfile.raw output.raw
    	Fixes 2 standard LCHEAPO BUGS:
    		1: A second is dropped then picked up on the next block.
    		2: Time gets screwed up every several months only on 1 block/ch
    	New in version 0.2:
    		- Handles spliced datafiles with zero-filled gaps:
    			+ Adds dates to headers in gap 
    			+ Verifies that gap is the right size (no time tear afterwards)
    		- Handles incomplete datafiles
    			+ Warns the user that the data do not go as far as the directory claims
    			+ Changes the "directoryEntries" value in the header
    	Also reports (but does/can not fix!) other time tears
"""
    parser = OptionParser(usageStr)
    parser.add_option("--version", dest="version",
                      action = "store_true", help="Display Program Version", default=False)
    parser.add_option("-v", "--verbose", dest="verbosity",
                      action = "count", help="Be verbose (-v = kind of, -vv = very", default=0)
    (opt, arguments) = parser.parse_args()
    
    # Get the filename (the arguments)
    if opt.version:
        print "%s - Version: %s" % (PROGRAM_NAME, VERSION)
        sys.exit(0)
        
    if len(arguments) != 2:
        print "\n%s Error: Program requires an input file with raw data and an output filename." % PROGRAM_NAME
        parser.print_help()
        sys.exit(-1)

    return arguments[0], arguments[1], opt.verbosity


##############################################################################
# Name          : getTimeDelta
# Purpose       : Convert a floating point number, representing a time offset in
#                 seconds, into a datetime.timedelta object.
#                 corresponding to the number of milliseconds.
# Inputs        : floatTimeInSec    - Floating point number holding the number of
#                                     seconds.  The fractional part will correspond
#                                     to milliseconds.
# Outputs       : none
# Bidirectional : none
# Returns       : A datetime.timedelta object.
# Notes         : none
##############################################################################
def getTimeDelta(floatTimeInSec):
    "Return a timedelta() object correspoding to the seconds passed into the function."
    days = int (floatTimeInSec / 86400)
    floatTimeInSec -= days * 86400

    hours = int (floatTimeInSec / 3600)
    floatTimeInSec -= hours * 3600

    minutes = int (floatTimeInSec/60)
    floatTimeInSec -= minutes * 60
    
    seconds = int (floatTimeInSec)
    floatTimeInSec -= seconds

    msec = int (floatTimeInSec) * 1000

    return datetime.timedelta(days, seconds, 0, msec, minutes, hours)


##############################################################################
# Name          : convertToMSec
# Purpose       : Convert a datetime.timedelta object into corresponding number
#                 of milliseconds.
# Inputs        : tm   -  datetime.timedelta() object
# Outputs       : none
# Bidirectional : none
# Returns       : int  -  milliseconds
# Notes         : none
##############################################################################
def convertToMSec(tm):
    "Given a timedelta() object return the corresponding number of milliseconds."
    return ((tm.days * 86400) + (tm.seconds)) * 1000 + int (tm.microseconds/1000)

    
def stopProcess(commandQ):
    if not commandQ:
        return False
    try:
        if commandQ.get(0) == "Stop":
            print "RECEIVED 'STOP' MESSAGE"
            return True
    except Queue.Empty:
        pass
    
    return False

##############################################################################
# Name          : main
# Purpose       : -
# Inputs        : -
# Outputs       : -
# Bidirectional : -
# Returns       : -
# Notes         : -
##############################################################################
def main(inFilename, outFilename, verbosity, commandQ=None, responseQ=None):
	ifp1 = open(inFilename, 'r')
	ofp1 = open(outFilename, 'w')

	lcHeader, lcDir, lcData = (LCDiskHeader(), LCDirEntry(), LCDataBlock())

	# -----------------------------
	# Find and copy the disk header
	# -----------------------------
	lcHeader.seekHeaderPosition(ifp1)
	lcHeader.seekHeaderPosition(ofp1)
	lcHeader.readHeader(ifp1)
	lcHeader.writeHeader(ofp1)
	if stopProcess(commandQ):
		return

	# ---------------------------------
	# Copy and modify the lcData blocks
	# ---------------------------------
	lastBlock = lcDir.determineLastBlock(ifp1)
	firstBlock = lcHeader.dataStart
	
	blockTime = int ((166 * (1.0/lcHeader.realSampleRate)) * 1000)
	blockTimeDelta = datetime.timedelta(0, 0, 0, blockTime, 0, 0)

	# Grab the first time entries (one for each channel) and adjust them
	# so that they point an entire blockTimeDelta in the past.  This is done to
	# "prime the pump" so that we can add in the blockTimeDelta the first time we
	# use it.
	lcData.seekBlock(ifp1, firstBlock)
	lastTime = []
	if verbosity > 1:
		lcHeader.printHeader()
	for i in range (0, lcHeader.numberOfChannels):
		lcData.readBlock(ifp1)
		lastTime.append(lcData.getDateTime() - blockTimeDelta)

	ifp1.seek(0,2); # Go to the end
	lastAddress=ifp1.tell()
	# Back up to data start block
	lcData.seekBlock(ifp1, firstBlock)
	lcData.seekBlock(ofp1, firstBlock)
	i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear = 0, 0, 0, 0
	inGap_counter=0
	quitEarly=False

	# Check to make sure the file is as long as the directory says (WCC)
	firstBlockAddress=ifp1.tell()
	numFileBlocks=math.floor((lastAddress-firstBlockAddress)/512)
	if verbosity:
		print "firstBlock=%d, lastBlock=%d, dirBlocks=%d, fileBlocks=%d" % (firstBlock, lastBlock, lastBlock-firstBlock+1,numFileBlocks, )

	# Cycle through every block and compare the expected time to the actual time.
	#for i in range(firstBlock, lastBlock+1):	% Have problems with last block sometimes
	for i in range(firstBlock, lastBlock+1-100*lcHeader.numberOfChannels):
		lcData.readBlock(ifp1)
		if verbosity > 1:	# Very verbose, print each block header
			print "%8d(%d):" % (i,ifp1.tell()),
			lcData.printDecimalDumpOfHeader()
		if (lcData.year==0 and lcData.month==0 and lcData.day==0):	# We are in a user-created zero data block
			if inGap_counter==0 :
				t=lastTime[0] + blockTimeDelta
				print "YEAR=MONTH=DAY=0: User-created data gap at block %d (~%s), filling in block headers" % (ifp1.tell()/512 - 2,t) 
			lcData.blockFlag=previousBlockFlag
			lcData.numberOfSamples=previousNumberOfSamples
			lcData.muxChannel = previousMuxChannel+1
			if (lcData.muxChannel >= lcHeader.numberOfChannels) :
				lcData.muxChannel=0
			t=lastTime[lcData.muxChannel] + blockTimeDelta
			if verbosity:
				print "                       Setting CH%d time to %s   Block %d" % (lcData.muxChannel,t,ifp1.tell()/512 - 2)
			lcData.changeTime(t)
			inGap_counter += 1
		else: 
			if inGap_counter>0:
				print "                       Gap ended after %d blocks (%.1f seconds)   Block %d" % (inGap_counter,(inGap_counter/lcHeader.numberOfChannels)*blockTime/1000,ifp1.tell()/512 - 2)
			expectedTime = lastTime[lcData.muxChannel] + blockTimeDelta
			t = lcData.getDateTime()
			diff = abs(convertToMSec(t - expectedTime))
			if diff:
				if diff > 1100:
					# Difference is greater than 1-second.  This could be a time tear or another
					# lcheapo bug (bad time entry).
					if inGap_counter > 0:
						print "CH%d: time=%s     Block %d" % (lcData.muxChannel,lcData.getDateTime(),ifp1.tell()/512 - 2)
						if convertToMSec(t - expectedTime) > 0:
							print "    %.1f second time tear after gap!  Your data gap is probably %d blocks TOO SHORT" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
						else:
							print "    %.1f second time overlap after gap!  Your data gap IS PROBABLY %d blocks TOO LONG" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
						lastTime[lcData.muxChannel]=lcData.getDateTime()
						for j in range(lcHeader.numberOfChannels-1): # skip one set of channels
							lcData.readBlock(ifp1)
							lastTime[lcData.muxChannel]=lcData.getDateTime()
					else:
						pos = ifp1.tell()
						channel = lcData.muxChannel

						# Find the next block with the same channel
						tempData = LCDataBlock()
						tempData.readBlock(ifp1)
						while channel != tempData.muxChannel: tempData.readBlock(ifp1)

						tempTime = tempData.getDateTime()
						tempDiff = abs(convertToMSec(tempTime - expectedTime))
						ifp1.seek(pos)
						if (tempDiff - 2*convertToMSec(blockTimeDelta) < 2):
							# Stupid LCHEAPO BUG - Time gets screwed up every several months only on 1 block/ch
							print "Stupid LCHEAPO BUG #2.  CH%d Expected Time: %s, Got: %s    Block %d" % (lcData.muxChannel,expectedTime, t, ifp1.tell()/512 - 2)
							countErrorTimeBug2 += 1
							t = expectedTime
							lcData.changeTime(t)
						else:
							# Time tear (leave the time stamp alone - do not fix it!)
							print "Time Tear in Data.   CH%d Expected Time: %s, Got: %s    Block %d" % (lcData.muxChannel,expectedTime, t, ifp1.tell()/512 - 2)
							countErrorTear += 1
				else:
					# Stupid LCHEAPO BUG - A second is dropped then picked up on the next block.
					print "Stupid LCHEAPO BUG #1. CH%d Expected Time: %s, Got: %s    Block %d" % (lcData.muxChannel,expectedTime, t, ifp1.tell()/512 - 2)
					countErrorTimeBug1 += 1
					t = expectedTime
					lcData.changeTime(t)
			inGap_counter=0    
		# Write out the block of data and report status (if necessary)
		lcData.writeBlock(ofp1)
		if (i%5000 == 0):
			#print "Block %d (%d 1-sec errors, %d bad time, %d time tear)" % (i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear)
			if stopProcess(commandQ):
				return
			if responseQ:
				responseQ.put((i, lastBlock+1, countErrorTimeBug1, countErrorTear))
			
		lastTime[lcData.muxChannel] = t
		previousMuxChannel=lcData.muxChannel
		previousBlockFlag=lcData.blockFlag
		previousNumberOfSamples=lcData.numberOfSamples
	
	print "Finished at block %d (%d 1-sec errors, %d bad time, %d time tear)" % (i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear)
	if responseQ:
		responseQ.put((i, lastBlock+1, countErrorTimeBug1, countErrorTear))

	# ----------------------------------------------------------------------
	# Copy over the directory entries and modify the block time to correspond
	# to the actual time in the data block.
	# ----------------------------------------------------------------------

	# Open the output file for reading in the block data
	ifp2 = open(outFilename, 'r')
	lcData2 = LCDataBlock()

	# Seek the directory location
	lcDir.seekBlock(ifp1, lcHeader.dirStart)
	lcDir.seekBlock(ofp1, lcHeader.dirStart)
	
	# If quit early, correct the number of directory values in the  header
	if quitEarly:
		print "SHOULD CHANGE THE NUMBER OF DIRECTORY ENTRIES (on seekBlock in next Part?)"

	# Copy directory but change the time to correspond to the time in the data block.
	# The file pointer ifp2 points to the data block.
	if verbosity:
		print "COPYING/CORRECTING DIRECTORY"
		print " DIR# |    BLOCK# | DIRTIME                    | BLOCKTIME                | DIFF (SECS)"
		print " -----+-----------+----------------------------+--------------------------+------------"
	for i in range(0, lcHeader.dirCount):
		lcDir.readDirEntry(ifp1)
		if verbosity:
			print " %4d | %9d | %-26s |" % (i+1,lcDir.blockNumber,lcDir.getDateTime()),
		if lcDir.blockNumber > lastBlock :
			print "\nDIR%d, BLOCK%d IS BEYOND THE END OF FILE!" % (i+1,lcDir.blockNumber)
			print "REDUCING NUMBER OF DIRECTORY ENTRIES IN HEADER FROM %d TO %d" % (lcHeader.dirCount,i)
			lcHeader.dirCount=i
			lcHeader.seekHeaderPosition(ofp1)
			lcHeader.writeHeader(ofp1)
			print "QUITTING"
			break
		lcData2.seekBlock(ifp2, lcDir.blockNumber)
		lcData2.readBlock(ifp2)
		blockTime = lcData2.getDateTime()
		if verbosity:
			diff = abs(convertToMSec(blockTime-lcDir.getDateTime()))
			if diff>1:
				print " %-26s | %14.1f" % (blockTime,diff/1000)
			else:
				print " SAME            |   0"
		lcDir.changeTime(blockTime)
		lcDir.writeDirEntry(ofp1)
		if stopProcess(commandQ):
			return


	# -----------------------
	# Close off all the files
	# -----------------------
	ofp1.close()
	ifp1.close()
	ifp2.close()




# ----------------------------------------------------------------------------------
# Check for script invocation (run 'main' if the script is not imported as a module)
# ----------------------------------------------------------------------------------
if __name__ ==  '__main__':
    inFilename, outFilename, verbosity = getOptions()
    #main(inFilename, outFilename)
    commandQ=Queue.Queue(0)
    responseQ = Queue.Queue(0)
    main(inFilename, outFilename, verbosity, commandQ, responseQ)
