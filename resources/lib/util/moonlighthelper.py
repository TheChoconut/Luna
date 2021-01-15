import os
import subprocess
import threading
import time

from xbmcswift2 import xbmc, xbmcaddon, xbmcgui
from resources.lib.di.requiredfeature import RequiredFeature

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
                [self.config_helper.get_binary(), 'map', map_file, '-input',
                 self.plugin.get_setting('input_device', str)], stdout=subprocess.PIPE)

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
        try:
            import queue
            from resources.lib.util.inputwrapper import InputWrapper
            from resources.lib.model.inputmap import InputMap
            from resources.lib.util.stoppableinputhandler import StoppableInputHandler
            from resources.lib.util.stoppablejshandler import StoppableJSHandler
        except:
            print("Failed to initialize wanted imports...")
            return False

        # TODO: Implementation detail which should be hidden?
        input_queue = queue.Queue()
        input_map = InputMap(map_file)
        input_device = None

        for handler in device.handlers:
            if handler[:-1] == 'js':
                input_device = os.path.join('/dev/input', handler)

        if not input_device:
            return False

        input_wrapper = InputWrapper(input_device, device.name, input_queue, input_map)
        input_wrapper.build_controller_map()

        print('num buttons: %s' % input_wrapper.num_buttons)
        print('num_axes: %s' % input_wrapper.num_axes)
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

        return os.path.isfile(map_file) and success

    def pair_host(self, dialog):
        return RequiredFeature('connection-manager').request().pair(dialog)

    def launch_game_thread(self, isResumeMode, binary_path, game_id):
        player = xbmc.Player()
        launchscript_cwd = self.internal_path + 'resources/lib/launchscripts/linux/'
        moonlight_args = [binary_path + "moonlight", "stream", "-app", game_id, "-logging"]
        showIntro = self.plugin.get_setting('show_intro', bool)
        if self.plugin.get_setting('enable_moonlight_alt_aml_algorithm', bool):
            moonlight_args.append('-altdecalgorithm')
        if not isResumeMode:
            self.plugin.set_setting('last_run', game_id)
            if showIntro:
                moonlight_args = moonlight_args + ["-delay", "10"]

        try:
            moonlight_cmd = subprocess.Popen(moonlight_args, cwd=binary_path, start_new_session=True)
            heart = subprocess.Popen([launchscript_cwd + 'moonlight-heartbeat.sh'], cwd=launchscript_cwd, start_new_session=True)

            if showIntro and not isResumeMode:
                player.play(self.internal_path + '/resources/statics/loading.mp4')
                time.sleep(8)
                xbmc.audioSuspend()
                time.sleep(2.5)
                player.stop()

            subprocess.Popen(['killall', '-STOP', 'kodi.bin'])	
            moonlight_cmd.wait()
            heart.wait()

            xbmcgui.Dialog().notification('Information', game_id + ' is still running on host. Resume via Luna, ensuring to quit before the host is restarted!', xbmcgui.NOTIFICATION_INFO, False)
        except Exception as e:
            print("Failed to execute moonlight process.")
            print(e)
        finally:
            xbmc.audioResume()
            xbmc.executebuiltin("InhibitScreensaver(false)")
            if os.path.isfile(binary_path + "aml_decoder.stats"):				
                with open(binary_path + "aml_decoder.stats") as stat_file:
                    statistics = stat_file.read()
                    if "StreamStatus = -1" in statistics:
                        confirmed = xbmcgui.Dialog().yesno('Stream initialisation failed...', 'Try running ' + game_id + ' again?', nolabel='No', yeslabel='Yes')
                        if confirmed:
                            self.launch_game(game_id)
                    else:
                        xbmcgui.Dialog().ok('Stream statistics', statistics)

    def launch_game(self, game_id):

        binary_path = self.config_helper.binary_path
        if binary_path is None:
            xbmcgui.Dialog().ok("Missing binaries", "Couldn\'t detect moonlight binary.\r\nPlease check your setup.")
            return

        player = xbmc.Player()
        if player.isPlayingVideo():
            player.stop()

        isResumeMode = bool(self.plugin.get_setting('last_run',str))
        if isResumeMode:
            xbmc.audioSuspend()

        xbmc.executebuiltin("Dialog.Close(busydialog)")
        xbmc.executebuiltin("Dialog.Close(notification)")
        xbmc.executebuiltin("InhibitScreensaver(true)")

        if os.path.isfile(binary_path + "aml_decoder.stats"):
            os.remove(binary_path + "aml_decoder.stats")

        launch_thread = threading.Thread(target=self.launch_game_thread, args=(isResumeMode, binary_path, game_id))
        launch_thread.start()

    def list_games(self):
        return RequiredFeature('nvhttp').request().get_app_list()
