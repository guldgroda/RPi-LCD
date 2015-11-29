#!/usr/bin/python2.7

# Based on Code example from http://www.pi-supply.com

# Import the modules to send commands to the system and access GPIO pins
from subprocess import call
import RPi.GPIO as gpio
import time 

# Define a function to keep script running
def loop():
	try:
    		raw_input()
	except (EOFError):
		print time.strftime('%Y-%m-%d %H:%M:%S')+" EOFError" 

 
# Define a function to run when an interrupt is called
def shutdown(pin):
	call('halt', shell=False)

def setupGPIO(pin):
	gpio.setmode(gpio.BOARD) # Set pin numbering to board numbering
	gpio.setup(pin, gpio.IN) # Set up pin 7 (GPIO4) as an input
	gpio.add_event_detect(pin, gpio.RISING, callback=shutdown, bouncetime=200) # Set up an interrupt to look for button presses
	

print time.strftime('%Y-%m-%d %H:%M:%S')+" Setting up GPIO" 

try:
	setupGPIO(7)
except (RuntimeError):
	print time.strftime('%Y-%m-%d %H:%M:%S')+" Failed to add edge detection... trying again." 
	time.sleep(0.5)
	setupGPIO(7) #IF it fails, try again...

print time.strftime('%Y-%m-%d %H:%M:%S')+" Starting loop" 
loop() # Run the loop function to keep script running
