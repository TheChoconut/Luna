import xbmcgui
import os
import subprocess
from resources.lib.di.requiredfeature import RequiredFeature
from resources.lib.model.game import Game


class GameController:
    def __init__(self, plugin, core, moonlight_helper, scraper_chain, logger):
        self.plugin = plugin
        self.core = core
        self.moonlight_helper = moonlight_helper
        self.scraper_chain = scraper_chain
        self.logger = logger

    def get_games(self):
        """
        Fills local game storage with scraper results (if enabled) or game names (if scrapers are disabled)
        """
        game_list = self.moonlight_helper.list_games()

        if game_list is None or len(game_list) == 0:
            xbmcgui.Dialog().notification(
                self.core.string('name'),
                'Getting game list failed. This usually means your host wasn\'t paired properly.',
                '',
                20000
            )
            return

        progress_dialog = xbmcgui.DialogProgress()
        progress_dialog.create(
            self.core.string('name'),
            'Refreshing Game List'
        )

        if game_list is None or len(game_list) == 0:
            xbmcgui.Dialog().notification(
                self.core.string('name'),
                self.core.string('empty_game_list')
            )
            return

        bar_movement = int(1.0 / len(game_list) * 100)

        storage = self.core.get_storage()
        game_version_storage = self.plugin.get_storage('game_version')

        cache = {}
        if game_version_storage.get('version') == Game.version:
            cache = storage.raw_dict().copy()

        storage.clear()

        i = 1
        for nvapp in game_list:
            progress_dialog.update(bar_movement * i, 'Processing: %s' % nvapp.title)
            game = Game(nvapp.title)

            if nvapp.id in cache:
                if not storage.get(nvapp.id):
                    progress_dialog.update(bar_movement * i, 'Restoring information from cache')
                    storage[nvapp.id] = cache.get(nvapp.id)[0]
            else:
                try:
                    progress_dialog.update(bar_movement * i, 'Getting Information from Local Sources')
                    storage[nvapp.id] = self.scraper_chain.query_game_information(nvapp)
                except KeyError:
                    self.logger.info(
                        'Key Error thrown while getting information for game {0}: {1}'
                        .format(nvapp.title,
                                KeyError.message))
                    storage[nvapp.id] = game
            i += 1

        game_version_storage.clear()
        game_version_storage['version'] = Game.version

        storage.sync()
        game_version_storage.sync()


    def refresh_games(self):

        game_list = self.moonlight_helper.list_games()

        storage = self.core.get_storage()
        game_version_storage = self.plugin.get_storage('game_version')

        cache = {}
        if game_version_storage.get('version') == Game.version:
            cache = storage.raw_dict().copy()

        storage.clear()

        i = 1
        for nvapp in game_list:
            game = Game(nvapp.title)

            if nvapp.id in cache:
                if not storage.get(nvapp.id):
                    storage[nvapp.id] = cache.get(nvapp.id)[0]
            else:
                try:
                    storage[nvapp.id] = self.scraper_chain.query_game_information(nvapp)
                except KeyError:
                    self.logger.info(
                        'Key Error thrown while getting information for game {0}: {1}'
                        .format(nvapp.title,
                                KeyError.message))
                    storage[nvapp.id] = game
            i += 1

        game_version_storage.clear()
        game_version_storage['version'] = Game.version

        storage.sync()
        game_version_storage.sync()


    def get_games_as_list(self):
        """
        Parses contents of local game storage into a list that can be interpreted by Kodi
        :rtype: list
        """

        def context_menu(game_id):

            if self.plugin.get_setting('last_run', str):
                lastrun = self.plugin.get_setting('last_run', str)
                if (lastrun == game.name):
                    return [
                    (
                        'Game Information',
                        'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                            endpoint='show_game_info',
                            game_id=game_id
                        )
                    ),
                    (
                        self.core.string('addon_settings'),
                        'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                            endpoint='open_settings'
                        )
                    ),
                    (
                        self.core.string('full_refresh'),
                        'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                            endpoint='do_full_refresh'
                        )
                    ),
                    (
                        self.core.string('quit_game'),
                        'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                            endpoint='quit_game', refresh=True
                        )
                    )
                ]


                else:
                    return [
                (
                    'Game Information',
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='show_game_info',
                        game_id=game_id
                    )
                ),
                (
                    self.core.string('addon_settings'),
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='open_settings'
                    )
                ),
                (
                    self.core.string('full_refresh'),
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='do_full_refresh'
                    )
                )
            ]


            else:
                return [
                (
                    'Game Information',
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='show_game_info',
                        game_id=game_id
                    )
                ),
                (
                    self.core.string('addon_settings'),
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='open_settings'
                    )
                ),
                (
                    self.core.string('full_refresh'),
                    'XBMC.RunPlugin(%s)' % self.plugin.url_for(
                        endpoint='do_full_refresh'
                    )
                )
            ]

        storage = self.core.get_storage()

        if len(storage.raw_dict()) == 0:
            self.get_games()

        items = []
        for i, game_name in enumerate(storage):
            game = storage.get(game_name)
            label = None
            if self.plugin.get_setting('last_run', str):
                lastrun = self.plugin.get_setting('last_run', str)
                if (lastrun == game.name):
                    label = u'[COLOR green]\u2588[/COLOR]' + u'[COLOR green]\u2588[/COLOR]' + '\n' + game.name
                else:
                    label = game.name
            else:
                label = game.name

            items.append({
                'label': label,
                'icon': game.get_selected_poster(),
                'thumbnail': game.get_selected_poster(),
                'info': {
                    'year': game.year,
                    'plot': game.plot,
                    'genre': game.get_genre_as_string(),
                    'originaltitle': game.name,
                },
                'replace_context_menu': True,
                'context_menu': context_menu(game_name),
                'path': self.plugin.url_for(
                    endpoint='launch_game',
                    game_id=game.name
                ),
                'properties': {
                    'fanart_image': game.get_selected_fanart().get_original()
                }
            })

        return items

    def launch_game(self, game_name):
        """
        Launches game with specified name
        :type game_name: str
        """
        self.moonlight_helper.launch_game(game_name)
