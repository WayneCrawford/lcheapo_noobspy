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
import copy         # for deepcopy of argparse dictionary
import logging      # for logging information
#import datetime

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
versionString="0.63"
VERSIONS = """    VERSIONS
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
    0.52:    
      - The JSON file is ALWAYS named process-steps.json
      - If there is already a process-steps.json, the new information is appended to it
    0.6:    
      - If multiple files specified, assume all are sections of same instrument
        file, add header from first file to all others, output names include
        timestamp of start of data
      - If there is already a process-steps.json, the new information is appended to it
    0.61:    
      - Corrected process-steps.json to have steps as list, not dictionary
    0.62:    
      - Fixed bug with "warnings" variable
    0.63:    
      - Fixed bug making last directory entry for originally headerless files
    NOT YET:
      - Force non-time header values
        Test to make sure first file has header, and subsequent don't (requires new
        routine isHeader in lcheapo.py)
        If first file doesn't have header, allow header creation (requires new routine
        makeHeader in lcheapo.py)
        Change directory entry creation to create a new one if original header did'nt
        have enough directory entries
        
"""
warnings=0  # count # of warnings
        
##############################################################################
# Name      : getOptions
# Purpose     : To obtain the command line options (if any are given)
# Inputs    : none
# Outputs     : none
# Bidirectional : none
# Returns     : 
# Notes     : Uses the optparse library functions
##############################################################################
def getOptions():
  "Parse user passed options and parameters."
  
  parser = argparse.ArgumentParser(description="Fix common LCHEAPO bugs",
    epilog=textwrap.dedent("""\
  =========================================================================
  The LCHEAPO bugs are:\n\
    1: A second is dropped then picked up on the next block.
    2: Time tag is wrong for up to 3 consecutive blocks
    
  Outputs (for input filename root.*):
    root.fix.lch: fixed data
    root.fix.txt: information about fixes applied
    root.fix.timetears.txt: time tear lines (if any) 
  Notes:
    - TIME TEARS MUST BE ELIMINATED BEFORE FURTHER PROCESSING!!!
    - Sometimes (if there were 3+ consecutive bad times/channel, but not
      an overall time tear), rerunning this program on the
      output will get rid of leftover "time tears"
    - The last data block is always ignored, because this block sometimes
      causes problems
  Recommendations:
    - Name your inputfile STA.lch, where STA is the station name
    - After running, and once all time tears have been hand-corrected,
      re-run %prog -v --dryrun on the fixed file to verify
      that there are no remaining errors and to get information
      about the directory header.  
  Example: 
    - for an LCHEAPO file named RR38.lch:
      > lcFix.py RR38.raw.lch  > RR38.fix.txt
      > lcFix.py -v --dryrun RR38.fix.lch > RR38-verify.txt
"""),
  formatter_class=argparse.RawDescriptionHelpFormatter)
  
  
  parser.add_argument("infiles", metavar="inFileName", nargs='+', help="Input filename(s)")
  parser.add_argument("--version", action='version', version='%(prog)s {:s}'.format(versionString))
  parser.add_argument("-v", "--verbose", dest="verbosity",action = "count", default=0,
            help="Be verbose (-v = kind of, -vv = very")
  parser.add_argument("-d", "--dryrun", dest="dryrun",action = "store_true", default=False,
            help="Dry Run: do not output fixed LCHEAPO file")
  parser.add_argument("-r", "--root", dest="outFileRoot",default='',help="specify root output filename")
  parser.add_argument("-F", "--forceTimes", dest="forceTime",action = "store_true", default=False,
            help="Force times to be consecutive (use only if time tear identified but proven false by synchronizing events before and after)")
  #   parser.add_argument("-o", "--outfile", dest="outfile",
  #             help="Force output (fixed) file name (only works if one input file)")
  args = parser.parse_args()

  #parameters=vars(args)
  #print(parameters)

  #sys.exit(0)
  
  return args


