#!/usr/bin/bash

sleep 10

while [ true ]; do
        status="$(pidof moonlight | wc -w)"
        if [ ${status} -ne 1 ]; then
            echo 1 > /sys/class/video/disable_video
            systemctl start kodi
            exit
        else
            sleep 2
        fi
done
