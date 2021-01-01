#!/usr/bin/sh

IFS=$'\n'
count=0

sleep 10

while [ `cat /sys/class/video/disable_video` -eq 1 ]; do
    echo Setting disable_video flag to zero...
    echo 0 > /sys/class/video/disable_video
done

while [ true ]; do
    status="$(ps -ef | grep "[m]oonlight stream"* | wc -l)"
    if [ ${status} -ne 1 ]; then
        echo ${status}
        echo 'Moonlight is NOT running' 
        echo 1 > /sys/class/video/disable_video
        echo 0 > /sys/class/graphics/fb0/blank
        echo 0 > /sys/class/graphics/fb1/blank
        killall -CONT kodi.bin
        exit
    else
        echo 'Moonlight is running'
        if [ -f "/storage/moonlight/aml_decoder.stats" ]; then
            failed="$(sed '1!d' "/storage/moonlight/aml_decoder.stats" | awk 'END {print $NF}')"
            if [[ ${failed} == "-1" ]]; then
                killall moonlight
                echo 1 > /sys/class/video/disable_video
                echo 0 > /sys/class/graphics/fb0/blank
                echo 0 > /sys/class/graphics/fb1/blank
                killall -CONT kodi.bin
                exit
            fi
        fi

        if [ $count -lt 2 ]; then
            for i in $(lsusb | awk '{ print $6 }'); do
                if [ $(lsusb -v -d $i | grep InterfaceClass | awk 'END {print $(NF-2), $(NF-1), $NF}') == "Human Interface Device" ]; then
                    echo "$i"
                    hid=$(lsusb -d "$i" | awk '{ print $4}' | sed 's/.$//')
                    echo "$hid"
                    python /storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/reset_usb.py -d $hid
                fi
            done
            count=$((count+1))
        fi
        sleep 2
    fi
done

