import re
import subprocess
import threading
import os
import sys

import xbmc
from resources.lib.di.requiredfeature import RequiredFeature
from resources.lib.nvhttp.pairingmanager.abstractpairingmanager import AbstractPairingManager


class SimplePairingManager(AbstractPairingManager):
    def __init__(self, crypto_provider):
        self.crypto_provider = crypto_provider
        self.config_helper = RequiredFeature('config-helper').request()
        self.logger = RequiredFeature('logger').request()

    def pair(self, nvhttp, server_info, dialog):
        self.logger.info('[MoonlightHelper] - Attempting to pair host: ' + self.config_helper.host_ip)
        pairing_proc = subprocess.Popen(["./moonlight", "pair"], cwd="/storage/moonlight", encoding='utf-8', shell=False, stdout=subprocess.PIPE)
        lines_iterator = iter(pairing_proc.stdout.readline, "")

        pairing_thread = threading.Thread(target=self.loop_lines, args=(self.logger, lines_iterator, dialog))
        pairing_thread.start()

        while pairing_proc.poll() is None:
            xbmc.sleep(1000)

        new_server_info = nvhttp.get_server_info()
        if self.get_pair_state(nvhttp, new_server_info) == self.STATE_PAIRED:
            return self.STATE_PAIRED
        else:
            return self.STATE_FAILED

        main = "pkill -x moonlight"
        print(os.system(main))

    def loop_lines(self, logger, iterator, dialog):
        pin_regex = r'^Please enter the following PIN on the target PC: (\d{4})'
        for line in iterator:
            if line.strip() == "":
                break
            match = re.match(pin_regex, line)
            if match:
                self.update_dialog(match.group(1), dialog)
                break
