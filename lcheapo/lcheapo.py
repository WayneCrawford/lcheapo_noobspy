#!/usr/bin/python2.7
"lcheapo.py --  Data access for lcheapo files"

import sys
import datetime
import struct
import string
import os

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME     = "lcheapo.py"
VERSION          = "0.3.0"
HEADER_START     = 2
#HEADER_START     = 8
BLOCK_SIZE       = 512

##############################################################################
# Class LCCommon
##############################################################################
class LCCommon:
    def __init__(self):
        (self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year) = (0,0,0,0,1,1,2000)
    
    def fixYear(self, year):
        "Change year from 2 to 4 digits."
        if (0 <= year < 50):
            year += 2000
        elif (50 < year < 100):
            year += 1900
        return year

    def getDateTime(self):
        "Convert the year:day:month:hour:minute:second.msec value to a datetime object."
        try: 
            return datetime.datetime(self.fixYear(self.year), self.month, self.day, self.hour, self.minute, self.second, self.msec*1000)
        except:
            return datetime.datetime(1900, 1, 1, 0, 0, 0, 0)  # Return a bogus date

    def changeTime(self, tm):
        "Change the local values to correspond to the datetime.datetime object passed in to the function."
        if (tm.year < 2000):
            self.year = tm.year - 1900
        else:
            self.year = tm.year - 2000

        self.month = tm.month
        self.day = tm.day
        self.hour = tm.hour
        self.minute = tm.minute
        self.second = tm.second
        self.msec = int (tm.microsecond / 1000)
        
        
    def getRealSampleRate(self, sampleRate):
        "Fix a bug in the sample rate."
        if (sampleRate < 61):
            return 31.25
        elif (sampleRate < 125):
            return 62.50
        return float(sampleRate)

    def determineLastBlock (self, fp):
        "Determine the last full block in the file."
        currentPos = fp.tell()
        fp.seek(-1,2)
        lastBlock = int (fp.tell() / BLOCK_SIZE)
        if currentPos % BLOCK_SIZE != 0:
            lastBlock -= 1;
        fp.seek(currentPos, 0)
        return lastBlock

    def seekBlock(self, fp, block):
        "Go to a particular block in the file."
        fp.seek(block * BLOCK_SIZE, os.SEEK_SET)
        

##############################################################################
# Class LCUserData
##############################################################################
class LCUserData (LCCommon):
    "Read/Write the user data section of a LCheapo file."
    def __init__(self):
        self.userData = ""

    def seekUserDataPosition(self, fp):
        "Move the file pointer to the user data position."
        fp.seek(0, os.SEEK_SET)

    def isValidData(self):
        if self.userData.find("LCHEAPO")  != 0:
            return False
        else:
            return True
    
    def readData(self, fp):
        self.userData = fp.read(2048)

    def writeData(self, fp):
        # ------ NOT FINISHED ------
        fp.write(self.userData)
        

