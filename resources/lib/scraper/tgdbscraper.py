import os
import subprocess
from urllib.request import urlopen
from bs4 import BeautifulSoup

from xbmcswift2 import xbmcgui

from .abcscraper import AbstractScraper
from resources.lib.model.apiresponse import ApiResponse
from resources.lib.model.fanart import Fanart


class TgdbScraper(AbstractScraper):
    def __init__(self, plugin, core):
        AbstractScraper.__init__(self, plugin, core)
        self.base_api_url = 'https://thegamesdb.net/'
        self.search_api_url = self.base_api_url + "search.php?platform_id[]=1&name=" 
        self.cover_cache = self._set_up_path(os.path.join(self.base_path, 'art/poster/'))
        self.fanart_cache = self._set_up_path(os.path.join(self.base_path, 'art/fanart/'))
        self.api_cache = os.path.join(self.base_path, 'api_cache/')

    def name(self):
        return 'TGDB'

    def get_game_information(self, nvapp):
        request_name = nvapp.title.replace(" ", "+").replace(":", "")
        response = self._gather_information(nvapp, request_name)
        response.name = nvapp.title
        return response

    def return_paths(self):
        return [self.cover_cache, self.fanart_cache, self.api_cache]

    def is_enabled(self):
        return self.plugin.get_setting('enable_tgdb', bool)

    def _gather_information(self, nvapp, game):
        game_cover_path = self._set_up_path(os.path.join(self.cover_cache, nvapp.id))
        game_fanart_path = self._set_up_path(os.path.join(self.fanart_cache, nvapp.id))
        
        search_html = urlopen(self.search_api_url + game).read()
        search_soup = BeautifulSoup(search_html)
        game_link = search_soup.find(id="display").find("a")
        game_url = ""
        if game_link is None:
            xbmcgui.Dialog().notification(
                self.core.string('name'),
                self.core.string('scraper_failed') % (game, self.name())
            )
            return ApiResponse()
        else:
            game_url = game_link.get('href')
            game_html = urlopen(self.base_api_url + game_url).read()
            game_soup = BeautifulSoup(game_html)

            dict_response = self._parse_xml_to_dict(game_soup)
            posters = dict_response['posters']
            dict_response['posters'] = []
            for poster in posters:
                dict_response['posters'].append(self._dump_image(game_cover_path, poster))

            local_arts = {}
            for art in dict_response.get('fanarts'):
                art.set_thumb(self._dump_image(game_fanart_path, art.get_original()))
                local_arts[os.path.basename(art.get_original())] = art
            dict_response['fanarts'] = local_arts
            return ApiResponse.from_dict(**dict_response)

    @staticmethod
    def _parse_xml_to_dict(game_soup):
        """

        :rtype: dict
        :type root: Element
        """
        data = {'year': 'N/A', 'plot': 'N/A', 'posters': [], 'genre': [], 'fanarts': []}
        overview = game_soup.find("p", class_="game-overview")
        if overview is not None:
            data['plot'] = overview.text
        siblings = overview.find_next_siblings('p')
        for sibling in siblings:
            if 'Genre' in sibling.text:
                data['genre'] = sibling.text.replace('Genre(s): ', '').split(' | ')
        front_cover = game_soup.find("img", alt='front cover')
        if front_cover is not None:
            data['posters'] = [front_cover.get('src')]
        fanart = game_soup.find("a", attrs={"data-caption": "Fanart"})
        if fanart is not None:
            model = Fanart()
            model.set_original(fanart.get('href'))
            data['fanarts'].append(model)

        return data
