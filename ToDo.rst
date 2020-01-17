TO DO
======================
 
- Add sdpchain:process-steps to lcheader (new version #)

- Add commonly used routines:
  * lccut (replaces dd, allowing "skip", "count" "if" and "of")
  * lcinfo: give an overview of LCHEAPO files (time range, channels, if times match)

- Add wrappers for commonly used routines:
  * sdp_msmod? (

- Modify sdpchain:process so that:
    * It creates its own part of the command-line arguments (-d, -i, -o)
    * "-d ... makes it run the command from within that directory " (what
      does this mean?
      
- Modify lcfix to:
    * modify "Write Block" in header to correspond to data length
    * work with input header file
    * be more streamlined (cleaner code) 


Use `reStructuredText
<http://docutils.sourceforge.net/rst.html>`_ to modify this file.