##############################################################################
# Class LCDiskHeader
##############################################################################
class LCDiskHeader (LCCommon):
    "Read/Write values of an LCheapo disk header."
    def __init__(self):
        pass

    def fixDiskSizeBug (self):
        "Fix an old bug which doubled the disk size."
        self.diskSize /= 2

    def seekHeaderPosition(self, fp):
        "Move the file pointer to the standard header position."
        fp.seek(HEADER_START*BLOCK_SIZE,os.SEEK_SET)
        
    def readHeader(self, fp):
        self.seekHeaderPosition(fp)
        "Read an LCheapo disk header (packed big endian format)."
        (self.writeBlock, self.writeByte, self.readBlock, self.readByte) = struct.unpack('>LHLH', fp.read(12))
        (self.dirStart, self.dirSize, self.dirBlock, self.dirCount) = struct.unpack('>4L', fp.read(16))
        (self.slowStart, self.slowSize, self.slowBlock, self.slowByte) = struct.unpack('>4L', fp.read(16))
        (self.logStart, self.logSize, self.logBlock, self.logByte) = struct.unpack('>4L', fp.read(16))
        (self.dataStart, self.diskNumber) = struct.unpack('>LH', fp.read(6))
        (self.softwareVersion, self.description) = struct.unpack('>10s80s', fp.read(90))
        (self.sampleRate, self.startChannel, self.numberOfChannels) = struct.unpack('>3H', fp.read(6))
        (self.slowDataRate, self.slowStartChannel, self.slowNumberOfChannels) = struct.unpack('>3H', fp.read(6))
        (self.dataType, self.diskSize, self.ramSize, self.numberOfWindows) = struct.unpack('>4H', fp.read(8))
            
        # Python strings do not terminate on '\0', therefore, do this manually.
        self.softwareVersion = string.split(self.softwareVersion, '\0')[0]
        self.description = string.split(self.description, '\0')[0]

        # Additions which cannot be written back out
        self.realSampleRate = self.getRealSampleRate(self.sampleRate)
        self.dataTypeString = "Unknown Compression"
        if self.dataType >= 0 and self.dataType <= 3:
            self.dataTypeString = ("Uncompressed (16-Bit)",  "Compressed (16-Bit)",
                                     "Uncompressed (24-Bit)",  "Compressed (24-Bit)")[self.dataType]

    def writeHeader(self, fp):
        "Write an LCheapo disk header (packed big endian format)."
        fp.write(struct.pack('>LHLH', self.writeBlock, self.writeByte, self.readBlock, self.readByte))
        fp.write(struct.pack('>4L', self.dirStart, self.dirSize, self.dirBlock, self.dirCount))
        fp.write(struct.pack('>4L', self.slowStart, self.slowSize, self.slowBlock, self.slowByte))
        fp.write(struct.pack('>4L', self.logStart, self.logSize, self.logBlock, self.logByte))
        fp.write(struct.pack('>LH', self.dataStart, self.diskNumber))
        fp.write(struct.pack('>10s80s', self.softwareVersion, self.description))
        fp.write(struct.pack('>3H', self.sampleRate, self.startChannel, self.numberOfChannels))
        fp.write(struct.pack('>3H', self.slowDataRate, self.slowStartChannel, self.slowNumberOfChannels))
        fp.write(struct.pack('>4H', self.dataType, self.diskSize, self.ramSize, self.numberOfWindows))

    def printHeader(self):
        "Print the disk header information."
        print "\n\n"
        print "==========================="
        print "Disk Header"
        print "===========================\n"
        print "Field Name                 Contents"
        print "----------                 --------"
        print "Write Block            %12d (Next block to write)" % self.writeBlock
        print "Write Byte             %12d (Next byte to write)" % self.writeByte
        print "Read Block             %12d (Unused)" % self.readBlock
        print "Read Byte              %12d (Unused)" % self.readByte

        print "\n==== Dir Info ===="
        print "Dir Start              %12d (Dir start block)" % self.dirStart
        print "Dir Size               %12d (Max Dir entries)" % self.dirSize
        print "Dir Block              %12d (Next Dir block)"  % self.dirBlock
        print "Dir Count              %12d (Total Dir entries)" % self.dirCount

        print "\n==== Slow Data Storage ===="
        print "Slow Start             %12d (Slow data start block)" % self.slowStart
        print "Slow Size              %12d (Slow data size in blocks)" % self.slowSize
        print "Slow Block             %12d (Next block number to write)" % self.slowBlock
        print "Slow Byte              %12d (Next byte number to write)" % self.slowByte

        print "\n==== Log Data Info ===="
        print "Log Start              %12d (Log data start block)" % self.logStart
        print "Log Size               %12d (Log size in blocks)" % self.logSize
        print "Log Block              %12d (Next block number to write)" % self.logBlock
        print "Log Byte               %12d (Next byte number to write)" % self.logByte

        print "\n==== General Information ===="
        print "Data Start             %12d (Normal data start block)" % self.dataStart
        print "Disk Number            %12d" % self.diskNumber
        print "Software Version                  %s" % self.softwareVersion
        print "Description                       %s" % self.description
        print "Sample Rate            %12.2f Hz (written as %d Hz)" % (self.realSampleRate, self.sampleRate)
        print "Start Channel          %12d" % self.startChannel
        print "Number Of Channels     %12d" % self.numberOfChannels
        print "Slow Data Rate         %12d (Unused)" % self.slowDataRate
        print "Slow Start Channel     %12d (Unused)" % self.slowStartChannel
        print "Slow Num Of Channels   %12d (Unused)" % self.slowNumberOfChannels

        # Determine data type
        print "Data Type              %12d [%s]" % (self.dataType, self.dataTypeString)
        print "Disk Size              %12d GB" % self.diskSize
        print "RAM Size               %12d MB" % self.ramSize
        print "Number Of windows      %12d (Unused)" % self.numberOfWindows
        

