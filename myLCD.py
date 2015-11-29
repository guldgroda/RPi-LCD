#!/usr/bin/python


##Time
from datetime import datetime, timedelta
from time import gmtime, strftime, sleep

##Data Acqusition
from xml.dom import minidom
import urllib2
import json
import feedparser

##Scheduling
import schedule
import time

## Raspberry libraries
import RPi.GPIO as GPIO
from RPLCD import CharLCD

## Shutdown management
import os.path

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


### Functions for downloading data
def getUrlData(url):
	try:
		my_data = urllib2.urlopen(url)
	except urllib2.URLError, e:
		my_data = "-1"
	return my_data

### Functions and variables for getting bus times
busTimes="Not available yet..."
def getBusTimes():
	## Skanetrafiken Open Lab API
	stationID = "81748"
	busStopName = "Lund Gambro"
	skanetrafikenURL="http://www.labs.skanetrafiken.se/v2.2/stationresults.asp?selPointFrKey=" + stationID
	myStopPoint = "A" # towards city/Gunnesbo
	global busTimes
	##Get XML Data from API
	my_data = getUrlData(skanetrafikenURL)
	if "-1" in my_data:
		busTimes = "Something went wrong..."
		print "Something went wrong..."
	else:
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
		busTimes = my_times
		#print "New BusTimes: "+busTimes
	
	return

### Temperature
## yr.no API
curTemp = "NA" #placeholder...
def getTemp():
	placeID = "Sverige/Scania/Lund"
	weatherNowURL = "http://www.yr.no/place/" + placeID + "/forecast.xml"
	global curTemp
	my_data = getUrlData(weatherNowURL)
	if "-1" in my_data:
		curTemp = "NA"
		print "Lost internet connection..."
	else:
		xml_data = minidom.parse(urllib2.urlopen(weatherNowURL))
		node = xml_data.getElementsByTagName("temperature")[0]
		temp = getNodeText(node.attributes.values()[0])
		curTemp = temp
		#print "New temp: "+curTemp

### Exchange rates
my_currencies = ["USD", "EUR","CNY","GBP","NOK", "DKK"]
exchange_rates = []
for i in range(0,len(my_currencies)):
	exchange_rates.append("N/A") #placeholder
xrt_count = 0

# API information
app_id = ""	
with open("openxrtappid") as f:
	app_id = f.readline()

base_url = "https://openexchangerates.org/api/"

def getLatest(currencies):
	latest = "latest.json?app_id="
	# Create URL
	my_url = base_url + latest + app_id
	# Get JSON data from URL
	json_data = json.load(getUrlData(my_url))
	# Get exchange rates from JSON data
	rates = json_data['rates']
	my_rates =  []
	for currency in currencies:
		#print currency
		#All currencies correlating to USD, we convert to SEK...
		USD = rates['SEK']
		if "USD" in currency:
			this_xrt = "%.2f" % USD
		else:
			this_xrt = "%.2f" % (USD/rates[currency])
		# After getting XRT, append it to
		#print type(this_xrt) 
		my_rates.append(this_xrt)
	#print my_rates
	return my_rates

def getHistory(date, currencies):
	history = "historical/"+date+".json?app_id="
	# Create URL
	my_url = base_url + history + app_id
	#print my_url
	# Get JSON data from URL	
	json_data = json.load(getUrlData(my_url))
	rates = json_data['rates']
	my_rates =  []
	for currency in currencies:
		#print currency
		#All currencies correlating to USD, we convert to SEK...
		USD = rates['SEK']
		if "USD" in currency:
			this_xrt = "%.2f" % USD
		else:
			this_xrt = "%.2f" % (USD/rates[currency])
		# After getting XRT, append it to
		#print type(this_xrt) 
		my_rates.append(this_xrt)
	#print my_rates
	return my_rates

def getPercent(now,then):
	percents = []
	nbr = len(now)	
	for i in range(0, nbr):
		#print float(now[i])
		#print float(then[i])
		percent = 100*(float(now[i]) - float(then[i]))/float(then[i])
		#print percent
		percents.append(str("%.2f" % percent))

	return percents
		 
	
## Function for getting XRT (Exchange Rate)
def changeXRT_count():
	global xrt_count
	xrt_count+=1
	if xrt_count >= len(my_currencies):
		xrt_count = 0