##############################################################################
# Name      : getTimeDelta
# Purpose     : Convert a floating point number, representing a time offset in
#         seconds, into a datetime.timedelta object.
#         corresponding to the number of milliseconds.
# Inputs    : floatTimeInSec  - Floating point number holding the number of
#                   seconds.  The fractional part will correspond
#                   to milliseconds.
# Outputs     : none
# Bidirectional : none
# Returns     : A datetime.timedelta object.
# Notes     : none
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
# Name        : makeProcessStepsFile
# Purpose     : Make or append to a JSON file used by all datafile
#               processing programs.  This file is named "process-steps.json"
# Inputs      : startTimeStr  - A string containing the program start time
#               parameters - a list of program parameters
#               inFiles - a list of input files
#               outFiles - a list of output files
#               msgs - a list of messages about the data processing (one per input
#                      file)
#               returnCode: 0 for no error, others not yet defined
# Outputs     : file process-steps.json
# Bidirectional : none
# Returns     : none
# Notes       : none
##############################################################################
def makeProcessStepsFile(startTimeStr,parameters,inFiles,outFiles,msgs,returnCode) :
  application={'comment':"Fix common bugs in LCHEAPO data files",
    'name':"lcFix.py",
    'version':versionString}
  #execution=  {'commandline':str(sys.argv),
  execution=  {'commandline':" ".join(sys.argv),
    'comment':'',
    'date': startTimeStr,
    'messages':msgs,
    'parameters':parameters,
    'input files':inFiles,
    'output files':outFiles,
    'return_code': returnCode}
  try:
    fp=open("process-steps.json","r")
  except:  # File not found
    #tree={"steps":[{"0":{'application':application,'execution':execution}}]}
    tree={"steps":[{'application':application,'execution':execution}]}
  else:   # File found
    tree=json.load(fp)
    if 'steps' in tree: 
      # Find lowest available step #
#       newkey='0'
#       while newkey in tree['steps'][0]:
#         newkey=str(int(newkey)+1)
#       tree['steps'][0][newkey]={'application':application,'execution':execution}
       tree['steps'].append({'application':application,'execution':execution})
    else:
      #tree['steps']=[{"0":{'application':application,'execution':execution}}]
      tree['steps']=[{'application':application,'execution':execution}]
    fp.close() 
  #json.dumps(tree);  # For testing
  fp=open("process-steps.json","w")
  json.dump(tree,fp,sort_keys=True, indent=2);  # For real
  fp.close

##############################################################################
# Name      : convertToMSec
# Purpose     : Convert a datetime.timedelta object into corresponding number
#         of milliseconds.
# Inputs    : tm   -  datetime.timedelta() object
# Outputs     : none
# Bidirectional : none
# Returns     : int  -  milliseconds
# Notes     : none
##############################################################################
def convertToMSec(tm):
  "Given a timedelta() object return the corresponding number of milliseconds."
  return ((tm.days * 86400) + (tm.seconds)) * 1000 + int (tm.microseconds/1000)

  
def stopProcess(commandQ):
  global warnings
  if not commandQ:
    return False
  try:
    if commandQ.get(0) == "Stop":
      logging.warning("RECEIVED 'STOP' MESSAGE")
      warnings+=1
      return True
  except Queue.Empty:
    pass
  
  return False

def endBUG3(startBlock,endBlock):
  global startBUG3
  if startBUG3 >=0:
    logging.info("%8d:  End LCHEAPO BUG #3 (started at %d)" % (endBlock, startBlock))
    global printHeader
    startBUG3=-1
    printHeader=''

def printFinalMessage(forceTime, iFiles, iBug1, iBug2, iTT, iWH)   :
  logging.info("=================================================================================================")
  if not forceTime:  # Standard case
    logging.info("Overall totals: {:d} files, {:d} BUG1s, {:d} BUG2s, {:d} Time Tears, {:d} unexpected header values".format(iFiles,iBug1,iBug2,iTT,iWH))
    if iBug1>0:
      logging.info("  BUG1= 1-second errors in time tag")
    if iBug2>0:
      logging.info("  BUG2= Other isolated errors in time tag")
    if iTT>0:
      logging.info("  Time Tear=Bad time tag (BUG1 or BUG2) for more than two consecutive samples.  Could be long")
      logging.info("      stretch of bad records or an offset in records (must be fixed)")

    # Make error message (and return code) if there are time tears
    if iTT>0:
      logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
      logging.warning("YOU HAVE {:d} TIME TEARS: YOU MUST ELIMINATE THEM BEFORE CONTINUING!!!".format(iTT))
      logging.warning('Use "lcdump.py OBSfile..raw.lch STARTBLOCK NUMBLOCKS" to look at suspect sections')
      logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
      sys.exit(-1)
  else:  # Forced time corrections
    logging.warning("FORCED TIME CORRECTIONS, NO EVALUATION OF BUG1s and BUG2s ")
    logging.warning("(should have run this on a previously fixed file with only false time tears left)")
    logging.warning("Overall totals: {:d} files, {:d} Forced corrections, {:d} unexpected header values".format(iFiles,iTT,iWH))
    
