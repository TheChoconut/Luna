import Queue
import os
import subprocess
import threading
import pwd, os
import linecache

from xbmcswift2 import xbmc, xbmcaddon

from resources.lib.di.requiredfeature import RequiredFeature
from resources.lib.model.inputmap import InputMap
from resources.lib.util.inputwrapper import InputWrapper
from resources.lib.util.stoppableinputhandler import StoppableInputHandler
from resources.lib.util.stoppablejshandler import StoppableJSHandler


def loop_lines(dialog, iterator):
    """
    :type dialog:   DialogProgress
    :type iterator: iterator
    """
    for line in iterator:
        dialog.update(0, line)


class MoonlightHelper:
    regex_connect = '(Connect to)'
    regex_moonlight = '(Moonlight Embedded)'
    regex_certificate_gen = '(Generating certificate...done)'
    regex_connection_failed = '(Can\'t connect to server)'

    def __init__(self, plugin, config_helper, logger):
        self.plugin = plugin
        self.config_helper = config_helper
        self.logger = logger
        self.internal_path = xbmcaddon.Addon().getAddonInfo('path')

    def create_ctrl_map(self, dialog, map_file):
        mapping_proc = subprocess.Popen(
                ['stdbuf', '-oL', self.config_helper.get_binary(), 'map', map_file, '-input',
                 self.plugin.get_setting('input_device', unicode)], stdout=subprocess.PIPE)

        lines_iterator = iter(mapping_proc.stdout.readline, b"")

        mapping_thread = threading.Thread(target=loop_lines, args=(dialog, lines_iterator))
        mapping_thread.start()

        success = False

        # TODO: Make a method or function from this
        while True:
            xbmc.sleep(1000)
            if not mapping_thread.isAlive():
                dialog.close()
                success = True
                break
            if dialog.iscanceled():
                mapping_proc.kill()
                dialog.close()
                success = False
                break

        if os.path.isfile(map_file) and success:

            return True
        else:

            return False

    def create_ctrl_map_new(self, dialog, map_file, device):
        # TODO: Implementation detail which should be hidden?
        input_queue = Queue.Queue()
        input_map = InputMap(map_file)
        input_device = None

        for handler in device.handlers:
            if handler[:-1] == 'js':
                input_device = os.path.join('/dev/input', handler)

        if not input_device:
            return False

        input_wrapper = InputWrapper(input_device, device.name, input_queue, input_map)
        input_wrapper.build_controller_map()

        print 'num buttons: %s' % input_wrapper.num_buttons
        print 'num_axes: %s' % input_wrapper.num_axes
        expected_input_number = input_wrapper.num_buttons + (input_wrapper.num_axes *2)

        js = StoppableJSHandler(input_wrapper, input_map)
        it = StoppableInputHandler(input_queue, input_map, dialog, expected_input_number)

        success = False

        while True:
            xbmc.sleep(1000)
            if not it.isAlive():
                js.stop()
                dialog.close()
                js.join(timeout=2)
                if input_map.status == InputMap.STATUS_DONE:
                    success = True
                if input_map.status == InputMap.STATUS_PENDING or input_map.status == InputMap.STATUS_ERROR:
                    success = False
                break
            if dialog.iscanceled():
                it.stop()
                js.stop()
                success = False
                it.join(timeout=2)
                js.join(timeout=2)
                dialog.close()
                break

        if os.path.isfile(map_file) and success:

            return True
        else:

            return False

    def pair_host(self, dialog):
        return RequiredFeature('connection-manager').request().pair(dialog)

    def parseline(self, data):
	data = [str(i) for i in data.split()]
	return str(data[2]).strip()

    def launch_game(self, game_id):
	import time

	os.setuid(os.getuid())
	subprocess.Popen('echo 0 > /sys/class/video/disable_video', shell=True)
	subprocess.Popen('systemctl stop kodi', shell=True)
	time.sleep(5)
	if os.path.isfile("/storage/moonlight/zerotier.conf"):
    		# read file
		with open("/storage/moonlight/zerotier.conf") as content_file:
    			content = content_file.read()
			if (content == "enabled"):
				p = subprocess.Popen("/opt/bin/zerotier-one -d", shell=True)

        self.config_helper.configure()

	subprocess.Popen('/storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/moonlight-heartbeat.sh &', shell=True)

	ADDRESS = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 3).strip())
	WIDTH = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 4).strip())
	HEIGHT = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 5).strip())
	FPS = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 6).strip())
	BITRATE = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 7).strip())
	PACKETSIZE = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 8).strip())
	SOPS = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 9).strip())
	REMOTE = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 10).strip())
	LOCALAUDIO = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 11).strip())
	DEBUG = self.parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 12).strip())

	with open("/storage/moonlight/launch_params.txt",'w') as f:
   		f.write(ADDRESS + "\n")
   		f.write(WIDTH + "\n")
   		f.write(HEIGHT + "\n")
   		f.write(FPS + "\n")
   		f.write(BITRATE + "\n")
		f.write(PACKETSIZE + "\n")
   		f.write(DEBUG + "\n")
		f.write("\n")
		f.write("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + game_id + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault")

	with open("/storage/moonlight/lastrun.txt","w") as f:
   		f.write(game_id)

	if (DEBUG.lower() == "false"):
		subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + "\"" + game_id + "\"" + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault > /storage/moonlight/debug.txt", shell=True)
	elif (DEBUG.lower() == "true"):
		subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + "\"" + game_id + "\"" + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault -debug > /storage/moonlight/debug.txt", shell=True)

    def list_games(self):
        return RequiredFeature('nvhttp').request().get_app_list()
