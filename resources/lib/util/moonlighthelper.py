import Queue
import os
import subprocess
import threading
import pwd, os
import linecache
import signal

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

    def launch_game(self, game_id):
        import time
        import xbmcgui

        player = xbmc.Player()
        if player.isPlayingVideo():
            player.stop()

        if self.plugin.get_setting('last_run', str):
            xbmc.audioSuspend()

        xbmc.executebuiltin("Dialog.Close(busydialog)")
        xbmc.executebuiltin("Dialog.Close(notification)")

        if os.path.isfile("/storage/moonlight/aml_decoder.stats"):
            os.remove("/storage/moonlight/aml_decoder.stats")

        p = None

        if self.plugin.get_setting('zerotier', bool):
            if os.path.isfile("/opt/bin/zerotier-one"):
                p = subprocess.Popen(["/opt/bin/zerotier-one", "-d"], shell=False, preexec_fn=os.setsid)
            else:
                xbmcgui.Dialog().ok('', 'Missing ZeroTier binaries... Installation is required via Entware!')

        self.config_helper.configure()

        if self.plugin.get_setting('last_run', str):
            sp = subprocess.Popen(["moonlight", "stream", "-app", game_id, "-logging"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)
        else:
            sp = subprocess.Popen(["moonlight", "stream", "-app", game_id, "-logging", "-delay", "10"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)

        subprocess.Popen(['/storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/moonlight-heartbeat.sh'], shell=False)

        if not self.plugin.get_setting('last_run', str):
            xbmc.Player().play('/storage/.kodi/addons/script.luna/resources/statics/loading.mp4')
            time.sleep(8)
            xbmc.audioSuspend()
            time.sleep(2.5)
            xbmc.Player().stop()

        self.plugin.set_setting('last_run', game_id)

        subprocess.Popen(['killall', '-STOP', 'kodi.bin'], shell=False)	
        sp.wait()

        main = "pkill -x moonlight"
        heartbeat = "pkill -x moonlight-heart"
        print(os.system(main))
        print(os.system(heartbeat))

        xbmc.audioResume()

        if not (p is None):
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            p.wait()

        if os.path.isfile("/storage/moonlight/aml_decoder.stats"):				
            with open("/storage/moonlight/aml_decoder.stats") as stat_file:
                statistics = stat_file.read()
                if "StreamStatus = -1" in statistics:
                    confirmed = xbmcgui.Dialog().yesno('Stream initialisation failed...', 'Try running ' + game_id + ' again?', nolabel='No', yeslabel='Yes')
                    if confirmed:
                        self.launch_game(game_id)
                else:
                    xbmcgui.Dialog().ok('Stream statistics', statistics)

        game_controller = RequiredFeature('game-controller').request()
        game_controller.refresh_games()
        del game_controller
        xbmc.executebuiltin('Container.Refresh')
        xbmcgui.Dialog().notification('Information', game_id + ' is still running on host. Resume via Luna, ensuring to quit before the host is restarted!', xbmcgui.NOTIFICATION_INFO, False)

    def list_games(self):
        return RequiredFeature('nvhttp').request().get_app_list()
