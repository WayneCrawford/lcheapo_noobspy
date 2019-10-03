#!/usr/bin/python2.7

from __future__ import print_function
import sys
from optparse import OptionParser
from lcheapo import *
#import process_step
from datetime import datetime,timedelta

# ------------------------------------
# Global Variable Declarations
# ------------------------------------
PROGRAM_NAME     = "lcheader"
VERSION          = "1.0"
bytes_per_block=512
dirs_per_block=16
blocks_per_dirEntry=14336
samples_per_block=166

##############################################################################
def __getOptions():
    "Parse user passed options and parameters."
    usageStr = "%prog [-h] [-V]"
    parser = OptionParser(usageStr)
    parser.add_option("-V", "--version", dest="version",
                      action = "store_true", help="Display Program Version", default=False)
    parser.add_option("-n", "--noDirectory", action = "store_true",
                      help="Print disk header", default=False)
    parser.add_option("--dry_run", action = "store_true",
                      help="don't save to disk", default=False)
    parser.add_option("-i", "--input_file",help="input header file to modify")
    (opts, arguments) = parser.parse_args()
    
    # Get the filename (the arguments)
    if opts.version:
        print("{} - Version: {}".format(PROGRAM_NAME, VERSION))
        sys.exit(0)
    return opts

##############################################################################
def main(opts):
    """main function"""
    if opts.input_file:
        h=__read_header(opts.input_file)
    else:
        h=__generic_header()
    h,params=__get_parameters(h)
    if opts.dry_run:
        return(2)
    with open(params['filename_prefix']+'.header.raw.lch', 'w') as fp:
        # Pre-blank file
        if opts.noDirectory:
            fp.write(b'\x00'*bytes_per_block*h.dirStart)
        else:
            fp.write(b'\x00'*bytes_per_block*h.dataStart)
            
        # Write header
        h.seekHeaderPosition(fp)
        h.writeHeader(fp)
        if opts.noDirectory:
            return(0)

        # Write directory
        d=__prep_dirEntry(h.sampleRate)
        dt=params['wake_time']
        dirCount=0
        samples_per_dirEntry=samples_per_block*blocks_per_dirEntry/h.numberOfChannels
        dir_timeoffset=timedelta(seconds=samples_per_dirEntry/h.sampleRate)
        blocknum=h.dataStart
        d.seekBlock(fp, h.dirStart)
        while dt<params['end_time']:
            d=__make_dirEntry(d,blocknum,dt)
            d.writeDirEntry(fp)
            dt+=dir_timeoffset
            dirCount=dirCount+1
            blocknum+=blocks_per_dirEntry
        h.dirCount=dirCount
        h.seekHeaderPosition(fp)
        h.writeHeader(fp)
    
    #process_step.write()
    return(0)
            
##############################################################################
def __get_parameters(h):
    """Imitate LCHEAPO parameter menu, return values"""
    params=dict(wake_time=datetime(2017,01,01,05,00,00),
                end_time= datetime(2018,01,01,05,00,00),
                filename_prefix="generic"
            )
    while not __validate_params(h,params):
        h.description =             __get_string("Description (Cruise_InstModel_SN_Site)",
                                            h.description)
        h.sampleRate =              __get_int("Sample Rate",h.sampleRate,\
                                            [31,62,125,250,500,1000,2000,4000])
        h.realSampleRate =          h.getRealSampleRate(h.sampleRate)
        h.numberOfChannels =        __get_int("Number of Channels",h.numberOfChannels,
                                            [1,2,3,4])

        params['wake_time'] =       __get_datetime("Wake Time",params['wake_time'])
        if params['end_time']<params['wake_time']:
            params['end_time']=params['wake_time']+timedelta(days=365)
        params['end_time'] =        __get_datetime("End Time",params['end_time'])
        params['filename_prefix'] = __get_string("Output Filename Prefix",
                                            params['filename_prefix'])

    datalen=params['end_time']-params['wake_time']
    datalen_seconds=datalen.days*86400+datalen.seconds+datalen.microseconds/1.e6
    datalen_blocks=int(datalen_seconds*h.sampleRate/samples_per_block)*h.numberOfChannels    
    h.writeBlock=h.dataStart + datalen_blocks
    return h,params

##############################################################################
def __validate_params(h,params):
    """Validate header parameters"""
    print('**** PARAMETERS ****')
    print('            Description: {}'.format(h.description))
    print('            Sample Rate: {:d} ({:.1f} real)'.format(h.sampleRate,h.realSampleRate))
    print('     Number of Channels: {}'.format(h.numberOfChannels))
    print('              Wake Time: {}'.format(params['wake_time'].isoformat()))
    print('               End Time: {}'.format(params['end_time'].isoformat()))
    print('        Output Filename: {}'.format(params['filename_prefix']+
                                        '.header.raw.lch'))
    resp=raw_input('Is this acceptable? [y/N]: ')
    if not resp:
        return False
    if resp[0].lower()=='y':
        return True
    return False
    
