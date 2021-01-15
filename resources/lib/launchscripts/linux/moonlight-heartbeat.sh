#!/usr/bin/sh

IFS=$'\n'
count=0

sleep 10

while [ true ]; do
    status="$(ps -ef | grep "[m]oonlight stream"* | wc -l)"
    if [ ${status} -ne 1 ]; then
        echo ${status}
        echo 'Moonlight is NOT running'

        # Just in case something fails, reset the framebuffers.
        echo 0 > /sys/class/graphics/fb0/blank
        echo 0 > /sys/class/graphics/fb1/blank
        killall -CONT kodi.bin
        exit
    else
        echo 'Moonlight is running'
        if [ -f "aml_decoder.stats" ]; then
            failed="$(sed '1!d' "aml_decoder.stats" | awk 'END {print $NF}')"
            if [[ ${failed} == "-1" ]]; then
                killall moonlight
                # Just in case something fails, reset the framebuffers.
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
                    python reset_usb.py -d $hid
                fi
            done
            count=$((count+1))
        fi
        sleep 2
    fi
done

