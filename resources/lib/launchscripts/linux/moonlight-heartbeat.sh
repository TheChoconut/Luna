#!/usr/bin/sh

IFS=$'\n'
count=0

find /sys/bus/usb/devices/*/authorized -exec sh -c 'echo 0 > ${0}; echo 1 > ${0}' {} \;
mv logfile logfile.old
moonlight stream -app "$1" >> logfile 2>&1

# Reset to default settings.
echo 0 > /sys/class/graphics/fb0/blank
echo 0 > /sys/class/graphics/fb1/blank
echo "rm default" > /sys/class/vfm/map
echo "add default decoder ppmgr amlvideo deinterlace amvideo" > /sys/class/vfm/map
killall -CONT kodi.bin