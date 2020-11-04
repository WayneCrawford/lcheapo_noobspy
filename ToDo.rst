TO DO
======================

- lcfix will overwrite a file with suffix 'fix.lch'!!!!!!

- Add sdpchain:process-steps to lcheader (new version #)


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
