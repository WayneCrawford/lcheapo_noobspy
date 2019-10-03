#!/usr/bin/python2.7
"lcFix.py --  Fix errors in lcheapo files."

from __future__ import print_function
from lcheapo import *
import argparse
import Queue
import math
import os
import json
import textwrap
#import datetime

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
versionString="0.51"
VERSIONS = """    	VERSIONS
    	 0.2:
    		- Handles spliced datafiles with zero-filled gaps:
    			+ Adds dates to headers in gap 
    			+ Verifies that gap is the right size
    			  (no time tear afterwards)
    		- Handles incomplete datafiles
    			+ Warns the user that the data do not go as far as the
    			  directory claims
    			+ Changes the "directoryEntries" value in the header
    	0.3:		
    		- Output starts with block #
    		- Output is streamlined for zero- filled gaps
    		- Confirm channel #: consecutive and < 4)
    		- Changed block# reported to conform to lcdump.py (tell()/512-1)
    		- Expanded BUG2 to handle 2 consecutive bad times/channel
    		  (called BUG #2b)
    		- Time tears (MUST BE FIXED) are saved to timeTears.txt
    		- Bug #1s repeating every 500 blocks are identified as Bug #3
    		  (can reduce the text output by a lot!)
    	0.4:		
    		- Expanded BUG #2 to handle up to 3 consecutive bad times/channel
    		  (BUG #2c)
    	0.45:		
    		- Add --dryrun option (don't output fixed LCHEAPO file)
    		- Add check of non-time header values
    	0.46:		
    		- By default, program names output file
    	0.5:		
    		- Creates a JSON file with execution information
    		- Handles multiple lcheapo input files (should be different fragments of
    			same station, still only write one JSON file)
    	0.51:		
    		- Names the JSON file based on the input filename (each input file gets its own JSON)
    		- Add -F (forceTimes) option: to force time tags to be consecutive (should
    		  only be used if all identified time tears are proven wrong
    		  by comparing arrival times of events across stations)
    	NOT YET:
    		- Force non-time header values
"""
                
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
	
	parser = argparse.ArgumentParser(description="Fix common LCHEAPO bugs",
		epilog=textwrap.dedent("""\
	=========================================================================
	The LCHEAPO bugs are:\n\
		1: A second is dropped then picked up on the next block.
		2: Time tag is wrong for at most 3 consecutive blocks/ch
		
	Outputs (for input filename root.ext):
		root-fix.ext: fixed data
		root-fix.txt: information about fixes applied
		root-timetears.txt: time tear lines (if any) 
	Notes:
		- TIME TEARS MUST BE ELIMINATED BEFORE FURTHER PROCESSING!!!
		- Sometimes (if there were 3+ consecutive bad times/channel, but not
			an overall time tear), rerunning this program on the
			output will get rid of leftover "time tears"
	Recommendations:
		- Name your inputfile STA.lch, where STA is the station name
		- After running, and once all time tears have been hand-corrected,
			re-run %prog -v --dryrun on the fixed file to verify
			that there are no remaining errors and to get information
			about the directory header.  
	Example: 
		- for an LCHEAPO file named RR38.lch:
			> lcFix.py RR38.lch  > RR38-fix.txt
			> lcFix.py -v --dryrun RR38-fix.lch > RR38-verify.txt
"""),
	formatter_class=argparse.RawDescriptionHelpFormatter)
	
	
	parser.add_argument("infiles", metavar="inFileName", nargs='+', help="Input filename(s)")
	parser.add_argument("--version", action='version', version='%(prog)s {:s}'.format(versionString))
	parser.add_argument("-v", "--verbose", dest="verbosity",action = "count", default=0,
						help="Be verbose (-v = kind of, -vv = very")
	parser.add_argument("-d", "--dryrun", dest="dryrun",action = "store_true", default=False,
						help="Dry Run: do not output fixed LCHEAPO file")
	parser.add_argument("-F", "--forceTimes", dest="forceTime",action = "store_true", default=False,
						help="Force times to be consecutive (use only if time tear identified but proven false by synchronizing events before and after)")
	#     parser.add_argument("-o", "--outfile", dest="outfile",
	# 						help="Force output (fixed) file name (only works if one input file)")
	args = parser.parse_args()

	return args


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
            print("RECEIVED 'STOP' MESSAGE")
            return True
    except Queue.Empty:
        pass
    
    return False

