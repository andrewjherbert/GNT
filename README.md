GNT

Python programs for operating a GNT4604 paper tape reader / punch via a serial port.

GNTread <infile> -- read a paper tape as raw bytes into <infile>.  If <infile> exists it will be overwritten.
  
GNTRAW <outfile> -- punch <outfile> as raw bytes to paper tape with no translation.
  
GNT900 <outfile> -- punch <outfile> assumed to be UTF-8 with translation of certain non-ASCII character found in Elliott 900 telecode.
  
GNTBIN <outfile> -- punch <outfile> assumed to be a sequence of decimal numbers representing 8 bit codes.
  
GNTtest          -- a test program for verifying delay parameter in driving serial port

Note (1): the GNT900 and GNTBIN programs relate to paper tape encodings used by my Elliott 900 Simulator.

Note (2): 900 telecode is a paper tape code that preceded ASCII, which associated different printed symbols with certain of the ASCII codes.
GNT900 assumes the input is UTF-8 and maps certain symbols from Unicode corresponding to the Elliott symbols to the ASCII symbols standing 
in the same positions in the respective 8 bit codes.

Note (3): the representation of a paper tape as a series of decimal numbers is a convenient format for editing binary paper tapes.
