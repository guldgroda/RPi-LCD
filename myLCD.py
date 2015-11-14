  #!/usr/bin/python2.7


##Time
from datetime import datetime
from time import gmtime, strftime, sleep

##Data Acqusition
from xml.dom import minidom
import urllib2

##Scheduling
import schedule
import time

## Rasperry libraries
import RPi.GPIO as GPIO
from RPLCD import CharLCD

##define staic values

## LCD SETUP
### Pin number has to be change to the pin numbers you are using on your Raspberry Pi.
### The LCD is a 40x4 display. The library RPLCD can only handle 40x2 so the LCD has to be set up as two 40x2 displays.
### using two enable signals. The handling of this is done under LCD handler.
### The number are the pin numbers of the Raspberry Pi, not the GPIO numbers.
### If using a older Raspberry Pi with only 26 pins make sure you have the correct pin pinnumbers.

GPIO_PIN_RS = 32
GPIO_PIN_RW = None ## Raspberry Pi cannot handle if the display writes data. Could damage RPi. This pin on the LCD was connected to gound.
GPIO_PIN_E_TOP = 33
GPIO_PIN_E_BOTTOM = 31
GPIO_PIN_D4 = 36
GPIO_PIN_D5 = 35
GPIO_PIN_D6 = 38
GPIO_PIN_D7 = 40
LCD_COLUMNS = 40
LCD_ROWS = 2
LCD_DOT_SIZE = 8

LCD_BRIGHTNESS = 0 # to be used with PWM for control of the LCD brightness.

### Initialize the LCD
lcd_top = CharLCD(pin_rs=GPIO_PIN_RS, pin_rw=GPIO_PIN_RW,  pin_e=GPIO_PIN_E_TOP, pins_data=[GPIO_PIN_D4, GPIO_PIN_D5, GPIO_PIN_D6, GPIO_PIN_D7], numbering_mode=GPIO.BOARD, cols=LCD_COLUMNS, rows=LCD_ROWS, dotsize=LCD_DOT_SIZE)
lcd_bottom = CharLCD(pin_rs=GPIO_PIN_RS, pin_rw=GPIO_PIN_RW, pin_e=GPIO_PIN_E_BOTTOM, pins_data=[GPIO_PIN_D4, GPIO_PIN_D5, GPIO_PIN_D6, GPIO_PIN_D7], numbering_mode=GPIO.BOARD, cols=LCD_COLUMNS, rows=LCD_ROWS, dotsize=LCD_DOT_SIZE)

var = 1
i = 0


### Functions for getting time
def getTime():
	"Gets the current time and date and returns as a string"
	time=strftime("%A %Y-%m-%d %H:%M:%S")
	return time

### Functions for XML parsing
def getNodeText(node):
        nodelist = node.childNodes
        result = []
        for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                        result.append(node.data)
        return ''.join(result)

### Functions and variables for getting bus times
busTimes="Not available yet..."
def getBusTimes():
	## Skanetrafiken Open Lab API
	stationID = "81748"
	busStopName = "Lund Gambro"
	skanetrafikenURL="http://www.labs.skanetrafiken.se/v2.2/stationresults.asp?selPointFrKey=" + stationID
	myStopPoint = "A" # towards city/Gunnesbo
	
	##Get XML Data from API
	xml_data = minidom.parse(urllib2.urlopen(skanetrafikenURL))
	##Get all line elements (each arriving bus is one line"
	results = xml_data.getElementsByTagName("Line")
	# Lists for the bus times and DepDeviation	
	timeList = []
	deviationList = []

	#Loop through all departures
	for departure in results:
		# Get stopPoint
	        stopPoint = getNodeText(departure.getElementsByTagName("StopPoint")[0])
        	# We only want buses going towards city centre
		if stopPoint == myStopPoint:
			# Save bus name (bus 4)
                	name = getNodeText(departure.getElementsByTagName("Name")[0])
                	# Get date and time, formatted YYYY-MM-DDTHH:MM:SS and get only HH:MM
			time = getNodeText(departure.getElementsByTagName("JourneyDateTime")[0])[11:-3]
                	# Check if there is any deviation in time.
			if( len(departure.getElementsByTagName("DepTimeDeviation") ) != 0 ):
                	        # IF deviation, save the deviation
                	        deviation = getNodeText(departure.getElementsByTagName("DepTimeDeviation")[0])
                	else:
                	        # if no deviation, save 0 as deviation
                	        deviation = "0"
	        	# Append time and deviation to respective list.
			timeList.append(time)
        	        deviationList.append(deviation)
	
	## Create string from times and deviations
	nbrBusTimes = 6 # How many bus times that can possibly fit screen (Best case)
	maxChar = 34
	my_times = ""
	for i in range (0,nbrBusTimes):
		# Format should be HH:MM+dev
		devInt = int(float(deviationList[i])) 
		nextTime = ""
		if(devInt < 0):
			nextTime = timeList[i]+deviationList[i]+" "
		elif(devInt >0):
			nextTime = timeList[i]+"+"+str(devInt)+" "
		else:
			nextTime = timeList[i]+" "
		if len(my_times)+len(nextTime) < maxChar:
			my_times += nextTime
	global busTimes
	busTimes = my_times
	#print "New BusTimes: "+busTimes
	return

### Temperature
## yr.no API
curTemp = "NA" #placeholder...
def getTemp():
	placeID = "Sverige/Scania/Lund"
	weatherNowURL = "http://www.yr.no/place/" + placeID + "/forecast.xml"
	xml_data = minidom.parse(urllib2.urlopen(weatherNowURL))
	node = xml_data.getElementsByTagName("temperature")[0]
	temp = getNodeText(node.attributes.values()[0])
	global curTemp
	curTemp = temp
	#print "New temp: "+curTemp


### LCD Functions
def printLine( lineNr, str):
	#Add spaces for automatic clearing of LCD
	str+="                                            "
	"Prints one line on LCD, lineNR, 0-3 is LCD Row and str is string to be printed, max 40 char (will be cropped if longer)"
	str=str[:40] #Crop string to first 40 char
	# If lineNr 0 or 1, top LCD
	if lineNr==0 or lineNr==1:
		lcd_top.cursor_pos=(lineNr,0)
		lcd_top.write_string(str)
	# If lineNr 2 or 3, bottom LCD
	elif lineNr==2 or lineNr==3:
		lineNr-=2 #Still called as row 0,1 to lcd...
		lcd_bottom.cursor_pos=(lineNr,0)
		lcd_bottom.write_string(str)
	return
def clearLine(lineNr):
	printLine(lineNr, "                                            ")
	return

def firstString():
	"Creates first string for LCD"
	degree_sign=unichr(223).rstrip()
	str = "Lund "+curTemp+degree_sign+"C, "+getTime()
	return str
def secondString():
	"Creates second string for LCD"
	str = "Buss 4: "+busTimes
	return str
def thirdString():
	"Creates third string for LCD"
	str = "N/A"
	return str
def fourthString():
	"Creates fourth string for LCD"
	str = "N/A"
	return str

def updateLCD():
	printLine(0,firstString())
        printLine(1,secondString())
	printLine(2,thirdString())
        printLine(3,fourthString())
	#print "LCD update"	

### SCHEDULING
# Run everything once at start of program
getBusTimes()
getTemp()
updateLCD()

#Update bus times every 30 sec
schedule.every(30).seconds.do(getBusTimes)

# Update temp every 30 minutes
schedule.every(30).minutes.do(getTemp)

### MAIN FUNCTION
cnt=0
while True:
	schedule.run_pending()
	time.sleep(0.1)

	#Update LCD every 100 ms
	updateLCD()	

