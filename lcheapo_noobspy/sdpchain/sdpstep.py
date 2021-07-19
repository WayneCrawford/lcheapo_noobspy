#!/usr/bin/env python3
"""
    Run a command-line program and save info to process-steps file
"""
import subprocess
import sys
# import os
import argparse
from datetime import datetime
import distutils.spawn

from .version import __version__
from .process_steps import ProcessStep
from .setup_paths import setup_paths

assert sys.version_info >= (3, 5)

help_epilog = """
Some recommended instances of sdpstep:
TO INSERT A POSITIVE LEAP-SECOND (61-second minutes) AT $LEAPTIME
    ($LEAPTIME format is 'YYYY,DDD,HH,MM,SS,FFFF' delimiters can be [,:.])
    sdp-process "msmod --timeshift -1 -ts $LEAPTIME -s -o OUTFILE INFILE"
    sdp-process "msmod --actflags 4,1 -tsc $LEAPTIME -tec $LEAPTIME -s -i OUTFILE"
TO INSERT A NEGATIVE LEAP-SECOND (no second 59) AT $LPTIME
    sdp-process "msmod --timeshift +1 -ts $LEAPTIME -s -o OUTFILE INFILE"
    sdp-process "msmod --actflags 5,1 -tsc $LEAPTIME -tec $LEAPTIME  -s -i OUTFILE"
TO MERGE SEVERAL MINISEED FILES INTO ONE:
    sdp-process "msmod -o toto.mseed INFILES"
TO CHANGE CHANNEL/LOCATION CODES SEVERAL MINISEED FILES INTO ONE:
    sdp-process "msmod -o toto.mseed INFILES"

For use in the Seismology Data Preparation (SDP) chain

If tool_line_cmd is empty quotes, will create an unfilled process step
"""
app_description = "Run a command-line tool and write process-step"
app_name = "sdpstep"


def main():
    """
    Run a command line and enter run information into process-steps file

    -i and -o only affect the process-steps file, as each tool can have
    its own way to specify input and output files

    Uses subprocess toolbox, so redirects (">") and pipes ("|") won't work
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=app_description,
        epilog=help_epilog)
    parser.add_argument('tool_cmd_line', action="store",
                        help='The command line to run')
    parser.add_argument('-c', action="store", dest="exec_comment",
                        help='Execution comment')
    parser.add_argument('--version', action="store_true", dest="print_version",
                        default=False,
                        help='Print the version number and quit')
    parser.add_argument("-d", "--directory", dest="base_dir",
                        default='.', help="Base directory for files")
    parser.add_argument("-i", "--input", dest="in_dir", default='.',
                        help="path to input files (abs, or rel to base)")
    parser.add_argument("-o", "--output", dest="out_dir", default='.',
                        help="path for output files (abs, or rel to base)")
    args = parser.parse_args()
    if args.print_version:
        print(f'version {__version__}')
        sys.exit(0)

    process_step = ProcessStep(app_name,
                               " ".join(sys.argv),
                               app_description = app_description,
                               app_version = __version__,
                               parameters=args)

    args.in_dir, args.out_dir = setup_paths(args)

    # if args.base_dir:
    #     print('Changing working directory to {}'.format(args.base_dir))
    #     os.chdir(args.base_dir)

    if len(args.tool_cmd_line) == 0:
        process_step.exit_code=0,
        process_step.tools=["tool"]
    else:
        # RUN THE COMMAND LINE
        if ">" in args.tool_cmd_line or "|" in args.tool_cmd_line:
            raise ValueError('Cannot have ">" or "|" on tool_cmd_line')
        tool = args.tool_cmd_line.split()[0]
        if not is_tool(tool):
            raise OSError(f'tool "{tool}" not found')
        return_code, exec_message = run_command_line(args.tool_cmd_line)

        # WRITE INFORMATION TO PROCESS-STEPS FILE
        tool = args.tool_cmd_line.split()[0]
        params = dict(tool_version=_get_tool_version(tool),
                      tool_description=_get_tool_description(tool))
        process_step.exit_code=0,
        process_step.messages = exec_message
        process_step.tools=[tool]
    process_step.write(args.in_dir, args.out_dir)
    return


def is_tool(name):
    return distutils.spawn.find_executable(name) is not None


def run_command_line(command_line):
    """
    Runs the command line and returns information
    """
    try:
        # p = subprocess.check_output(command_line, stderr=subprocess.STDOUT)
        CP = subprocess.run(command_line.split(), check=True,
                            capture_output=True)   # ,
        # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        return_code = err.returncode
        exec_message = str(err.output, encoding='utf-8',
                           errors='strict').splitlines()

    else:
        return_code = 0
        exec_message = str(CP.stdout, encoding='utf-8',
                           errors='strict').splitlines()
    return return_code, exec_message


def _get_tool_version(tool):
    """
    Get version information about the command

    :param tool: the command-line tool
    :type tool: str
    :returns: version information
    :rtype: str
    """
    option_list = ["--version", "-V", "", '-h']
    for option in option_list:
        outp = _get_test_output([tool, option])
        if outp:
            return _get_first_line(outp)
    return ''


def _get_tool_description(tool):
    """
    Get description of the command

    :param tool: the command-line tool
    :type tool: str
    :returns: version information
    :rtype: str
    """
    option_list = ["--help", "-h", ""]
    for option in option_list:
        outp = _get_test_output([tool, option])
        if outp:
            return _get_first_line(outp)
    return 'None'


def _get_test_output(cmd_list):
    """
    Get output of command for test.

    :param cmd_list:command and any arguments
    :type cmd_list: str
    returns: List of the text lines from stdout+stderr
             or None if none output or command fails
    """
    try:
        CP = subprocess.run(cmd_list, timeout=5,
                            check=True, capture_output=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        return None
    else:
        if CP.returncode == 0:
            outp = CP.stdout
            outp = str(outp, encoding='utf-8', errors='strict')
            if type(outp) == 'str':
                outp = outp.splitlines()
        else:
            return None
    return outp


def _get_first_line(inp):
    if isinstance(inp, str):
        return inp.split('\n')[0]
    if isinstance(inp, list):
        if isinstance(inp[0], str):
            return inp[0].split('\n')[0]
    return ""


if __name__ == '__main__':
    main()