# ---------------------------------
# Find the first 0-channel block
# ---------------------------------
def findFirstMux0Block(firstBlock,ifp1) :
  lcData=LCDataBlock()
  lcData.seekBlock(ifp1,firstBlock)
  lcData.readBlock(ifp1)
  i=0
  while lcData.muxChannel != 0:
    i+=1
    lcData.readBlock(ifp1)
  return (firstBlock+i)

# ---------------------------------
def readLCHeader(ifp1) :
  lcHeader = LCDiskHeader()
  lcHeader.seekHeaderPosition(ifp1)
  lcHeader.readHeader(ifp1)
  firstInpBlock = lcHeader.dataStart
  return (lcHeader,lcHeader.dataStart)

# ---------------------------------
# Create the root of the output file name
# If the user specified one, use it
# If not, use the part of the input filename before the first '.'
# If there are multiple input files, append the data start time to the root
# ---------------------------------
def makeOutFileRoot(fname,numInFiles,userOutFileRoot,ifp1,firstBlock) :
  if len(userOutFileRoot)>0:
    outFileRoot = userOutFileRoot
  else:
    outFileRoot=fname.split('.')[0]
  if numInFiles > 1:
    # Add first time to outfile name
    lcData=LCDataBlock()
    lcData.seekBlock(ifp1,firstBlock)    # Step back one so that next read is here
    lcData.readBlock(ifp1)    # Read next block            
    t=lcData.getDateTime()
    timestring=t.strftime("%Y%m%dT%H%M%S")
    outFileRoot += '_' + timestring
  return outFileRoot

##############################################################################
# Name      : makeLogger
# Purpose     : Create a logger instance (allows us to send outputs to a file
#               and stdout, plus handle debugging, etc
# Inputs    : -
# Outputs     : -
# Bidirectional : -
# Returns     : -
# Notes     : -
##############################################################################
def makeLogger(fname) :
  # First create the file logger
  logging.basicConfig(filename=fname, level=logging.INFO,format='%(levelname)s %(message)s')
  # now the stdout logger
  sth=logging.StreamHandler(sys.stdout)
  sth.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
  sth.setLevel(logging.DEBUG)
  # now add the stdout handler to the original
  logging.getLogger().addHandler(sth)
  
##############################################################################
# Name      : main
# Purpose     : -
# Inputs    : -
# Outputs     : -
# Bidirectional : -
# Returns     : -
# Notes     : -
##############################################################################
def main():

      global warnings
      # Prepare variables
      iBug1=iBug2=iTT=iWH=iFiles=0
      msgs=[]
      outFiles=[]
      lcData = LCDataBlock()
      startTimeStr=datetime.datetime.strftime(datetime.datetime.utcnow(),'%Y-%m-%dT%H:%M:%SZ')
  
      # GET ARGUMENTS
      args = getOptions()  
      commandQ=Queue.Queue(0)
      responseQ = Queue.Queue(0)

      # SET UP TEXT OUTPUT FILE
      root = args.outFileRoot
      if len(root)==0:
            root=args.infiles[0].split('.')[0]
      makeLogger(root+'.fix.txt')
      #oftext=open(root+'.fix.txt','w')
 
      if args.dryrun:
            logging.info("DRY RUN: will not output a new file (useful for verifying that no errors remain)")
            if args.forceTime:
                logging.info("-F (forceTimes) IGNORED during dry run")
                args.forceTime=False
      # Loop through input files
      numInFiles=len(args.infiles)
      firstFile=True
      for fname in args.infiles:
            ifp1 = open(fname, 'r')
    
            # Find and copy the disk header
            if firstFile:    # First file, extract header
                  (lcHeader,firstInpBlock)=readLCHeader(ifp1)
                  if args.verbosity:
                        lcHeader.printHeader()
            else:
                  firstInpBlock=0    # dataBlocks will start at the very beginning
                  lcHeader.dirCount=0 # No header, so no directory entries
      
            logging.info('============== PROCESSING FILE %s =============' % (fname))

            # Determine last file block
            ifp1.seek(0,2)                # Seek end of file
            lastInpBlock=ifp1.tell()/512 - 1
    
            if stopProcess(commandQ):
              return

            # Adjust first block to correspond to first block with channel 0
            firstInpBlock=findFirstMux0Block(firstInpBlock,ifp1)
    
            outFileRoot=makeOutFileRoot(fname,numInFiles,args.outFileRoot,ifp1,firstInpBlock)
  
            # Process file
            (nBug1,nBug2,nTT,nWH,msg,ofname) = processInputFile(ifp1,fname,outFileRoot,lcHeader, firstInpBlock, lastInpBlock, firstFile, args,commandQ, responseQ)
            ifp1.close()
    
            # Update counters
            iBug1+=nBug1
            iBug2+=nBug2
            iTT+=nTT
            iWH+=nWH
            iFiles+=1
            msgs.append(msg)
            outFiles.append(ofname)
    
            firstFile=False
    
        # END OF INPUT FILES LOOP
    
      printFinalMessage(args.forceTime, iFiles, iBug1, iBug2, iTT, iWH)  

      if not args.dryrun:
            parameters=copy.deepcopy(vars(args))
            del parameters['infiles']
            if warnings==0:
                returnCode=0
            else:
                returnCode=2
            makeProcessStepsFile(startTimeStr,parameters,args.infiles,outFiles,msgs,0)

      #oftext.close()
      sys.exit(0)
  