##############################################################################
def __read_header(filename):
    """Read in header from an LCHEAPO file"""
    h = LCDiskHeader()
    with open(filename,'r') as fp:
        h.seekHeaderPosition(fp)
        h.readHeader(fp)
    return h

##############################################################################
def __generic_header():
    """Create a generic lcheapo header"""
    
    default_data_startblock=3586
    default_dir_startblock=8
    default_data_type=2  
    default_data_type_string="Uncompressed (24-Bit)"
    
    h = LCDiskHeader()

    # UNUSED OR STANDARD VALUES
    h.dataType=default_data_type
    h.diskSize=0    # GB
    h.ramSize=8     # MB
    h.softwareVersion='9.08a-OLD'
    h.dirStart=default_dir_startblock
    h.dataStart=default_data_startblock    
    #h.dirSize=(h.dataStart-h.dirStart-1)*dirs_per_block
    h.dirSize=(h.dataStart-h.dirStart)*dirs_per_block - 1 # Modified to work with lc2ms v1
    (h.slowStart,h.slowSize,h.slowBlock,h.slowByte)=(0,0,0,0)
    (h.logStart,h.logSize,h.logBlock,h.logByte)=(0,0,0,0)
    (h.slowDataRate,h.slowStartChannel,h.slowNumberOfChannels)=(0,0,0)
    (h.readBlock, h.startChannel,h.diskNumber)=(0,0,0)
    (h.numberOfWindows,h.readByte,h.writeByte)=(0,0,0)

    # These should be modified after writing directory    
    (h.dirBlock,h.dirCount)=(0,0)
    
    # USER-SPECIFIED VALUES    
    h.description='generic lcheapo header'    
    h.sampleRate=125
    h.numberOfChannels=4
    h.writeBlock=h.dataStart
        
    # Additions which cannot be written to file
    h.realSampleRate = h.getRealSampleRate(h.sampleRate)
    h.dataTypeString = default_data_type_string
    return h
    
##############################################################################
def __prep_dirEntry(sample_rate):
    """Prepare lcheapo directory entry object"""
    d=LCDirEntry()
    d.recordLength = 0  # Unused
    d.sampleRate =   sample_rate
    d.numBlocks =    blocks_per_dirEntry
    d.flag =         0x49
    d.muxChannel =   0
    d.U1 =           0 # Unused
    return d
    
##############################################################################
def __make_dirEntry(d,blocknum, dt):
    """Put time in lcheapo directory entry"""
    d.blockNumber=blocknum
    d.changeTime(dt)
    #(d.year,d.month,d.day,d.hour,d.minute,d.second)= dt.timetuple()[0:6]
    #d.year=d.year-1900
    #d.msec=int(dt.microsecond/1000)
    return d
    
##############################################################################
def __get_string(question,default):
    """Read a string from the command line"""
    resp=raw_input("{} [{}]: ".format(question, default))
    if not resp:
        return default
    return resp

##############################################################################
def __get_datetime(question,default):
    """Read a datetime from the command line"""
    resp=raw_input("{} [{}]: ".format(question, default.isoformat()))
    if not resp:
        return default
    else:
        try:
            resp=datetime.strptime(resp,'%Y-%m-%dT%H:%M:%S')
        except:
            try:
                resp=datetime.strptime(resp,'%Y-%m-%dT%H:%M:%S.%f')
            except:
                print('Invalid input: {}'.format(resp))
                resp=__get_datetime(question,default)
    return resp
    
##############################################################################
def __get_int(question,default,possibles=False):
    """Read an int from the command line"""
    resp=raw_input("{} [{:d}]: ".format(question, default))
    if not resp:
        return default
    else:
        try:
            resp=int(resp)
        except:
            print('Invalid input: {}'.format(resp))
            resp=__get_int(question,default,possibles)
        if isinstance(possibles,list):
            if resp not in possibles:
                print('Input must be one of: {}'.format(str(possibles)))
                resp=__get_int(question,default,possibles)       
    return resp
    
##############################################################################
def __get_float(question,default,possibles=False):
    """Read a float from the command line"""
    resp=raw_input("{} [{:d}]: ".format(question, default))
    if not resp:
        return default
    else:
        try:
            resp=float(resp)
        except:
            print('Invalid input: {}'.format(resp))
            resp=__get_float(question,default,possibles)
        if isinstance(possibles,list):
            if resp not in possibles:
                print('Input must be one of: {:d}'.format(possibles))
                resp=__get_float(question,default,possibles)       
    return resp
    
##############################################################################
if __name__ ==  '__main__':
    opts = __getOptions()
    status=main(opts)
    sys.exit(status)

