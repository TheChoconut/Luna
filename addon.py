import os
import subprocess
import requests
from resources.lib.di.requiredfeature import RequiredFeature

plugin = RequiredFeature('plugin').request()

addon_path = plugin.storage_path
addon_internal_path = plugin.addon.getAddonInfo('path')


@plugin.cached_route('/')
def index():
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
        
        return main_route()
    else:
        no_host_detected()

def no_host_detected():
    import xbmcgui
    core = RequiredFeature('core').request()
    core.check_script_permissions()
    xbmcgui.Dialog().ok(core.string('name'), core.string('configure_first'))
    del core
    binary_path = RequiredFeature('config-helper').request().binary_path
    if binary_path is None:
        confirmed = xbmcgui.Dialog().yesno('', 'Moonlight not detected! Would you like to download/setup the package now?', nolabel='No', yeslabel='Yes')
        if confirmed:
            get_moonlight()
    open_settings()

def main_route():
    default_fanart_path = addon_internal_path + '/fanart.jpg'
    return [
        {
            'label': 'Games',
            'thumbnail': addon_internal_path + '/resources/icons/controller.png',
            'fanart': default_fanart_path,
            'path': plugin.url_for(endpoint='show_games')
        }, {
            'label': 'Resume Running Game',
            'thumbnail': addon_internal_path + '/resources/icons/resume.png',
            'fanart': default_fanart_path,
            'path': plugin.url_for(endpoint='resume_game')
        }, {
            'label': 'Quit Current Game',
            'thumbnail': addon_internal_path + '/resources/icons/quit.png',
            'fanart': default_fanart_path,
            'path': plugin.url_for(endpoint='quit_game', refresh=False)
        }, {
            'label': 'ZeroTier Connect',
            'thumbnail': addon_internal_path + '/resources/icons/zerotier.png',
            'fanart': default_fanart_path,
            'path': plugin.url_for(endpoint='zerotier_connect')
        }, {
            'label': 'Settings',
            'thumbnail': addon_internal_path + '/resources/icons/cog.png',
            'fanart': default_fanart_path,
            'path': plugin.url_for(endpoint='open_settings')
        }
    ]

@plugin.route('/settings')
def open_settings():
    plugin.open_settings()
    core_monitor = RequiredFeature('core-monitor').request()
    core_monitor.onSettingsChanged()
    del core_monitor

@plugin.route('/settings/select-audio')
def select_audio_device():
    audio_controller = RequiredFeature('audio-controller').request()
    audio_controller.select_audio_device()