def endBUG3(startBlock,endBlock):
	global startBUG3
	if startBUG3 >=0:
		print("%8d:    End LCHEAPO BUG #3 (started at %d)" % (endBlock, startBlock))
		global printHeader
		startBUG3=-1
		printHeader=''

##############################################################################
# Name          : main
# Purpose       : -
# Inputs        : -
# Outputs       : -
# Bidirectional : -
# Returns       : -
# Notes         : -
##############################################################################
def main(args, commandQ=None, responseQ=None):

	# Prepare variables
	iBug1=iBug2=iTT=iWH=iFiles=0
	
	if args.dryrun:
		print("DRY RUN: will not output a new file (useful for verifying that no errors remain)")
		if args.forceTime:
			print("-F (forceTimes) IGNORED during dry run")
			args.forceTime=False
	# Loop through input files
	for fname in args.infiles :
		print("Working on file ",fname)
		#(nBug1,nBug2,nTT,nWH) = 1,2,0,4
		(nBug1,nBug2,nTT,nWH) = processInputFile(fname,args,commandQ, responseQ)
		iBug1+=nBug1
		iBug2+=nBug2
		iTT+=nTT
		iWH+=nWH
		iFiles+=1
	
	print("\n=================================================================================================")
	if not args.forceTime:	# Standard case
		print("Overall totals: {:d} files, {:d} BUG1s, {:d} BUG2s, {:d} Time Tears, {:d} unexpected header values".format(iFiles,iBug1,iBug2,iTT,iWH))
		if iBug1>0:
			print("  BUG1= 1-second errors in time tag")
		if iBug2>0:
			print("  BUG2= Other isolated errors in time tag")
		if iTT>0:
			print("  Time Tear=Bad time tag (BUG1 or BUG2) for more than two consecutive samples.  Could be long")
			print("            stretch of bad records or an offset in records (must be fixed)")

		# Make error message (and return code) if there are time tears
		if iTT>0:
			print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
			print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
			print("YOU HAVE {:d} TIME TEARS: YOU MUST ELIMINATE THEM ALL BEFORE CONTINUING!!!".format(iTT))
			print('Use "lcDump.py OBSfile.lch STARTBLOCK NUMBLOCKS" to look at suspect sections')
			print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
			print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
	 		sys.exit(-1)
	else:	# Forced time corrections
		print("FORCED TIME CORRECTIONS, NO EVALUATION OF BUG1s and BUG2s ")
		print("(should have run this on a previously fixed file with only false time tears left)")
		print("Overall totals: {:d} files, {:d} Forced corrections, {:d} unexpected header values".format(iFiles,iTT,iWH))

	sys.exit(0)
	