##############################################################################
# Class LCDirEntry
##############################################################################
class LCDirEntry (LCCommon):
    "Read/Write a single directory entry from an LCheapo file."
    def __init__(self):
        pass

    def readDirEntry(self, fp):
        "Read an LCheapo directory entry (packed big endian format)"
        (self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year) = struct.unpack('>HBBBBBB', fp.read(8))
        (self.blockNumber, self.recordLength, self.sampleRate, self.numBlocks) = struct.unpack('>2L2H', fp.read(12))
        (self.flag, self.muxChannel) = struct.unpack('>2B', fp.read(2))
        self.U1 = struct.unpack('>10B', fp.read(10)) # Unused

    def writeDirEntry(self, fp):
        "Write an LCheapo directory entry (packed big endian format)"
        timeData = struct.pack('>HBBBBBB', self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year)
        flagData = struct.pack('>2L2H2B', self.blockNumber, self.recordLength, self.sampleRate, self.numBlocks, self.flag, self.muxChannel)
        uData    = struct.pack('>10B', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)  #Self.U1 does not work?
        fp.write(timeData)
        fp.write(flagData)
        fp.write(uData)

    def __str__(self):
        "Create string of directory entry (in short format)."
        return "{:26s} Ch:{:02d} {:7.2f}Hz     {:12d} {:12d} {:12d} Flg:0x{:02x}".format\
               (str(self.getDateTime()), self.muxChannel, self.getRealSampleRate(self.sampleRate),
                self.blockNumber, self.numBlocks, self.recordLength, self.flag)
#        return "%26s Ch:%02d %7.2fHz     %12d %12d %12d Flg:0x%02x" % \
#               (str(self.getDateTime()), self.muxChannel, self.getRealSampleRate(self.sampleRate),
#                self.blockNumber, self.numBlocks, self.recordLength, self.flag)


