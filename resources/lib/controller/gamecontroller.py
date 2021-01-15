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
            dialogText = 'Processing: %s\n' % nvapp.title
            progress_dialog.update(bar_movement * i, dialogText)
            game = Game(nvapp.title)

            if nvapp.id in cache:
                if not storage.get(nvapp.id):
                    progress_dialog.update(bar_movement * i, dialogText + 'Restoring information from cache')
                    storage[nvapp.id] = cache.get(nvapp.id)[0]
            else:
                try:
                    progress_dialog.update(bar_movement * i, dialogText + 'Getting Information from Local Sources')
                    storage[nvapp.id] = self.scraper_chain.query_game_information(nvapp)
                except KeyError as e:
                    self.logger.info(
                        'Key Error thrown while getting information for game {0}: {1}'
                        .format(nvapp.title,
                                str(e)))
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
                except KeyError as e:
                    self.logger.info(
                        'Key Error thrown while getting information for game {0}: {1}'
                        .format(nvapp.title,
                                str(e)))
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
            default_context_menu = [
                (
                    self.core.string('addon_settings'),
                    'RunPlugin(%s)' % self.plugin.url_for(endpoint='open_settings')
                ),
                (
                    self.core.string('full_refresh'),
                    'RunPlugin(%s)' % self.plugin.url_for(endpoint='do_full_refresh')
                )
                ]

            lastrun = self.plugin.get_setting('last_run', str)
            if lastrun:
                if (lastrun == game.name):
                    return default_context_menu + [(
                        self.core.string('quit_game'),
                        'RunPlugin(%s)' % self.plugin.url_for(endpoint='quit_game', refresh=True)
                    )]
            return default_context_menu

        storage = self.core.get_storage()

        if len(storage.raw_dict()) == 0:
            self.get_games()

        items = []
        lastrun = self.plugin.get_setting('last_run', str)
        for i, game_name in enumerate(storage):
            game = storage.get(game_name)
            label = game.name if type(game.name) == str else str(game.name, 'utf-8')
            if lastrun and lastrun == label:
                label = '[B][COLOR green]' + label + '[/COLOR][/B]'
                lastrun = False
            
            game.year = int(game.year) if game.year is not None and game.year.isnumeric() else ''
            items.append({
                'label': label,
                'icon': game.get_selected_poster(),
                'thumbnail': game.get_selected_poster(),
                'info': {
                    'title': game.name,
                    'genre': game.genre,
                    'plot': game.plot,
                    'mediatype': 'movie',
                    'year': game.year
                },
                'fanart': game.get_selected_fanart().get_original(),
                'replace_context_menu': True,
                'context_menu': context_menu(game_name),
                'path': self.plugin.url_for(
                    endpoint='launch_game',
                    game_id=game.name
                )
            })

        return items

    def launch_game(self, game_name):
        """
        Launches game with specified name
        :type game_name: str
        """
        self.moonlight_helper.launch_game(game_name)
