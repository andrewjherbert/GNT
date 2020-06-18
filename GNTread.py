
# Read in paper tapes from GNT4604.

print("\nGNTread - Andrew Herbert - 13/08/2019\n")

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

# Function to read in a tape on current serial port ser

def readTape(ser):
    
    reel = 1000 * 12 * 10 # length of roll of tape (1000') in characters

    buf = bytearray(reel)
    chCount = 0

    # Wait for data to come from reader
    while ser.in_waiting <= 0:
        time.sleep(0.1)
    for i in range(reel):
        b = ser.read(1) # read one character
        if len(b) == 0:
            break # tape has run through reader
        else:
             buf[i] = b[0]
             chCount = chCount + 1
    buf = buf[:chCount-1]
    print (len(buf), "characters read")
    
    if len(buf) == 0:
        return buf

    # Trim off header
    nxt = 0
    for i in range(len(buf)):
        nxt=i
        if buf[i] != 0:
            break
    buf = buf[max(0,nxt):]

    # Trim off trailer
    nxt = 0
    for i in range(len(buf)):
        nxt=-i
        if buf[nxt-1] != 0:
            break
    if nxt < 0:
        buf = buf[:nxt]

    print ("Trimmed to ", len(buf), "characters")
    return buf

# Function to check tape buffers b1 and b2 are identical

def verifyTape(b1,b2):
    if len(b1) != len(b2) :
        print ("Tapes are of different length")
        sys.exit(1)
    for i in range (len(b1)) :
        if b1[i] != b2[i] :
            print ("Tapes are not identical")
            sys.exit(1)

# Main program

@click.command()
@click.argument('outfile', type=click.File('wb'))
@click.argument('port', default='/dev/ttyUSB0')
def GNTread (outfile, port):

    # Set up serial port
    ser = serial.Serial()
    ser.port     = port
    ser.baudrate = 4800
    ser.timeout  = 1

    # Open serial port
    try:
        ser.open()
    except serial.SerialException as e:
            sys.stderr.write(
                'Could not open serial port {}: {}\n'.format(ser.name, e))
            sys.exit(1)
            
    # Read tape twice and compare
    # Prompt user
    input("Load tape in reader, press RETURN and start reader")
    # Read entire tape for first time
    tape1 = readTape(ser)
    # Prompt user
    input("Reload tape, press RETURN and start reader")
    tape2 = readTape(ser)
    # Close the serial port
    ser.close()
    # Verify the tapes are identical
    verifyTape(tape1,tape2)
    print("Tapes match ok")
    # Output header
    for i in range(60) :
        outfile.write(bytes([0]))
    # Output tape
    outfile.write(tape1)
    # Output trailer
    for i in range(60) :
        outfile.write(bytes([0]))
    # Close file
    outfile.close()

if __name__ == '__main__' :
    GNTread()