##############################################################################
# Class LCDataBlock
##############################################################################
class LCDataBlock (LCCommon):
    "Read/Write a data block in the LCheapo file."
    def __init__(self):
        pass

    def readBlock(self, fp):
        "Read a block of LCheapo data from the specified pointer."
        (self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year) = struct.unpack('>HBBBBBB', fp.read(8))
        (self.blockFlag, self.muxChannel, self.numberOfSamples) = struct.unpack('>BBH', fp.read(4))
        (self.U1, self.U2) = struct.unpack('>BB', fp.read(2)) # 2 Undocumented Bytes: U1=Flag=3 & U2=SampleCount=166
        self.data = fp.read(498)

    def writeBlock(self, fp):
        "Write a block of LCheapo data to the specified pointer."
        timeData = struct.pack('>HBBBBBB', self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year)
        flagData = struct.pack('>BBH', self.blockFlag, self.muxChannel, self.numberOfSamples)
        uData    = struct.pack('>BB', self.U1, self.U2)
        fp.write(timeData)
        fp.write(flagData)
        fp.write(uData)
        fp.write(self.data)

    def printHexDumpOfHeader(self, annotated = False):
        "Print out the data header in hexidecimal format."
        if annotated:
            print "msec:%04x sec:%02x min:%02x hour:%02x day:%02x month:%02x year:%02x" % (self.msec, self.second, self.minute,
                                                                                           self.hour, self.day, self.month, self.year),
            print "Flag:%02x Chan:%02x Samples:%04x" % (self.blockFlag, self.muxChannel, self.numberOfSamples)
        else:
            print "%04x%02x%02x %02x%02x%02x%02x" % (self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year),
            print "%02x%02x%04x" % (self.blockFlag, self.muxChannel, self.numberOfSamples)
        
    def printDecimalDumpOfHeader(self, annotated = False):
        "Print out the data header in decimal format."
        if annotated:
            print "msec:%4d sec:%02d min:%02d hour:%02d day:%02d month:%02d year:%02d" % (self.msec, self.second, self.minute,
                                                                                         self.hour, self.day, self.month, self.year),
            print "Flag:%03d Chan:%02d Samples:%4d" % (self.blockFlag, self.muxChannel, self.numberOfSamples)
        else:
            print "%4d %02d %02d %02d %02d %02d %02d" % (self.msec, self.second, self.minute, self.hour, self.day, self.month, self.year),
            print "%03d %02d %4d" % (self.blockFlag, self.muxChannel, self.numberOfSamples)

    def prettyPrintHeader(self, annotated = False):
        "Print out the data header in pretty format."
        if annotated:
            print "DateTime:%02d/%02d/%02d-%02d:%02d:%02d.%03d " % (self.year, self.month, self.day,
            														self.hour, self.minute, self.second, self.msec),
            print "Flag:%03d Chan:%02d Samples:%4d U1:%03d U2:%03d" % (self.blockFlag, self.muxChannel, self.numberOfSamples, self.U1, self.U2)
        else:
            print "%02d/%02d/%02d-%02d:%02d:%02d.%03d " % (self.year, self.month, self.day,self.hour, self.minute, self.second, self.msec),
            print "F%03d CH%02d %4d samps U1=%03d U2=%03d" % (self.blockFlag, self.muxChannel, self.numberOfSamples, self.U1, self.U2)

    def convertDataTo24BitValues(self):
        "Convert the data block into a list of 24-bit values."
        data = [x*(1<<16) + y*(1<<8) + z for x,y,z in [struct.unpack(">bBB", self.data[x:x+3]) for x in range(0,498,3)]]
        return data
    
    def printHexDumpOfData(self):
        "Print out the data block in hexidecimal format."
        count = 0
        for i in struct.unpack(">498B", self.data):
            sys.stdout.write("%02x" % i)
            count += 1
            if count % 3 == 0: sys.stdout.write("  ")
            if count % 30 == 0: sys.stdout.write("\n")
        sys.stdout.write("\n")

    def printDecimalDumpOfData(self):
        "Print out the data block in decimal format."
        count = 0
        data = self.convertDataTo24BitValues()
        for i in data:
            sys.stdout.write("%8d " % i)
            count += 1
            if count % 8 == 0: sys.stdout.write("\n")
        sys.stdout.write("\n")
        
    def __str__(self):
        return "CH:%d  Samples:%3d  Date:%02d-%02d-%02d %02d:%02d:%02d.%04d" % (self.muxChannel, self.numberOfSamples,
                                                                                self.year, self.month, self.day, self.hour,
                                                                                self.minute, self.second, self.msec)


##############################################################################
# Name          : main
# Purpose       : Main program
# Inputs        : non
# Outputs       : none
# Bidirectional : none
# Returns       : 0-Ok, 1-Error
# Notes         : -
##############################################################################
def main():
    "Main Program"
    print "lcheapo.py is not a runnable program."
    return 0


# ----------------------------------------------------------------------------------
# Check for script invocation (run 'main' if the script is not imported as a module)
# ----------------------------------------------------------------------------------
if __name__ ==  '__main__':
    main()