##############################################################################
# Name      : processInputFile
# Purpose     : -
# Inputs    : -
# Outputs     : -
# Bidirectional : -
# Returns     : -
# Notes     : Was main() up to version 0.5: main now handles JSON file creation and multiple input files
##############################################################################
def processInputFile(ifp1, fname, outFileRoot, lcHeader, firstInpBlock, lastInpBlock, hasHeader, args, commandQ=None, responseQ=None):

    # Declare variables
    global startBUG3, printHeader, lcDir, warnings
    i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr= 0, 0, 0, 0, 0
    lastBUG1s=[0,0,0,0]
    printHeader=''
    startBUG3=-1
    inGap_counter=0
    previousMuxChannel=-1
    previousBlockFlag=73
    previousNumberOfSamples=166
    previousU1=3
    previousU2=166
    verbosity=args.verbosity
    consecIdentTimeErrors, oldDiff= 0,0  # Currently only used for Force Time option
    lcData = LCDataBlock()

    if not args.dryrun:
        #if args.outfile is None :
        outfilename=outFileRoot+".fix.lch"
        ofp1 = open(outfilename, 'w')
    fname_timetears=outFileRoot+'.fix.timetears.txt'
    oftt = open(fname_timetears,'w');

    # -----------------------------
    # Copy the disk header to the output file
    # -----------------------------
    if not args.dryrun:
        lcHeader.seekHeaderPosition(ofp1)
        lcHeader.writeHeader(ofp1)
    if stopProcess(commandQ):
        return

    blockTime = int ((166 * (1.0/lcHeader.realSampleRate)) * 1000)
    blockTimeDelta = datetime.timedelta(0, 0, 0, blockTime, 0, 0)

    # Grab the first time entries (one for each channel) and adjust them
    # so that they point an entire blockTimeDelta in the past.  This is done to
    # "prime the pump" so that we can add in the blockTimeDelta the first time we
    # use it.
    lcData.seekBlock(ifp1, firstInpBlock)
    lastTime = []
    for i in range (0, lcHeader.numberOfChannels):
        lcData.readBlock(ifp1)
        lastTime.append(lcData.getDateTime() - blockTimeDelta)

    ifp1.seek(0,2); # Go to the end
    lastAddress=ifp1.tell()
    # Back up to data start block
    lcData.seekBlock(ifp1, firstInpBlock)
    if not args.dryrun:
        if hasHeader:
            lcData.seekBlock(ofp1, firstInpBlock)
        else:
            lcData.seekBlock(ofp1, lcHeader.dataStart)

    #if verbosity:
    logging.info ("  data Blocks: first=%d, last=%d" % (firstInpBlock, lastInpBlock ))
    logging.info ("  PROCESSING FILE")

    # For every block, compare the expected and actual times.
    for i in range(firstInpBlock, lastInpBlock+1):
        lcData.readBlock(ifp1)
        currBlock=ifp1.tell()/512-1
        if startBUG3>=0 and currBlock>lastBUG1s[0]+500:
            endBUG3(startBUG3,currBlock)
        if i != currBlock:
            logging.info("Error: currBlock (%d) != i (%d)" % (currBlock,i))
        if verbosity > 1:  # Very verbose, print each block header
            logging.info("%8d(%d): " % (i,ifp1.tell()))
            #lcData.printDecimalDumpOfHeader(True)
            lcData.prettyPrintHeader()
        ###### USER-CREATED ZERO DATA BLOCK #############
        if (lcData.year==0 and lcData.month==0 and lcData.day==0):
            if inGap_counter==0 :
                t=lastTime[0] + blockTimeDelta
                bugStartBlock=currBlock
                bugStartDate=t
                logging.info("%s%8d: ZERO-FILLED DATA GAP Starts, filling headers" % (printHeader,currBlock))
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
                logging.info("             Data Gap: Setting CH%d time to %s   Block %d" % (lcData.muxChannel,t,currBlock))
            lcData.changeTime(t)
            bugEndDate=t
            inGap_counter += 1
        else: 
            ##### VERIFY NON-TIME HEADER VALUES ############
            if (lcData.blockFlag!=73) | (lcData.numberOfSamples!=166) | (lcData.U1!=3) | (lcData.U2!=166) :
                if (countUnexpectHdr < 100) :
                    logging.info("%s%8d: Unexpected non-time header values:" % (printHeader,currBlock))
                    lcData.prettyPrintHeader(True)
                elif (countUnexpectHdr == 100) :
                    logging.info("%s%8d: >100 Unexpected non-time headers: WON'T PRINT ANY MORE!" % (printHeader,currBlock))
                countUnexpectHdr+=1
            ##### VERIFY CHANNEL NUMBER ############
            if previousMuxChannel != -1 :
                predictedChannel=previousMuxChannel+1
                if predictedChannel>=lcHeader.numberOfChannels :
                    predictedChannel=0
                if lcData.muxChannel != predictedChannel :
                    if ((lcData.muxChannel > lcHeader.numberOfChannels) | (lcData.muxChannel < 0)):
                        logging.warning("%s%8d: WARNING: Channel = %d IS IMPOSSIBLE, setting to predicted %d" % (printHeader,currBlock,lcData.muxChannel,predictedChannel))
                        warnings+=1
                        lcData.muxChannel = predictedChannel
                    else:
                        logging.warning("%s%8d: WARNING: Channel = %d, predicted was %d" % (printHeader,currBlock,lcData.muxChannel,predictedChannel))
                        warnings+=1
            if inGap_counter>0:
                ###### END OF USER-CREATED ZERO DATA BLOCK #############
                logging.info("%s%8d: ZERO-FILLED DATA GAP Ends: %6d blocks (~%.1f seconds, from %s to %s)" % (
                    printHeader,currBlock-1, inGap_counter,(inGap_counter/lcHeader.numberOfChannels)*blockTime/1000.,
                    bugStartDate, bugEndDate))
            expectedTime = lastTime[lcData.muxChannel] + blockTimeDelta
            t = lcData.getDateTime()
            diff = abs(convertToMSec(t - expectedTime))
            if diff:
                if args.forceTime:
                  if (consecIdentTimeErrors>0) & (diff != oldDiff): # Starting a new time offset
                      logging.info("%d blocks" % consecIdentTimeErrors)
                      consecIdentTimeErrors=0
              
                  if consecIdentTimeErrors==0: # New time error or error offset
                    forceTimeErrorStr="%s%8d:  CH%d: %g-s offset FORCED to conform..." % (printHeader,currBlock,lcData.muxChannel,diff/1000.)
                  t = expectedTime
                  lcData.changeTime(t)
                  countErrorTear += 1  # Use time tear counter to count forced
                  consecIdentTimeErrors += 1  # Currently only used for forceTime
                  oldDiff=diff
                else:
                  if diff > 1100:
                    # Difference is greater than 1-second.  This could be a time tear or another
                    # lcheapo bug (bad time entry).
                    if inGap_counter > 0:
                      logStr="%s%8d:  CH%d: TIME=%s" % (printHeader,currBlock,lcData.muxChannel,lcData.getDateTime())
                      if convertToMSec(t - expectedTime) > 0:
                        txt= "  %.1f second time tear after gap!  YOUR DATA GAP IS PROBABLY %d blocks TOO SHORT" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
                      else:
                        txt= "  %.1f second time overlap after gap!  YOUR DATA GAP IS PROBABLY %d blocks TOO LONG" % (diff/1000., lcHeader.numberOfChannels*diff/blockTime)
                      logging.warning(logStr+printHeader+txt)
                      warnings+=1
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
                        logging.info("%s%8d: Stupid LCHEAPO BUG #2.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
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
                          logging.info("%s%8d: Stupid LCHEAPO BUG #2b.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
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
                            logging.info("%s%8d: Stupid LCHEAPO BUG #2c.  CH%d Expected Time: %s, Got: %s" % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
                            countErrorTimeBug2 += 1
                            t = expectedTime
                            lcData.changeTime(t)
                          else:
                            # Time tear (leave the time stamp alone - do not fix it!)
                            txt="%8d: Time Tear in Data.   CH%d Expected Time: %s, Got: %s" % (currBlock, lcData.muxChannel,expectedTime, t)
                            logging.warning(printHeader+txt)
                            warnings+=1
                            print(printHeader+txt,file=oftt)
                            countErrorTear += 1
                  else:
                    # Stupid LCHEAPO BUG - A second is dropped then picked up on the next block.
                    if lastBUG1s[0] == currBlock-500:
                      if startBUG3<0:
                        logging.info("%s%8d: Stupid LCHEAPO BUG #3. BUG #1s repeating at 500-block intervals" % (printHeader,currBlock))
                        startBUG3=currBlock
                        printHeader='      '
                    else:
                      logging.info("%s%8d: Stupid LCHEAPO BUG #1. CH%d Expected Time: %s, Got: %s " % (printHeader,currBlock,lcData.muxChannel,expectedTime, t))
                    countErrorTimeBug1 += 1
                    t = expectedTime
                    lcData.changeTime(t)
                    lastBUG1s.pop(0)  # FIFO: remove first element and add new last one
                    lastBUG1s.append(currBlock);
            else:
                if args.forceTime & (consecIdentTimeErrors>0):
                  logging.info(forceTimeErrorStr+"%d blocks" % consecIdentTimeErrors)
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
                responseQ.put((i, lastInpBlock, countErrorTimeBug1, countErrorTear))
      
        lastTime[lcData.muxChannel] = t
        previousMuxChannel=lcData.muxChannel
        previousBlockFlag=lcData.blockFlag
        previousNumberOfSamples=lcData.numberOfSamples
        previousU1=lcData.U1
        previousU2=lcData.U2
    # END LOOP THROUGH EVERY BLOCK  
    if args.forceTime:
            message="  {}=>{}: Finished at block {:d} ({:d} time errors FORCEABLY corrected)".format(fname,outfilename,i,countErrorTear)
    else:
            message="  {}=>{}: Finished at block {:d} ({:d} BUG1s, {:d} BUG2s, {:d} Time Tears, {:d} unexpected header values)".format( 
              fname,outfilename,i, countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr)
    logging.info(message)

    if responseQ:
        responseQ.put((i, lastInpBlock, countErrorTimeBug1, countErrorTear))

    # ----------------------------------------------------------------------
    # Copy over the directory entries and modify the block time to correspond
    # to the actual time in the data block.
    # ----------------------------------------------------------------------

    # Open the output datafile for reading
    if not args.dryrun:
        ofp_data = open(outfilename, 'r') # generally the output file
    else:
        ofp_data = open(inFilename, 'r') # if no output file, read block data from input file
    lcData2 = LCDataBlock()

    # Put both input and output file pointers to the directory (reads one and updates the other?)  
    if hasHeader: # In input file
        lcDir=LCDirEntry()
        lcDir.seekBlock(ifp1, lcHeader.dirStart)
    if not args.dryrun: # In output file
        lcDir.seekBlock(ofp1, lcHeader.dirStart)
  
    # Copy directory but change the time to correspond to the time in the data block.
    # ifp1 points to the start of the input file's directory
    # ofp1 points to the start of the output file's directory
    # ofp_data points to the output file's data block.
    if verbosity:
        if hasHeader:
          logging.info("  COPYING/CORRECTING DIRECTORY")
        else:
          logging.info("  CREATING DIRECTORY")
        logging.info("   DIR# |    BLOCK# | ORIG DIRTIME               | NEW DIRTIME (BLOCKTIME)      | DIFF (SECS)")
        logging.info("   -----+-----------+----------------------------+------------------------------+------------")
    iDir=0
    if hasHeader:
        lastOutBlock=lastInpBlock
    else:
        lastOutBlock=lastInpBlock+lcHeader.dataStart
    # LCHEAPO DIRECTORY ENTRIES ARE EVERY 14336 blocks BY DEFAULT
    DIRBLOCKS=14336
    # Loop through the directory
    while True:
        # If the input file had a directory, read in the next entry (or add one if we're beyond original end)
        if hasHeader:
            if iDir < lcHeader.dirCount:
                lcDir.readDirEntry(ifp1)
                origDirTime=lcDir.getDateTime()
            else:
                nextDirBlock=lcDir.blockNumber+lcDir.numBlocks
                if iDir<=lcHeader.dirSize and nextDirBlock <= lastOutBlock :
                    # ADD DIRECTORY ENTRIES
                    lcDir.blockNumber=lcDir.blockNumber+lcDir.numBlocks
                    origDirTime='None'
                else:
                    break
        # If it did not have a directory, make up the next entry
        else:
            lcDir.numBlocks=DIRBLOCKS
            nextDirBlock=lcHeader.dataStart + iDir*lcDir.numBlocks
            #print (iDir, lcHeader.dirSize, nextDirBlock,lcHeader.dataStart, lastOutBlock)
            if iDir < lcHeader.dirSize and nextDirBlock <= lastOutBlock:
                lcDir.blockNumber=nextDirBlock
                origDirTime='None'
            else:
                break
        verboselogtext="   %4d | %9d | %-26s |" % (iDir+1,lcDir.blockNumber,origDirTime)
        # Jump out if directory start block number is beyond end of file 
        if lcDir.blockNumber > lastOutBlock:
            if verbosity:
                logging.info(verboselogtext)
            break
            
        # Put the start time of the block pointed to by the directory entry into the directory entry
        if hasHeader or not args.dryrun:  # ofp_data has a header unless we're doing a dryrun on a headerless file
          lcData2.seekBlock(ofp_data, lcDir.blockNumber)
        else: # ofp_data is headerless
          lcData2.seekBlock(ofp_data, lcDir.blockNumber-lcHeader.dataStart)
        lcData2.readBlock(ofp_data)
        blockTime = lcData2.getDateTime()
        if verbosity:
          if hasHeader: # Compare directory times to corresponding block times
            diff = abs(convertToMSec(blockTime-lcDir.getDateTime()))
            #if diff>1:
            logging.info(verboselogtext+"   %-26s | %14.1f" % (blockTime,diff/1000))
            #else:
            #  logging.info("   %-26s | %-14d" % ('SAME',0))
          else:
              logging.info(verboselogtext+"   %-26s | %-14s" % (blockTime,"N/A"))
        lcDir.changeTime(blockTime)
        # If directory entry goes beyond end of data, write and break out
        if lcDir.blockNumber+lcDir.numBlocks>=lastOutBlock:
            lcDir.numBlocks=lastOutBlock-lcDir.blockNumber+1
            if not args.dryrun:
                lcDir.writeDirEntry(ofp1)
            iDir+=1
            break
        if not args.dryrun:
          lcDir.writeDirEntry(ofp1)        
        iDir+=1
        
    if iDir != lcHeader.dirCount :
        if hasHeader:
          if iDir < lcHeader.dirCount :
            logging.info("\n  DIR%d, LAST BLOCK (%d) IS BEYOND THE END OF FILE!" % (iDir+1,lcDir.blockNumber+lcDir.numBlocks))
            logging.info("  REDUCING NUMBER OF DIRECTORY ENTRIES IN HEADER FROM %d TO %d" % (lcHeader.dirCount,iDir))
          else:
            logging.info("\n  ADDED %d DIRECTORY ENTRIES TO COVER END OF DATA!" % (iDir-lcHeader.dirCount))
        else:
          logging.info("  %d DIRECTORY ENTRIES CREATED" % iDir)
        if not args.dryrun:
          lcHeader.dirCount=iDir
          lcHeader.seekHeaderPosition(ofp1)
          lcHeader.writeHeader(ofp1)
    if stopProcess(commandQ):
        return



    # -----------------------
    # Close all the files
    # -----------------------
    if not args.dryrun:
        ofp1.close()
        ofp_data.close()
    oftt.close()

    if countErrorTear==0:
        os.remove(fname_timetears);
  
    return countErrorTimeBug1, countErrorTimeBug2, countErrorTear, countUnexpectHdr, message, outfilename
  
# ----------------------------------------------------------------------------------
# Check for script invocation (run 'main' if the script is not imported as a module)
# ----------------------------------------------------------------------------------
if __name__ ==  '__main__':
  main()