##############################################################################
# Name          : processInputFile
# Purpose       : -
# Inputs        : -
# Outputs       : -
# Bidirectional : -
# Returns       : -
# Notes         : Was main() up to version 0.5, where main handled JSON file creation and multiple input files
##############################################################################
def processInputFile(inFilename, args, commandQ=None, responseQ=None):

	# Declare variables
	global startBUG3, printHeader
	i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr= 0, 0, 0, 0, 0
	lastBUG1s=[0,0,0,0]
	printHeader=''
	startBUG3=-1
	inGap_counter=0
	quitEarly=False
	previousMuxChannel=-1
	previousBlockFlag=73
	previousNumberOfSamples=166
	previousU1=3
	previousU2=166
	verbosity=args.verbosity
	consecIdentTimeErrors, oldDiff= 0,0	# Currently only used for Force Time option

	startTimeStr=datetime.datetime.strftime(datetime.datetime.utcnow(),'%Y-%m-%dT%H:%M:%SZ')

	(root,ext)=os.path.splitext(inFilename)
	ifp1 = open(inFilename, 'r')
	if not args.dryrun:
		#if args.outfile is None :
		outfilename=root+"-fix"+ext
		ofp1 = open(outfilename, 'w')
	fname_timetears=root+'-timetears.txt'
	oftt = open(fname_timetears,'w');

	lcHeader, lcDir, lcData = (LCDiskHeader(), LCDirEntry(), LCDataBlock())

	# -----------------------------
	# Find and copy the disk header
	# -----------------------------
	lcHeader.seekHeaderPosition(ifp1)
	lcHeader.readHeader(ifp1)
	if not args.dryrun:
		lcHeader.seekHeaderPosition(ofp1)
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
	if verbosity:
		lcHeader.printHeader()
	for i in range (0, lcHeader.numberOfChannels):
		lcData.readBlock(ifp1)
		lastTime.append(lcData.getDateTime() - blockTimeDelta)

	ifp1.seek(0,2); # Go to the end
	lastAddress=ifp1.tell()
	# Back up to data start block
	lcData.seekBlock(ifp1, firstBlock)
	if not args.dryrun:
		lcData.seekBlock(ofp1, firstBlock)

	# Check to make sure the file is as long as the directory says (WCC)
	firstBlockAddress=ifp1.tell()
	numFileBlocks=math.floor((lastAddress-firstBlockAddress)/512)
	#if verbosity:
	print ("  ==========================================================================")
	print ("  firstBlock=%d, lastBlock=%d, dirBlocks=%d, fileBlocks=%d" % (firstBlock, lastBlock, lastBlock-firstBlock+1,numFileBlocks ))
	print ("  ==========================================================================")

	# Cycle through every block and compare the expected time to the actual time.
	#for i in range(firstBlock, lastBlock+1):	% Have problems with last block sometimes
	for i in range(firstBlock, lastBlock+1-100*lcHeader.numberOfChannels):
		lcData.readBlock(ifp1)
		currBlock=ifp1.tell()/512-1
		if startBUG3>=0 and currBlock>lastBUG1s[0]+500:
			endBUG3(startBUG3,currBlock)
		if i != currBlock:
			print("Error: currBlock (%d) != i (%d)" % (currBlock,i))
		if verbosity > 1:	# Very verbose, print each block header
			print("%8d(%d): " % (i,ifp1.tell()),end='')
			#lcData.printDecimalDumpOfHeader(True)
			lcData.prettyPrintHeader()
		###### USER-CREATED ZERO DATA BLOCK #############
		if (lcData.year==0 and lcData.month==0 and lcData.day==0):
			if inGap_counter==0 :
				t=lastTime[0] + blockTimeDelta
				bugStartBlock=currBlock
				bugStartDate=t
				print("%s%8d: ZERO-FILLED DATA GAP Starts, filling headers" % (printHeader,currBlock))
				#print "YEAR=MONTH=DAY=0: User-created data gap at block %d (~%s), filling in block headers" % (ifp1.tell()/512 - 2,t) 
			lcData.blockFlag=previousBlockFlag
			lcData.numberOfSamples=previousNumberOfSamples
			lcData.U1=previousU1
			lcData.U2=previousU2
			lcData.muxChannel = previousMuxChannel+1
			if (lcData.muxChannel >= lcHeader.numberOfChannels) :
				lcData.muxChannel=0
			t=lastTime[lcData.muxChannel] + blockTimeDelta
			if verbosity:
				print("                       Data Gap: Setting CH%d time to %s   Block %d" % (lcData.muxChannel,t,currBlock))
			lcData.changeTime(t)
			bugEndDate=t
			inGap_counter += 1
		else: 
			##### VERIFY NON-TIME HEADER VALUES ############
			if (lcData.blockFlag!=73) | (lcData.numberOfSamples!=166) | (lcData.U1!=3) | (lcData.U2!=166) :
				if (countUnexpectHdr < 100) :
					print("%s%8d: Unexpected non-time header values:" % (printHeader,currBlock),end='')
					lcData.prettyPrintHeader(True)
				elif (countUnexpectHdr == 100) :
					print("%s%8d: >100 Unexpected non-time headers: WON'T PRINT ANY MORE!" % (printHeader,currBlock))
				countUnexpectHdr+=1
			##### VERIFY CHANNEL NUMBER ############
			if previousMuxChannel != -1 :
				predictedChannel=previousMuxChannel+1
				if predictedChannel>=lcHeader.numberOfChannels :
					predictedChannel=0
				if lcData.muxChannel != predictedChannel :
					if ((lcData.muxChannel > lcHeader.numberOfChannels) | (lcData.muxChannel < 0)):
						print("%s%8d: WARNING: Channel = %d IS IMPOSSIBLE, setting to predicted %d" % (printHeader,currBlock,lcData.muxChannel,predictedChannel))
						lcData.muxChannel = predictedChannel
					else:
						print("%s%8d: WARNING: Channel = %d, predicted was %d" % (printHeader,currBlock,lcData.muxChannel,predictedChannel))
			if inGap_counter>0:
				###### END OF USER-CREATED ZERO DATA BLOCK #############
				print("%s%8d: ZERO-FILLED DATA GAP Ends: %6d blocks (~%.1f seconds, from %s to %s)" % (
					printHeader,currBlock-1, inGap_counter,(inGap_counter/lcHeader.numberOfChannels)*blockTime/1000.,
					 bugStartDate, bugEndDate))
			expectedTime = lastTime[lcData.muxChannel] + blockTimeDelta
			t = lcData.getDateTime()
			diff = abs(convertToMSec(t - expectedTime))
			if diff:
				if args.forceTime:
					if (consecIdentTimeErrors>0) & (diff != oldDiff): # Starting a new time offset
							print("%d blocks" % consecIdentTimeErrors)
							consecIdentTimeErrors=0
							
					if consecIdentTimeErrors==0: # New time error or error offset
						print("%s%8d:    CH%d: %g-s offset FORCED to conform..." % (printHeader,currBlock,lcData.muxChannel,diff/1000.),end='')

					t = expectedTime
					lcData.changeTime(t)
					countErrorTear += 1	# Use time tear counter to count forced
					consecIdentTimeErrors += 1	# Currently only used for forceTime
					oldDiff=diff
				else:
					if diff > 1100:
						# Difference is greater than 1-second.  This could be a time tear or another
						# lcheapo bug (bad time entry).
						if inGap_counter > 0:
							print("%s%8d:    CH%d: TIME=%s" % (printHeader,currBlock,lcData.muxChannel,lcData.getDateTime()),end='')
							if convertToMSec(t - expectedTime) > 0:
								txt= "    %.1f second time tear after gap!  YOUR DATA GAP IS PROBABLY %d blocks TOO SHORT" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
							else:
								txt= "    %.1f second time overlap after gap!  YOUR DATA GAP IS PROBABLY %d blocks TOO LONG" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
							print(printHeader+txt)
							print(printHeader+txt,file=oftt)
							countErrorTear += 1
							lastTime[lcData.muxChannel]=lcData.getDateTime()
							for j in range(lcHeader.numberOfChannels-1): # skip one set of channels
								lcData.readBlock(ifp1)
								lastTime[lcData.muxChannel]=lcData.getDateTime()
						else:
					
							# Find the next block with the same channel
							pos = ifp1.tell()
							channel = lcData.muxChannel
						
							tempData = LCDataBlock()
							tempData.readBlock(ifp1)
							while channel != tempData.muxChannel: tempData.readBlock(ifp1)
							tempTime = tempData.getDateTime()
							tempDiff = abs(convertToMSec(tempTime - expectedTime))
							ifp1.seek(pos)
							# back to the original block
						
							if (tempDiff - 2*convertToMSec(blockTimeDelta) < 2):
								# Stupid LCHEAPO BUG - Time gets screwed up every several months only on 1 block/ch
								print("%s%8d: Stupid LCHEAPO BUG #2.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
								countErrorTimeBug2 += 1
								t = expectedTime
								lcData.changeTime(t)
							else:
								# Check TWO blocks ahead with the same channel
								tempData = LCDataBlock()
								tempData.readBlock(ifp1)
								while channel != tempData.muxChannel: tempData.readBlock(ifp1)
								tempData.readBlock(ifp1)
								while channel != tempData.muxChannel: tempData.readBlock(ifp1)	
								tempTime = tempData.getDateTime()
								tempDiff = abs(convertToMSec(tempTime - expectedTime))
								ifp1.seek(pos)
								# back to the original block
							
								if (tempDiff - 3*convertToMSec(blockTimeDelta) < 2):
									# Stupid LCHEAPO BUG - Time gets screwed up every several months only on 1 block/ch
									print("%s%8d: Stupid LCHEAPO BUG #2b.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
									countErrorTimeBug2 += 1
									t = expectedTime
									lcData.changeTime(t)
								else:
									# Check THREE blocks ahead with the same channel
									tempData = LCDataBlock()
									tempData.readBlock(ifp1)
									while channel != tempData.muxChannel: tempData.readBlock(ifp1)
									tempData.readBlock(ifp1)
									while channel != tempData.muxChannel: tempData.readBlock(ifp1)	
									tempData.readBlock(ifp1)
									while channel != tempData.muxChannel: tempData.readBlock(ifp1)	
									tempTime = tempData.getDateTime()
									tempDiff = abs(convertToMSec(tempTime - expectedTime))
									ifp1.seek(pos)
									# back to the original block
							
									if (tempDiff - 4*convertToMSec(blockTimeDelta) < 2):
										# Stupid LCHEAPO BUG - Time gets screwed up every several months only on 1 block/ch
										print("%s%8d: Stupid LCHEAPO BUG #2c.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
										countErrorTimeBug2 += 1
										t = expectedTime
										lcData.changeTime(t)
									else:
										# Time tear (leave the time stamp alone - do not fix it!)
										txt="%8d: Time Tear in Data.   CH%d Expected Time: %s, Got: %s" % (currBlock, lcData.muxChannel,expectedTime, t)
										print(printHeader+txt)
										print(printHeader+txt,file=oftt)
										countErrorTear += 1
					else:
						# Stupid LCHEAPO BUG - A second is dropped then picked up on the next block.
						if lastBUG1s[0] == currBlock-500:
							if startBUG3<0:
								print("%s%8d: Stupid LCHEAPO BUG #3. BUG #1s repeating at 500-block intervals" % (printHeader,currBlock))
								startBUG3=currBlock
								printHeader='          '
						else:
							print("%s%8d: Stupid LCHEAPO BUG #1. CH%d Expected Time: %s, Got: %s " % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
						countErrorTimeBug1 += 1
						t = expectedTime
						lcData.changeTime(t)
						lastBUG1s.pop(0)	# FIFO: remove first element and add new last one
						lastBUG1s.append(currBlock);
			else:
				if args.forceTime & (consecIdentTimeErrors>0):
					print("%d blocks" % consecIdentTimeErrors)
					consecIdentTimeErrors=0
			inGap_counter=0    
		# Write out the block of data and report status (if necessary)
		if not args.dryrun:
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
		previousU1=lcData.U1
		previousU2=lcData.U2
	
	if args.forceTime:
		message="  Finished at block {:d} ({:d} time errors FORCEABLY corrected)".format(i,countErrorTear)
	else:
		message="  Finished at block {:d} ({:d} BUG1s, {:d} BUG2s, {:d} Time Tears, {:d} unexpected header values)".format( 
					i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr)
	print(message)
	
	if responseQ:
		responseQ.put((i, lastBlock+1, countErrorTimeBug1, countErrorTear))

	# ----------------------------------------------------------------------
	# Copy over the directory entries and modify the block time to correspond
	# to the actual time in the data block.
	# ----------------------------------------------------------------------

	# Open the output file for reading in the block data
	if not args.dryrun:
		ifp2 = open(outfilename, 'r')
	else:
		ifp2 = open(inFilename, 'r') # read data info from input file, since output file doesn't exist
	lcData2 = LCDataBlock()

	# Seek the directory location
	lcDir.seekBlock(ifp1, lcHeader.dirStart)
	if not args.dryrun:
		lcDir.seekBlock(ofp1, lcHeader.dirStart)
	
	# If quit early, correct the number of directory values in the  header
	if quitEarly:
		print("SHOULD CHANGE THE NUMBER OF DIRECTORY ENTRIES (on seekBlock in next Part?)")

	# Copy directory but change the time to correspond to the time in the data block.
	# The file pointer ifp2 points to the data block.
	if verbosity:
		print("COPYING/CORRECTING DIRECTORY")
		print(" DIR# |    BLOCK# | DIRTIME                    | BLOCKTIME                | DIFF (SECS)")
		print(" -----+-----------+----------------------------+--------------------------+------------")
	for i in range(0, lcHeader.dirCount):
		lcDir.readDirEntry(ifp1)
		if verbosity:
			print(" %4d | %9d | %-26s |" % (i+1,lcDir.blockNumber,lcDir.getDateTime()),end='')
		if lcDir.blockNumber > lastBlock :
			print("\nDIR%d, BLOCK%d IS BEYOND THE END OF FILE!" % (i+1,lcDir.blockNumber))
			if not args.dryrun:
				print("REDUCING NUMBER OF DIRECTORY ENTRIES IN HEADER FROM %d TO %d" % (lcHeader.dirCount,i))
				lcHeader.dirCount=i
				lcHeader.seekHeaderPosition(ofp1)
				lcHeader.writeHeader(ofp1)
			else:
				print("IF THIS WASN'T A DRY RUN, WOULD REDUCE THE NUMBER OF DIRECTORY ENTRIES FROM %d TO %d" % (lcHeader.dirCount,i))
			print("QUITTING")
			break
		lcData2.seekBlock(ifp2, lcDir.blockNumber)
		lcData2.readBlock(ifp2)
		blockTime = lcData2.getDateTime()
		if verbosity:
			diff = abs(convertToMSec(blockTime-lcDir.getDateTime()))
			if diff>1:
				print(" %-26s | %14.1f" % (blockTime,diff/1000))
			else:
				print(" SAME                     |   0")
		lcDir.changeTime(blockTime)
		if not args.dryrun:
			lcDir.writeDirEntry(ofp1)
		if stopProcess(commandQ):
			return



	# -----------------------
	# Close all the files
	# -----------------------
	if not args.dryrun:
		ofp1.close()
		ifp2.close()
	oftt.close()
	ifp1.close()

	if countErrorTear==0:
		os.remove(fname_timetears);

	#------------------------------------
	# make JSON file with run information
	#------------------------------------
	application={'comment':"Fixes standard LCHEAPO bugs, run before lc2ms",
		'name':"lcFix.py",
		'version':versionString}
	execution=  {'commandline':str(sys.argv),
		'comment':'',
		'date': startTimeStr,
		'messages':message,
		'parameters':{},
		'return_code':{}}
	tree={"steps":[{"0":{'application':application,'execution':execution}}]}
	json.dumps(tree);	# For testing
	fp=open(root+"lcFix.json","w")
	json.dump(tree,fp);	# For Real
	fp.close
	
	return countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr
	
# ----------------------------------------------------------------------------------
# Check for script invocation (run 'main' if the script is not imported as a module)
# ----------------------------------------------------------------------------------
if __name__ ==  '__main__':
    args = getOptions()
    
    commandQ=Queue.Queue(0)
    responseQ = Queue.Queue(0)
    main(args, commandQ, responseQ)
