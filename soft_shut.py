#!/usr/bin/python2.7

# Based on Code example from http://www.pi-supply.com

# Import the modules to send commands to the system and access GPIO pins
from subprocess import call
import RPi.GPIO as gpio
# General imports
import time 
import os

# Define a function to keep script running
def loop():
	while True:
		time.sleep(60)

# Define a function to run when an interrupt is called
def shutdown(pin):
	# Create shutdown file for LCD handler
	os.mknod("/home/pi/RPi-LCD/shutdown")
	# Sleep 10 seconds to let LCD handler show shutdown message
	time.sleep(10)
	# Call system halt
	call('halt', shell=False)

def setupGPIO(pin):
	gpio.setmode(gpio.BOARD) # Set pin numbering to board numbering
	gpio.setup(pin, gpio.IN) # Set up pin 7 (GPIO4) as an input
	gpio.add_event_detect(pin, gpio.RISING, callback=shutdown, bouncetime=200) # Set up an interrupt to look for button presses
	
### Main program
print time.strftime('%Y-%m-%d %H:%M:%S')+" Setting up GPIO" 

try:
	# Try to set up GPIO
	setupGPIO(7)
except (RuntimeError):
	print time.strftime('%Y-%m-%d %H:%M:%S')+" Failed to add edge detection... trying again." 
	time.sleep(1)
	setupGPIO(7) #IF it fails, try again...

# Run the loop functiun to keep script runngin
print time.strftime('%Y-%m-%d %H:%M:%S')+" Starting loop" 
loop()
