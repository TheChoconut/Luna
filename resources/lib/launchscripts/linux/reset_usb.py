#!/usr/bin/env python3
import os
import argparse
import subprocess

path='/sys/bus/usb/devices/'

def runbash(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.read().strip()
    return out

def reset_device(dev_num):
    sub_dirs = []
    for root, dirs, files in os.walk(path):
            for name in dirs:
                    sub_dirs.append(os.path.join(root, name))

    dev_found = 0
    for sub_dir in sub_dirs:
            if True == os.path.isfile(sub_dir+'/devnum'):
                    fd = open(sub_dir+'/devnum','r')
                    line = fd.readline()
                    if int(dev_num) == int(line):
                            print('Your device is at: '+sub_dir)
                            dev_found = 1
                            break

                    fd.close()

    if dev_found == 1:
            reset_file = sub_dir+'/authorized'
            runbash('echo 0 > '+reset_file) 
            runbash('echo 1 > '+reset_file) 
            print('Device reset successful')

    else:
            print("No such device")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--devnum', dest='devnum')
    args = parser.parse_args()

    if args.devnum is None:
            print('Usage:usb_reset.py -d <device_number> \nThe device    number can be obtained from lsusb command result')
            return

    reset_device(args.devnum)

if __name__=='__main__':
    main()