#!/usr/bin/sh

resume() {
  killall -CONT kodi.bin
}

trap resume EXIT

killall -STOP kodi.bin

# prevent black screen after playing video
echo 1 > /sys/class/graphics/fb0/blank
echo "rm default" > /sys/class/vfm/map
echo add default decoder ppmgr deinterlace amlvideo amvideo > /sys/class/vfm/map

mv logfile logfile.old
LD_PRELOAD="/usr/local/lib/libmoonlight-aml.so /usr/osmc/lib/libamavutils.so /usr/osmc/lib/libamadec.so /usr/osmc/lib/libamcodec.so" \
  moonlight stream \
  -platform aml \
  -app "$@" >> logfile 2>&1
