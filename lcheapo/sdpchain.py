#!/usr/bin/env python2.7
"sdp-process.py --  SDPCHAIN compatibility functions."

from __future__ import print_function
import os
import json
import copy         # for deepcopy of argparse dictionary


def setup_paths(args):
    """
    Set up paths according to SDPCHAIN standards
    
    args=class with the following properties:
        mandatory:
            base_directory [str]
            infiles [list]
        optional:
            input_directory [str]
            output_directory [str]
    """
    
    if os.path.isabs(args.input_directory):
        in_filename_path=args.input_directory
    else:
        in_filename_path=os.path.join(args.base_directory,args.input_directory)
    in_filename_root=args.infiles[0].split('.')[0]
    if os.path.isabs(args.output_directory):
        out_filename_path=args.output_directory
    else:
        out_filename_path=os.path.join(args.base_directory,args.output_directory)
    if not os.path.exists(out_filename_path):
        print("output directory '{}' does not exist, creating...".format(out_filename_path))
        os.mkdir(out_filename_path)
    elif not os.path.isdir(out_filename_path):
        print("output directory '{}' is a file!, changing to base directory".format(out_filename_path))
        out_filename_path=args.base_directory
    out_filename_root=in_filename_root

    return in_filename_path,in_filename_root,out_filename_path,out_filename_root


def make_process_steps_file(startTimeStr,args,outFiles,msgs,returnCode,debug=False) :
  """
    Make or append to a process-steps.json file
    
    Inputs: startTimeStr  - A string containing the program start time
            parameters - a list of program parameters
            inFiles - a list of input files
            outFiles - a list of output files
            msgs - a list of messages about the data processing (one per input
                   file)
            returnCode: 0 for no error, others not yet defined
    Outputs: file process-steps.json
  """
  parameters=copy.deepcopy(vars(args))
  del parameters['infiles']

  application={
    'name':"lcFix.py",
    'description':"Fix common bugs in LCHEAPO data files",
    'version':versionString
  }
  execution=  {
    'commandline':" ".join(sys.argv),
    'date':        startTimeStr,
    'messages':    msgs,
    'parameters':  parameters,
    'tools' :      [],
    'return_code': returnCode
  }
  execution['parameters']['input_files']=args.infiles
  execution['parameters']['output_files']=outFiles
  step = {'application':application,'execution':execution}
  if debug:
    print(json.dumps(step, indent=4, separators=(',', ': ')))
  filename=os.path.join(args.base_directory,'process-steps.json')
  try:
    fp=open(filename,"r")
  except:  # File not found
    tree={"steps":[step]}
  else:   # File found
    tree=json.load(fp)
    if 'steps' in tree: 
       tree['steps'].append(step)
    else:
      tree['steps']=[step]
    fp.close() 
  if debug:
    json.dumps(tree, indent=4, separators=(',', ': '));  # For testing
  fp=open(filename,"w")
  json.dump(tree,fp,sort_keys=True, indent=2);  # For real
  fp.close

