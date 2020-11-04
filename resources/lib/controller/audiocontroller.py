import xbmcgui
import subprocess
import os
import re


class AudioController(object):
    def __init__(self, audio_manager, config_helper, plugin):
        self.audio_manager = audio_manager
        self.config_helper = config_helper
        self.plugin = plugin

    def select_audio_device(self):
        device_list = [dev.name for dev in self.audio_manager.devices]

        for line in subprocess.check_output('aplay -l | grep card', shell=True).split('\n'):
            if line.strip():
                device_list.append(line)

        audio_device = xbmcgui.Dialog().select('Choose Audio Device', device_list)

        if audio_device != -1:
            device_name = device_list[audio_device]

            CARDS_REGEX = r'(?:card ?)([^:]*).*(?:device ?)([^:]*)'

            match = re.match(CARDS_REGEX, device_name)

            index1 = match.group(1)
            index2 = match.group(2)

            audio_parameter = 'hw:' + index1 + ',' + index2

            self.plugin.set_setting('audio_device_parameter', audio_parameter)
        return