@plugin.route('/resume')
def resume_game():
    import xbmcgui
    import time
    if (check_host(plugin.get_setting('host', str)) == True):
        if plugin.get_setting('last_run', str):
            lastrun = plugin.get_setting('last_run', str)
            confirmed = xbmcgui.Dialog().yesno('', 'Resume playing ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
            if confirmed:
                start_running_game()
        else:
            xbmcgui.Dialog().ok('', 'Game not running! Nothing to do...')
    else:
        if plugin.get_setting('last_run', str):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                plugin.set_setting('last_run', '')
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

def start_running_game():
    lastrun = plugin.get_setting('last_run', str)
    if lastrun:
        game_controller = RequiredFeature('game-controller').request()
        game_controller.launch_game(lastrun)
        del game_controller


@plugin.route('/zerotier')
def zerotier_connect():
    import xbmcgui

    if process_exists('zerotier-one'):
        confirmed = xbmcgui.Dialog().yesno('', 'Disable ZeroTier Connection?', nolabel='No', yeslabel='Yes', autoclose=5000)
        if confirmed:
            subprocess.Popen(["/usr/bin/killall", "zerotier-one"], shell=False, start_new_session=True)
    else:
        confirmed = xbmcgui.Dialog().yesno('', 'Enable ZeroTier Connection?', nolabel='No', yeslabel='Yes', autoclose=5000)
        if confirmed:
            if os.path.isfile("/opt/bin/zerotier-one"):
                subprocess.Popen(["/opt/bin/zerotier-one", "-d"], shell=False, start_new_session=True)
            else:
                xbmcgui.Dialog().ok('', 'Missing ZeroTier binaries... Installation is required via Entware!')

def process_exists(process_name):
    progs = subprocess.check_output("ps -ef | grep " + process_name + " | grep -v grep | wc -l", shell=True)
    if '1' in progs:
        return True
    else:
        return False


@plugin.route('/quit/<refresh>')
def quit_game(refresh):
    import xbmcgui
    lastrun = plugin.get_setting('last_run', str)
    if (check_host(plugin.get_setting('host', str)) == True):
        if lastrun:
            if moonlight_quit_game(lastrun) and refresh == 'True':
                do_full_refresh()
        else:
            xbmcgui.Dialog().ok('No game running', 'This client doesn\'t have any running games on host.')
    else:
        if lastrun:
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                plugin.set_setting('last_run', None)
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

def moonlight_quit_game(lastrun):
    """
        Asks if user wants to quit the game. If true, calls moonlight process and sets the variable accordingly.
        Run this function only if host is running! 
    """
    import xbmcgui
    binary_path = RequiredFeature('config-helper').request().binary_path
    confirmed = xbmcgui.Dialog().yesno('', 'Confirm to quit ' + lastrun + '?', nolabel='No', yeslabel='Yes', autoclose=5000)
    if confirmed:
        try:
            subprocess.run([binary_path + "moonlight", "quit"], cwd=binary_path, timeout=10, check=True)
            plugin.set_setting('last_run', None)
        except Exception as e:
            xbmcgui.Dialog().ok('Error', 'There was an error while attempting to quit the game.\nPlease provide logs to the developers.')
            core = RequiredFeature('core').request()
            core.logger.error('Failed to quit moonlight game: %s' % e)
            print(e)
            del core
            return False
    return confirmed

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
    if plugin.get_setting('last_run', str):
        plugin.set_setting('last_run', '')
    core = RequiredFeature('core').request()
    confirmed = xbmcgui.Dialog().yesno(
        core.string('name'),
        core.string('reset_cache_warning')
    )
    del core
    if confirmed:
        scraper_chain = RequiredFeature('scraper-chain').request()
        scraper_chain.reset_cache()
        del scraper_chain

@plugin.route('/actions/get-moonlight')
def get_moonlight():
    import xbmcgui
    xbmcgui.Dialog().notification('Moonlight Updater', 'Grabbing latest Moonlight package...')
    subprocess.call('wget https://gist.githubusercontent.com/TheChoconut/fe550f8c19c11f71a85841f135eddecb/raw/ -qO - | bash', shell=True)
    config_helper = RequiredFeature('config-helper').request()
    config_helper.configure()
    binary_path = config_helper.binary_path
    del config_helper
    if binary_path is not None:
        xbmcgui.Dialog().ok('', 'Moonlight deployed successfully!')
    else:
        xbmcgui.Dialog().ok('', 'Failed! Please try again...')

@plugin.route('/actions/delete-key')
def delete_key():
    import xbmcgui
    import shutil
    import time

    crypto_key_dir = RequiredFeature('crypto-provider').request().get_key_dir()
    if os.path.isfile(crypto_key_dir + "client.p12"):
        check = xbmcgui.Dialog().yesno('', 'Are you sure you want to clear the pairing key?', nolabel='No', yeslabel='Yes')
        if check:
            shutil.rmtree(crypto_key_dir)
            #time.sleep(2)
            if not os.path.isdir(crypto_key_dir):
                xbmcgui.Dialog().ok('', 'Pairing key successfully removed!')
    else:
        xbmcgui.Dialog().ok('', 'A pairing key was not found! Nothing to do...')

def check_host(hostname):
    try:
        request = requests.get("http://" + hostname + ":47989/serverinfo?", timeout=10)
        return request.status_code == 200
    except (requests.exceptions.Timeout, requests.ConnectionError) as e:
        print(e)
        return False

@plugin.route('/games')
def show_games():
    import xbmcgui
    core = RequiredFeature('core').request()
    core.check_script_permissions()
    del core
    crypto_key_dir = RequiredFeature('crypto-provider').request().get_key_dir()
    if (check_host(plugin.get_setting('host', str)) == True):
        if os.path.isfile(crypto_key_dir + 'client.p12'):
            game_controller = RequiredFeature('game-controller').request()
            return plugin.finish(game_controller.get_games_as_list(), sort_methods=['label'])
        else:
            xbmcgui.Dialog().ok('Pair key not found!', 'Please pair with the host before proceeding...')
            open_settings()
    else:
        xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

@plugin.route('/games/refresh')
def do_full_refresh():
    import xbmc
    game_controller = RequiredFeature('game-controller').request()
    game_controller.get_games()
    del game_controller
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/games/launch/<game_id>')
def launch_game(game_id):
    import xbmcgui
    import time
    if (check_host(plugin.get_setting('host', str)) == True):
        lastrun = plugin.get_setting('last_run', str)
        
        if lastrun and lastrun != game_id:
            if moonlight_quit_game(lastrun) == False:
                return
        
        game_controller = RequiredFeature('game-controller').request()
        game_controller.launch_game(game_id)
        del game_controller
    else:
        if plugin.get_setting('last_run', str):
            cleanup = xbmcgui.Dialog().yesno('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue. \nIf you have restarted the host since your last session, you will need to remove residual data. \n\nWould you like to remove residual data now?', nolabel='No', yeslabel='Yes')
            if cleanup:
                plugin.set_setting('last_run', '')
        else:
            xbmcgui.Dialog().ok('Communication Error', 'The host is either not powered on or is asleep on the job. \nOtherwise, please troubleshoot a network issue.')

plugin.run()