def getXRT():
	#Variable to save printed string to
	global exchange_rates 
	
	#print "get latest XRT"
	xrt_latest = getLatest(my_currencies)
	
	# Get dates
	date_today = datetime.now().date()
	date_oneday = str(date_today - timedelta(days = 1))
	date_oneweek = str(date_today - timedelta(days = 7))
	date_onemonth = str(date_today - timedelta(days = 30))
	date_oneyear = str(date_today - timedelta(days = 365))
	
	#Getting historical data
	xrt_oneday = getHistory(date_oneday, my_currencies)
	xrt_oneweek = getHistory(date_oneweek, my_currencies)
	xrt_onemonth = getHistory(date_onemonth, my_currencies)
	xrt_oneyear = getHistory(date_oneyear, my_currencies)	
	
	# Calculating percentages
	percent_oneday = getPercent(xrt_latest,xrt_oneday)
	percent_oneweek = getPercent(xrt_latest,xrt_oneweek)
	percent_onemonth = getPercent(xrt_latest,xrt_onemonth)
	percent_oneyear = getPercent(xrt_latest,xrt_oneyear)
	
	#Store to array of rates
	for i in range(0,len(my_currencies)):
		exchange_rates[i] = my_currencies[i]+": "+xrt_latest[i]+"kr "+percent_oneday[i]+"% "+percent_oneweek[i]+"% "+percent_onemonth[i]+"% "+percent_oneyear[i]+"% "
	
### News from Reddit World News
feed_url = "http://www.reddit.com/r/worldnews/.rss"
nbrTitles = 10 #number of headlines wanted
news_count = 0
curNews = []
for i in range(0,nbrTitles):
	curNews.append("N/A")
scrollCount = 0

# For changing which headline to show
def changenews_count():
	global news_count
	news_count+=1
	if news_count >= nbrTitles:
		news_count = 0
	global scrollCount
	scrollCount = 0
	return

# For getting news
def getNews():
	#Downloading feed
	d = feedparser.parse(feed_url)
	global curNews
	# Emptying curNews 
	curNews = []
	# Fill it up with news from feed
	for post in d.entries:
		#print "Printing headline"
		curNews.append(post.title)
	return
	
	

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
	str = "Bus 4: "+busTimes
	return str
def thirdString():
	"Creates third string for LCD"
	my_news = "          "+curNews[news_count]
	str = "News: "+my_news[scrollCount:scrollCount+34]
	global scrollCount
	scrollCount +=1
	return str
def fourthString():
	"Creates fourth string for LCD"
	global xrt_count
	str = exchange_rates[xrt_count]
	return str

def updateLCD():
	printLine(0,firstString())
        printLine(1,secondString())
	printLine(2,thirdString())
        printLine(3,fourthString())
	#print "LCD update"	

## Shutdown management
def shutdown_message():
	# Print shutdown message
	printLine(0,40*'-')
        printLine(1,13*' '+"Shutting down")
	printLine(2,5*' '+"Re-plug power cable to restart")
        printLine(3,40*'-')
	# Terminate LCD program
	quit()
	

### MAIN PROGRAM
# Remove old shutdown file
try:
	os.remove("/home/pi/RPi-LCD/shutdown")
except (OSError):
	pass

### SCHEDULING
# Run everything once at start of program
getBusTimes()
getTemp()
getXRT()
getNews()
updateLCD()

#Update bus times every 30 sec
schedule.every(30).seconds.do(getBusTimes)

# Update temp every 30 minutes
schedule.every(30).minutes.do(getTemp)

# Update exchange rate XRT every 12 hours
schedule.every(12).hours.do(getXRT)

# Update exchange rate counter ever 15 seconds
schedule.every(15).seconds.do(changeXRT_count)
 
# Update news every 30 mins
schedule.every(30).minutes.do(getNews)

# Update new counter every 20 seconds
schedule.every(20).seconds.do(changenews_count)

### MAIN FUNCTION
cnt=0
while True:
	schedule.run_pending()
	time.sleep(0.01)
	#Check if shutting down
	try:
		if os.path.isfile("/home/pi/RPi-LCD/shutdown"):
			print "Shutting down"
			shutdown_message()
	except (OSError):
		pass
	#Update LCD every 100 ms
	updateLCD()	
	
