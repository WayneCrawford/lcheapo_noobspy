TO DO
======================

- sdpcat should quit and say why if the output file exists already
  - and if the input files don't exist
- lccut also
- lccut command output should mention input file name
    - and should save as exec_messages to process-steps
- sdpcat should list files (and their size?) as it processes them to stdout
    - and to exec_messages
- ProcessSteps should have exec_message() function 
- Make all processing codes use sdpchain and its standard parameters
    - Need version number upgrade (1.0?)
- Make lcfix give an intelligent output when it doesn't find a header?
- Make process-steps a class
  - init at beggining
  - modify as you go
  - exec_message() function that prints a message to the screen and saves to
    its exec_messages list
  - write(resultcode) whereever you stop
- Make sdpchain.argparse
  - Sets up standard parameters (-d, -i, -o)
  - Checks if outfile exists (quit if so, unless Force)
  - Check if infiles exist?
- Make sdpchain a separate module

- Add wrappers for commonly used routines:

  * sdp_msmod?


- Modify sdpchain:process so that:

  * It creates its own part of the command-line arguments (-d, -i, -o)
  * "-d ... makes it run the command from within that directory " (what
    does this mean?


- Modify lcfix to:

  * modify "Write Block" in header to correspond to data length
  * work with input header file
  * be more streamlined (cleaner code) 
  * Force non-time header values
  * Test to make sure first file has header, and subsequent don't
    (requires new routine isHeader() in lcheapo.py)
  * If first file doesn't have header, allow header creation
    (use lcheader.py)
  * Change directory entry creation to create a new one if original header
    didn't have enough directory entries
