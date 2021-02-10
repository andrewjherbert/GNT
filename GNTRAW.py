
# Punch paper tapes on GNT4604.

# Punched tape is read back in and verified against file.

print("\nGNTRAW - Andrew Herbert - 28/08/2019\n")

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

def readTape(ser):

    ser.timeout = 0.1 # Timeout on read to detect end of tape
    
    reel = 1000 * 12 * 10 # Length of roll of tape (1000') in characters
    
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
        print ("Tapes are of different length")
        sys.exit(1)
    for i in range (len(b1)):
        if b1[i] != b2[i]:
            print ("Tapes are not identical at character", i, b1[i], b2[i])
            sys.exit(1)
    print("Tape verified ok")

# Function to punch a character

outEvents = 0
inEvents = 0

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

def punchBuffer(ser,buf):

    ser.timeout  = None # Wait indefinitely for DC1 after DC3
    for ch in buf:
        punchCh(ser, ch)

def punchRunout(ser):
    for i in range(90):
        punchCh(ser, 0)
            
# Main program

@click.command()
@click.argument('infile', type=click.File('rb'))
@click.argument('port', default='/dev/ttyUSB0')
def GNTpunch (infile, port):

    global inEvents, outEvents
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
            sys.stderr.write(
                'Could not open serial port {}: {}\n'.format(ser.name, e))
            sys.exit(1)
            
    # Read and trim file
    buf = infile.read()
    infile.close()
    buf = trim(buf)
    # Punch tape
    punchRunout(ser)
    punchBuffer(ser, buf)
    punchRunout(ser)
    
    # Read back and verify the tape
    # Prompt user
    print("Verifying punched tape - load output tape,"
          "press RETURN and start reader")
    tape = readTape(ser)

    # Close the serial port
    ser.close()
    
    # trim the tape
    tape = trim(tape)

    # Verify the tapes are identical
    verifyTape(buf, tape)

if __name__ == '__main__' :
    GNTpunch()


