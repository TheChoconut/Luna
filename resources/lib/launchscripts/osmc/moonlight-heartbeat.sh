#!/usr/bin/sh

IFS=$'\n'
count=0

sleep 2
while [ true ]; do
        status="$(ps -ef | grep "[m]oonlight stream"* | wc -l)"
        if [ ${status} -ne 1 ]; then
	    echo ${status}
	    echo 'Moonlight is NOT running' 
            echo 1 > /sys/class/video/disable_video
	    killall -CONT kodi.bin
            exit
        else
	    echo 'Moonlight is running'
	    if [ $count = 0 ]; then
		for i in $(lsusb | awk '{ print $6 }'); do
			if [ $(lsusb -v -d $i 2>&1 | grep 'Mouse') ]; then
				mouse=$(lsusb -d "$i" | awk '{ print $4}' | sed 's/.$//')
				python /storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/reset_usb.py -d $mouse
			fi
		done
		count=1
	    fi
            sleep 2
        fi
done
