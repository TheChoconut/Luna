#!/usr/bin/sh

IFS=$'\n'
count=0

mv logfile logfile.old
moonlight stream -game "$1" >> logfile 2>&1 &
sleep 3

while [ true ]; do
    status="$(ps -ef | grep "[m]oonlight stream"* | wc -l)"
    if [ ${status} -ne 1 ]; then
        echo ${status}
        echo 'Moonlight is NOT running'

        # Just in case something fails, reset the framebuffers.
        echo 0 > /sys/class/graphics/fb0/blank
        echo 0 > /sys/class/graphics/fb1/blank

        echo "rm default" > /sys/class/vfm/map
        echo "add default decoder ppmgr amlvideo deinterlace amvideo" > /sys/class/vfm/map

        killall -CONT kodi.bin
        exit
    else
        echo 'Moonlight is running'

        if [ $count -lt 2 ]; then
            find /sys/bus/usb/devices/*/authorized -exec sh -c 'echo 0 > ${0}; echo 1 > ${0}' {} \;
            count=$((count+1))
        fi
        sleep 2
    fi
done

