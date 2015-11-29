# RPi-LCD
Using a Raspberry Pi and a 40x4 LCD


Uses following packages:

schedule 0.3.2 - sudo pip install schedule

RPLCD - sudo pip install RPLCD

Add a row to SU crontab

sudo crontab -e

add this:

@reboot /bin/bash /path/to/script/myLCD_watchdog.sh

