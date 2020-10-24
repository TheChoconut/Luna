import pwd, os
import os
import threading
import subprocess
import linecache

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
    if os.path.isfile("/storage/moonlight/lastrun.txt"):
    	# read file
	with open("/storage/moonlight/lastrun.txt") as content_file:
		lastrun = content_file.read()
    		confirmed = xbmcgui.Dialog().yesno('', 'Resume playing game ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
		if confirmed:
			subprocess.Popen('echo 0 > /sys/class/video/disable_video', shell=True)
			subprocess.Popen('systemctl stop kodi', shell=True)
			time.sleep(5)
			if os.path.isfile("/storage/moonlight/zerotier.conf"):
    				# read file
				with open("/storage/moonlight/zerotier.conf") as content_file:
    					content = content_file.read()
					if (content == "enabled"):
						p = subprocess.Popen("/opt/bin/zerotier-one -d", shell=True)

			subprocess.Popen('/storage/.kodi/addons/script.luna/resources/lib/launchscripts/osmc/moonlight-heartbeat.sh &', shell=True)

			ADDRESS = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 3).strip())
			WIDTH = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 4).strip())
			HEIGHT = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 5).strip())
			FPS = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 6).strip())
			BITRATE = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 7).strip())
			PACKETSIZE = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 8).strip())
			SOPS = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 9).strip())
			REMOTE = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 10).strip())
			LOCALAUDIO = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 11).strip())
			DEBUG = parseline(linecache.getline('/storage/.kodi/userdata/addon_data/script.luna/.storage/luna.conf', 12).strip())

			with open("/storage/moonlight/launch_params.txt",'w') as f:
   				f.write(ADDRESS + "\n")
   				f.write(WIDTH + "\n")
   				f.write(HEIGHT + "\n")
   				f.write(FPS + "\n")
   				f.write(BITRATE + "\n")
   				f.write(PACKETSIZE + "\n")
   				f.write(DEBUG + "\n")
				f.write("\n")
				f.write("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + lastrun + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault")

			if (DEBUG.lower() == "false"):
				subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + lastrun + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault > /storage/moonlight/debug.txt", shell=True)
			elif (DEBUG.lower() == "true"):
				subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight stream " + ADDRESS + " -app " + lastrun + " -width " + WIDTH + " -height " + HEIGHT + " -fps " + FPS + " -bitrate " + BITRATE + " -packetsize " + PACKETSIZE + " -codec h265 -audio sysdefault -debug > /storage/moonlight/debug.txt", shell=True)



    else:
    	xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')

def parseline(data):
    data = [str(i) for i in data.split()]
    return str(data[2]).strip()


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
			p = subprocess.Popen("echo -n enabled > /storage/moonlight/zerotier.conf", shell=True)

	elif (content == "enabled"):
		confirmed = xbmcgui.Dialog().yesno('', 'Disable ZeroTier Connection?', nolabel='No', yeslabel='Yes', autoclose=5000)
		if confirmed:
			p = subprocess.Popen("echo -n disabled > /storage/moonlight/zerotier.conf", shell=True)


@plugin.route('/quit')
def quit_game():
    os.setuid(os.geteuid())
    import xbmcgui
    if os.path.isfile("/storage/moonlight/lastrun.txt"):
	# read file
    	with open("/storage/moonlight/lastrun.txt") as content_file:
    		lastrun = content_file.read()
		confirmed = xbmcgui.Dialog().yesno('', 'Confirm to quit running game, ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
		if confirmed:
			subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight quit", shell=True)
    			os.remove("/storage/moonlight/lastrun.txt") 
    			import xbmcgui
    			xbmcgui.Dialog().ok('', lastrun + ' successfully closed!')
    else:
    	xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')


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


@plugin.route('/games')
def show_games():
    game_controller = RequiredFeature('game-controller').request()
    plugin.set_content('movies')
    return plugin.finish(game_controller.get_games_as_list(), sort_methods=['label'])


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
    if os.path.isfile("/storage/moonlight/lastrun.txt"):
    	# read file
	with open("/storage/moonlight/lastrun.txt") as content_file:
    		content = content_file.read()
		if (content != game_id):
    			confirmed = xbmcgui.Dialog().yesno('', 'Quit running game ' + content + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
			if confirmed:
    				subprocess.Popen("LD_LIBRARY_PATH=/storage/moonlight /storage/moonlight/moonlight quit", shell=True)
    				os.remove("/storage/moonlight/lastrun.txt") 
				time.sleep(5);
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
