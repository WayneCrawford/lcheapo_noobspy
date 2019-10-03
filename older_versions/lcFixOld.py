#!/usr/bin/env python
"lcFix.py --  Fix errors in lcheapo files."

from lcheapo import *
from optparse import OptionParser
import Queue

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME     = "lcfix"
VERSION          = "0.1"

                
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
    usageStr = "%prog [-h] [-v] OBSfile.raw output.raw"
    parser = OptionParser(usageStr)
    parser.add_option("-v", "--version", dest="version",
                      action = "store_true", help="Display Program Version", default=False)
    (opt, arguments) = parser.parse_args()
    
    # Get the filename (the arguments)
    if opt.version:
        print "%s - Version: %s" % (PROGRAM_NAME, VERSION)
        sys.exit(0)
        
    if len(arguments) != 2:
        print "\n%s Error: Program requires an input file with raw data and an output filename." % PROGRAM_NAME
        parser.print_help()
        sys.exit(-1)

    return (arguments)


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
def main(inFilename, outFilename, commandQ=None, responseQ=None):
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
    for i in range (0, lcHeader.numberOfChannels):
        lcData.readBlock(ifp1)
        lastTime.append(lcData.getDateTime() - blockTimeDelta)

    # Back up to data start block
    lcData.seekBlock(ifp1, firstBlock)
    lcData.seekBlock(ofp1, firstBlock)
    i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear = 0, 0, 0, 0

    # Cycle through every block and compare the expected time to the actual time.
    for i in range(firstBlock, lastBlock+1):
        lcData.readBlock(ifp1)
        t = lcData.getDateTime()
        expectedTime = lastTime[lcData.muxChannel] + blockTimeDelta
        diff = abs(convertToMSec(t - expectedTime))
        if diff:
            if diff > 1100:
                # Difference is greater than 1-second.  This could be a time tear or another
                # lcheapo bug (bad time entry).
                countErrorTear += 1
                pos = ifp1.tell()
                channel = lcData.muxChannel

                # Find the next block with the same channel
                tempData = LCDataBlock()
                tempData.readBlock(ifp1)
                while channel != tempData.muxChannel: tempData.readBlock(ifp1)

                tempTime = tempData.getDateTime()
                tempDiff = abs(convertToMSec(tempTime - expectedTime))
                if (tempDiff - 2*convertToMSec(blockTimeDelta) < 2):
                    # Stupid LCHEAPO BUG - Time gets screwed up every several months only on 1 block/ch
                    print "Stupid LCHEAPO BUG #2.  Expected Time: %s, Got: %s    Block %d" % (expectedTime, t, ifp1.tell()/512 - 2)
                    countErrorTimeBug2 += 1
                    t = expectedTime
                    lcData.changeTime(t)
                else:
                    # Time tear (leave the time stamp alone - do not fix it!)
                    print "Time Tear in Data.      Expected Time: %s, Got: %s    Block %d" % (expectedTime, t, ifp1.tell()/512 - 2)
                    countErrorTear += 1
                ifp1.seek(pos)
            else:
                # Stupid LCHEAPO BUG - A second is dropped then picked up on the next block.
                print "Stupid LCHEAPO BUG #1.  Expected Time: %s, Got: %s    Block %d" % (expectedTime, t, ifp1.tell()/512 - 2)
                countErrorTimeBug1 += 1
                t = expectedTime
                lcData.changeTime(t)
            
        # Write out the block of data and report status (if necessary)
        lcData.writeBlock(ofp1)
        if (i%5000 == 0):
            #print "Block %d (%d 1-sec errors, %d bad time, %d time tear)" % (i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear)
            if stopProcess(commandQ):
                return
            if responseQ:
                responseQ.put((i, lastBlock+1, countErrorTimeBug1, countErrorTear))
                
        lastTime[lcData.muxChannel] = t
        
    print "Block %d (%d 1-sec errors, %d bad time, %d time tear)" % (i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear)
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

    # Copy directory but change the time to correspond to the time in the data block.
    # The file pointer ifp2 points to the data block.
    for i in range(0, lcHeader.dirCount):
        lcDir.readDirEntry(ifp1)
        lcData2.seekBlock(ifp2, lcDir.blockNumber)
        lcData2.readBlock(ifp2)
        blockTime = lcData2.getDateTime()
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
    inFilename, outFilename = getOptions()
    #main(inFilename, outFilename)
    commandQ=Queue.Queue(0)
    responseQ = Queue.Queue(0)
    main(inFilename, outFilename, commandQ, responseQ)
