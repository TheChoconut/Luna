import pwd, os
import os
import threading
import subprocess
import linecache
import signal
import requests

from resources.lib.di.requiredfeature import RequiredFeature

plugin = RequiredFeature('plugin').request()

addon_path = plugin.storage_path
addon_internal_path = plugin.addon.getAddonInfo('path')


@plugin.route('/')
def index():
    default_fanart_path = addon_internal_path + '/fanart.jpg'

    items = [
        {
            'label': 'Games',
            'thumbnail': addon_internal_path + '/resources/icons/controller.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='show_games'
                    )
        }, {
            'label': 'Resume Running Game',
            'thumbnail': addon_internal_path + '/resources/icons/resume.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='resume_game'
                    )
        }, {
            'label': 'Quit Current Game',
            'thumbnail': addon_internal_path + '/resources/icons/quit.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='quit_game'
                    )
        }, {

            'label': 'ZeroTier Connect',
            'thumbnail': addon_internal_path + '/resources/icons/zerotier.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='zerotier_connect'
                    )
        }, {
            'label': 'Settings',
            'thumbnail': addon_internal_path + '/resources/icons/cog.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='open_settings'
                    )
        }, {
            'label': 'Check For Update',
            'thumbnail': addon_internal_path + '/resources/icons/update.png',
            'properties': {
                    'fanart_image': default_fanart_path
            },
            'path': plugin.url_for(
                        endpoint='check_update'
                    )
        }
    ]

    return plugin.finish(items)


@plugin.route('/settings')
def open_settings():
    plugin.open_settings()
    core_monitor = RequiredFeature('core-monitor').request()
    core_monitor.onSettingsChanged()
    del core_monitor


@plugin.route('/settings/select-input')
def select_input_devices():
    from resources.lib.views.selectinput import SelectInput
    window = SelectInput('Select Input Devices')
    window.doModal()
    del window


@plugin.route('/settings/select-audio')
def select_audio_device():
    audio_controller = RequiredFeature('audio-controller').request()
    audio_controller.select_audio_device()

