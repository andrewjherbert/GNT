
# Punch Elliott BIN format paper tapes on GNT4604.

# Punched tape is read back in and verified against file.

print("\nGNTBIN - Andrew Herbert - 08/10/2019\n")

# GNT4604 configuration
#
# RaspberryPi connected via USB serial converter to GNT4604 DCE socket
# with null modem.
# Front panel switches:
# Mode - CPU
# Reader - NORM
# Punch - NORM
# Speed - HIGH
# DIP switches:
# SW1 ECHO - OFF
# SW2 - LEADER - OFF (Normal leader)
# SW3 - DC CODES  - OFF (No X-on/X-off control for reader)
# SW4-5 - OFF ON (8 data bits, no parity, 1 stop bit)
# SW6-7 - OFF OFF (4800 Baud)

import click
import serial
import sys
import time

# Function to trim leader and trailer off a buffer

def trim(buf):
    
    # Trim off header
    nxt = 0
    for i in range(len(buf)):
        nxt = i
        if buf[i] != 0:
            break
    buf = buf[nxt:]

    # Trim off trailer
    nxt = len(buf)
    for i in range(len(buf)):
        nxt = nxt-1
        if buf[nxt] != 0:
            break
    buf = buf[:nxt+1]

    return buf
    
# Function to read in a tape on current serial port ser

reel = 1000 * 12 * 10 # Length of roll of tape (1000') in characters

def readTape(ser):

    ser.timeout = 0.1 # Timeout on read to detect end of tape
    
    buf = bytearray(reel)
    chCount = 0

    # Wait for data to come from reader
    while ser.in_waiting <= 0:
        time.sleep(0.1)
    for i in range(reel):
        b = ser.read(1) # Read one character
        if len(b) == 0:
            break # Tape has run through reader
        else:
             buf[i] = b[0]
             chCount = chCount + 1
    buf = buf[:chCount-1]
    return buf

# Function to check tape buffers b1 and b2 are identical

def verifyTape(b1, b2):

    if len(b1) != len(b2):
        print ("Tapes are of different length",
                        len(b1), len(b2))
        #sys.exit(1)
    for i in range (min(len(b1),len(b2))):
        if b1[i] != b2[i]:
            print("Tapes are not identical at byte", i)
            print(b1[i])
            print(b2[i])
            sys.exit(1)
    print("Tape verified ok")

# Function to punch a character

outEvents = 0
inEvents = 0

# Function to punch a character
def punchCh(ser, ch):
    
    global inEvents, outEvents


    # Use DC1 and DC3 for flow control
    dc1 = 17 # X-ON
    dc3 = 19 # X-OFF

    # Pause after each punched character to allow GNT to signal flow 
    # control
    delay      = 1 / 80 # experimentally determined

    # Look for flow control
    while ser.in_waiting > 0:
        inEvents=inEvents+1
        b = ser.read (1)
        if b[0] == dc3:
            time.sleep (delay)
            b = ser.read (1)
            if b[0] != dc1:
                print ("DC3 not followed by DC1 - ", b[0])
                sys.exit (1)
        else:
            print ("DC3 expected, got ", b[0])
            sys.exit (1)

    # Output character to punch
    while ser.out_waiting > 0:
        outEvents=outEvents+1
        while ser.out_waiting > 0:
            time.sleep (delay)
    ser.write (bytes([ch]))

    # Allow time for GNT to send flow control codes
    time.sleep (delay)

# Function to punch a buffer

def punchBuffer(ser, buf):

    tape = bytearray(len(buf))
    ser.timeout  = None # Wait indefinitely for DC1 after DC3
    i = 0
    for ch in buf:
        punchCh(ser, ch)
    return(tape[0:i])

def punchRunout(ser):
    for i in range(90):
        punchCh(ser, 0)

# Function to convert a BIN format file to raw binary

def Convert (inFile):

    outBuf = bytearray(reel)
    words = inFile.split(None)
    inPos = 0
    outPos = 0
    while inPos < len(words):
        word = words[inPos]
        if word.startswith('('):
            while not words[inPos].endswith(')'):
                    inPos = inPos+1
            else:
                inPos = inPos+1
        else:
            outBuf[outPos] = int(words[inPos])
            outPos = outPos+1
            inPos = inPos+1
    return trim(outBuf)
        
# Main program

@click.command()
@click.argument('infile', type=click.File('r'))
@click.argument('port', default='/dev/ttyUSB0')
def GNTpunch (infile, port):

    inEvents = 0
    outEvents = 0
    # Set up serial port
    ser = serial.Serial()
    ser.port     = port
    ser.baudrate = 4800

    # Open serial port
    try:
        ser.open()
    except serial.SerialException as e:
            print("Could not open serial port ", ser.name, e)
            sys.exit(1)
            
    # Read and tidy file
    inBuf = infile.read()
    infile.close()
    # Remove BOM if present
    if ord(inBuf[0]) == 65279:
        inBuf = inBuf[1:]
    outBuf = Convert(inBuf)
        
    # Punch tape
    # Punch leader
    punchRunout(ser)
    # Punch file
    outputTape = punchBuffer(ser, outBuf)
    # Punch trailer
    punchRunout(ser)
    
    # Read back and verify the tape

    # Prompt user
    print("Verifying punched tape")
    input("Load tape, press RETURN and start reader")
    inputTape = trim(readTape(ser))

    # Close the serial port
    ser.close()

    # Verify the tapes are identical
    verifyTape(inputTape, outBuf)

if __name__ == '__main__' :
    GNTpunch()


