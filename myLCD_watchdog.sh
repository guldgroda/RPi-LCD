#!/bin/bash
#
# watchdog
#
# Run as a cron job to keep an eye on what_to_monitor which should always
# be running. Restart what_to_monitor and send notification as needed.
#
# This needs to be run as root or a user that can start system services.
#
# Revisions: 0.1 (20100506), 0.2 (20100507)

NAME=myLCD
START=/home/pi/RPi-LCD/myLCD.py
# NOTIFY=person1email
# NOTIFYCC=person2email
GREP=/bin/grep
PS=/bin/ps
NOP=/bin/true
DATE=/bin/date
# MAIL=/bin/mail
RM=/bin/rm

$PS -ef|$GREP -v grep|$GREP $NAME >/dev/null 2>&1
case "$?" in
   0)
   # It is running in this case so we do nothing.
   $NOP
   ;;
   1)
   echo "$NAME is NOT RUNNING. Starting $NAME and sending notices."
   /bin/usr/python $START 2>&1 >/dev/null &
   NOTICE=/tmp/watchdog.txt
   echo "$NAME was not running and was started on `$DATE`" > $NOTICE
   # $MAIL -n -s "watchdog notice" -c $NOTIFYCC $NOTIFY < $NOTICE
   $RM -f $NOTICE
   ;;
esac

exit