@plugin.route('/resume')
def resume_game():
    import xbmcgui
    import time
    os.setuid(os.getuid())
    if (check_host(plugin.get_setting('host', str)) == True):
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            # read file
            with open("/storage/moonlight/lastrun.txt") as content_file:
                lastrun = content_file.read()
                confirmed = xbmcgui.Dialog().yesno('', 'Resume playing ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
                if confirmed:
                    start_running_game()
        else:
            xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')
    else:
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                os.remove("/storage/moonlight/lastrun.txt") 
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

def start_running_game():
    import xbmcgui
    import time
    os.setuid(os.getuid())

    player = xbmc.Player()
    if player.isPlayingVideo():
        player.stop()

    xbmc.audioSuspend()

    if os.path.isfile("/storage/moonlight/aml_decoder.stats"):
        os.remove("/storage/moonlight/aml_decoder.stats")
    if os.path.isfile("/storage/moonlight/lastrun.txt"):
        # read file
        with open("/storage/moonlight/lastrun.txt") as content_file:
            lastrun = content_file.read()
            p = None
            with open("/sys/class/video/disable_video",'w') as f:
                f.write("0")
            time.sleep(5)
            if os.path.isfile("/storage/moonlight/zerotier.conf"):
                # read file
                with open("/storage/moonlight/zerotier.conf") as content_file:
                    content = content_file.read()
                    if (content == "enabled"):
                        if os.path.isfile("/opt/bin/zerotier-one"):
                            p = subprocess.Popen(["/opt/bin/zerotier-one", "-d"], shell=False, preexec_fn=os.setsid)
                        else:
                            xbmcgui.Dialog().ok('', 'Missing ZeroTier binaries... Installation is required via Entware!')

            sp = subprocess.Popen(["moonlight", "stream", "-app", lastrun, "-logging"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)

            subprocess.Popen(['/storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/moonlight-heartbeat.sh'], shell=False)
            subprocess.Popen(['killall', '-STOP', 'kodi.bin'], shell=False)
            sp.wait()

            main = "pkill -x moonlight"
            heartbeat = "pkill -x moonlight-heart"
            print(os.system(main))
            print(os.system(heartbeat))

            xbmc.audioResume()

            if not (p is None):
                #xbmcgui.Dialog().ok('', 'ZeroTier connection closed!')
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                p.wait()

            if os.path.isfile("/storage/moonlight/aml_decoder.stats"):
                with open("/storage/moonlight/aml_decoder.stats") as stat_file:
                    statistics = stat_file.read()
                    if "StreamStatus = -1" in statistics:
                        #xbmcgui.Dialog().ok('Error', 'Stream initialisation failed...')
                        confirmed = xbmcgui.Dialog().yesno('Stream initialisation failed...', 'Try running ' + lastrun + ' again?', nolabel='No', yeslabel='Yes')
                        if confirmed:
                            start_running_game()

                    else:
                        xbmcgui.Dialog().ok('Stream statistics', statistics)

            xbmcgui.Dialog().notification('Information', lastrun + ' is still running on host. Resume via Luna, ensuring to quit before the host is restarted!', xbmcgui.NOTIFICATION_INFO, 15000, False)


@plugin.route('/zerotier')
def zerotier_connect():
    os.setuid(os.getuid())
    import xbmcgui

    if not os.path.isfile("/storage/moonlight/zerotier.conf"):
        f = open("/storage/moonlight/zerotier.conf", "w")
        f.write("disabled")
        f.close()

    # read file
    with open("/storage/moonlight/zerotier.conf") as content_file:
        content = content_file.read()
        if (content == "disabled"):
            confirmed = xbmcgui.Dialog().yesno('', 'Enable ZeroTier Connection?', nolabel='No', yeslabel='Yes', autoclose=5000)
            if confirmed:
                f = open("/storage/moonlight/zerotier.conf", "w")
                f.write("enabled")
                f.close()

        elif (content == "enabled"):
            confirmed = xbmcgui.Dialog().yesno('', 'Disable ZeroTier Connection?', nolabel='No', yeslabel='Yes', autoclose=5000)
            if confirmed:
                f = open("/storage/moonlight/zerotier.conf", "w")
                f.write("disabled")
                f.close()


@plugin.route('/quit')
def quit_game():
    os.setuid(os.geteuid())
    import xbmcgui
    if (check_host(plugin.get_setting('host', str)) == True):
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            # read file
            with open("/storage/moonlight/lastrun.txt") as content_file:
                lastrun = content_file.read()
                confirmed = xbmcgui.Dialog().yesno('', 'Confirm to quit ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
                if confirmed:
                    subprocess.Popen(["moonlight", "quit"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)
                    os.remove("/storage/moonlight/lastrun.txt") 
                    xbmcgui.Dialog().ok('', lastrun + ' successfully closed!')
                    main = "pkill -x moonlight"
                    print(os.system(main))
        else:
            xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')
    else:
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                os.remove("/storage/moonlight/lastrun.txt") 
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')


@plugin.route('/quit_game')
def quit_game_sub():
    os.setuid(os.geteuid())
    import xbmcgui
    if (check_host(plugin.get_setting('host', str)) == True):
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            # read file
            with open("/storage/moonlight/lastrun.txt") as content_file:
                lastrun = content_file.read()
                confirmed = xbmcgui.Dialog().yesno('', 'Confirm to quit ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
                if confirmed:
                    subprocess.Popen(["moonlight", "quit"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)
                    os.remove("/storage/moonlight/lastrun.txt") 
                    xbmc.executebuiltin('Container.Refresh')
                    xbmcgui.Dialog().ok('', lastrun + ' successfully closed!')
                    main = "pkill -x moonlight"
                    print(os.system(main))
        else:
            xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')
    else:
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                os.remove("/storage/moonlight/lastrun.txt") 
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')


@plugin.route('/update')
def check_update():
    updater = RequiredFeature('update-service').request()
    update = updater.check_for_update(True)
    if update is not None:
        updater.initiate_update(update)


@plugin.route('/actions/create-mapping')
def create_mapping():
    config_controller = RequiredFeature('config-controller').request()
    config_controller.create_controller_mapping()
    del config_controller


@plugin.route('/actions/pair-host')
def pair_host():
    config_controller = RequiredFeature('config-controller').request()
    config_controller.pair_host()
    del config_controller

@plugin.route('/actions/reset-cache')
def reset_cache():
    import xbmcgui
    if os.path.isfile("/storage/moonlight/lastrun.txt"):
        os.remove("/storage/moonlight/lastrun.txt")
    core = RequiredFeature('core').request()
    confirmed = xbmcgui.Dialog().yesno(
            core.string('name'),
            core.string('reset_cache_warning')
    )

    if confirmed:
        scraper_chain = RequiredFeature('scraper-chain').request()
        scraper_chain.reset_cache()
        del scraper_chain

    del core

@plugin.route('/actions/get-moonlight')
def get_moonlight():
    import xbmcgui
    xbmcgui.Dialog().notification('Moonlight Updater', 'Grabbing latest Moonlight package...')
    subprocess.call('wget https://gist.githubusercontent.com/TheChoconut/fe550f8c19c11f71a85841f135eddecb/raw/ -qO - | bash', shell=True)
    if os.path.isfile("/storage/moonlight/moonlight"):
        xbmcgui.Dialog().ok('', 'Moonlight deployed successfully!')
    else:
        xbmcgui.Dialog().ok('', 'Failed! Please try again...')
    

@plugin.route('/actions/patch-osmc')
def patch_osmc_skin():
    skinpatcher = RequiredFeature('skin-patcher').request()
    skinpatcher.patch()
    del skinpatcher
    import xbmc
    xbmc.executebuiltin('ReloadSkin')


@plugin.route('/actions/rollback-osmc')
def rollback_osmc_skin():
    import xbmc
    skinpatcher = RequiredFeature('skin-patcher').request()
    skinpatcher.rollback()
    del skinpatcher
    xbmc.executebuiltin('ReloadSkin')


def check_host(hostname):
    try:
        request = requests.get("http://" + hostname + ":47989/serverinfo?", timeout=10)
        if request.status_code == 200:
            return True
        return False
    except (requests.exceptions.Timeout, requests.ConnectionError), e:
        print e
        return False


@plugin.route('/games')
def show_games():
    import xbmcgui
    if os.path.isfile("/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf"):
        os.remove("/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf")
    if (check_host(plugin.get_setting('host', str)) == True):
        game_controller = RequiredFeature('game-controller').request()
        plugin.set_content('movies')
        return plugin.finish(game_controller.get_games_as_list(), sort_methods=['label'])
    else:
        xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

@plugin.route('/games/refresh')
def do_full_refresh():
    import xbmc
    game_controller = RequiredFeature('game-controller').request()
    game_controller.get_games()
    del game_controller
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/games/info/<game_id>')
def show_game_info(game_id):
    from resources.lib.views.gameinfo import GameInfo
    core = RequiredFeature('core').request()
    game = core.get_storage().get(game_id)
    cache_fanart = game.get_selected_fanart()
    cache_poster = game.get_selected_poster()
    window = GameInfo(game, game.name)
    window.doModal()
    del window
    if cache_fanart != game.get_selected_fanart() or cache_poster != game.get_selected_poster():
        import xbmc
        xbmc.executebuiltin('Container.Refresh')
    del core
    del game


@plugin.route('/games/launch/<game_id>')
def launch_game(game_id):
    os.setuid(os.geteuid())
    import xbmcgui
    import time
    if (check_host(plugin.get_setting('host', str)) == True):
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            # read file
            with open("/storage/moonlight/lastrun.txt") as content_file:
                lastrun = content_file.read()
                if (lastrun != game_id):
                    confirmed = xbmcgui.Dialog().yesno('', 'Confirm to quit ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
                    if confirmed:
                        subprocess.Popen(["moonlight", "quit"], cwd="/storage/moonlight", env={'LD_LIBRARY_PATH': '/storage/moonlight'}, shell=False, preexec_fn=os.setsid)
                        os.remove("/storage/moonlight/lastrun.txt")
                        time.sleep(2);
                        main = "pkill -x moonlight"
                        print(os.system(main))
                        time.sleep(2);
                        core = RequiredFeature('core').request()
                        game_controller = RequiredFeature('game-controller').request()
                        core.logger.info('Launching game %s' % game_id)
                        game_controller.launch_game(game_id)
                        del core
                        del game_controller
                else:
                    core = RequiredFeature('core').request()
                    game_controller = RequiredFeature('game-controller').request()
                    core.logger.info('Launching game %s' % game_id)
                    game_controller.launch_game(game_id)
                    del core
                    del game_controller			
        else:
            core = RequiredFeature('core').request()
            game_controller = RequiredFeature('game-controller').request()
            core.logger.info('Launching game %s' % game_id)
            game_controller.launch_game(game_id)
            del core
            del game_controller
    else:
        if os.path.isfile("/storage/moonlight/lastrun.txt"):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                os.remove("/storage/moonlight/lastrun.txt") 
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')


@plugin.route('/games/launch-from-widget/<xml_id>')
def launch_game_from_widget(xml_id):
    core = RequiredFeature('core').request()
    game_id = int(xml_id)
    internal_game_id = plugin.get_storage('sorted_game_storage').get(game_id)

    game_controller = RequiredFeature('game-controller').request()
    core.logger.info('Launching game %s' % internal_game_id)
    game_controller.launch_game(internal_game_id)

    del core
    del game_controller

if __name__ == '__main__':
    core = RequiredFeature('core').request()
    update_storage = plugin.get_storage('update', TTL=24*60)
    if not update_storage.get('checked'):
        updater = RequiredFeature('update-service').request()
        updater.check_for_update()
        del updater
    core.check_script_permissions()

    if plugin.get_setting('host', str):
        game_refresh_required = False

        try:
            from resources.lib.model.game import Game
            if plugin.get_storage('game_version')['version'] != Game.version:
                game_refresh_required = True
        except KeyError:
            game_refresh_required = True

        if game_refresh_required:
            game_controller = RequiredFeature('game-controller').request()
            game_controller.get_games()
            del game_controller

        plugin.run()
        del plugin
        del core
    else:
        import xbmcgui
        core = RequiredFeature('core').request()
        xbmcgui.Dialog().ok(
                core.string('name'),
                core.string('configure_first')
        )
        del core
        if not os.path.isfile("/storage/moonlight/moonlight"):
            confirmed = xbmcgui.Dialog().yesno('', 'Moonlight not detected! Would you like to download/setup the package now?', nolabel='No', yeslabel='Yes')
            if confirmed:
                subprocess.call('wget https://gist.githubusercontent.com/TheChoconut/fe550f8c19c11f71a85841f135eddecb/raw/ -qO - | bash', shell=True)
                if os.path.isfile("/storage/moonlight/moonlight"):
                    xbmcgui.Dialog().ok('', 'Moonlight deployed successfully!')
                else:
                    xbmcgui.Dialog().ok('', 'Failed! Please try again...')
        open_settings()