import os
import stat

from xml.etree.ElementTree import ElementTree

from xbmcswift2 import xbmcaddon

internal_path = xbmcaddon.Addon().getAddonInfo('path')

STRINGS = {
    'name':                30000,
    'addon_settings':      30100,
    'full_refresh':        30101,
    'quit_game':           30102,
    'choose_ctrl_type':    30200,
    'enter_filename':      30201,
    'starting_mapping':    30202,
    'mapping_success':     30203,
    'set_mapping_active':  30204,
    'mapping_failure':     30205,
    'pair_failure_paired': 30206,
    'configure_first':     30207,
    'reset_cache_warning': 30208,
    'empty_game_list':     30209,
    'scraper_failed':      30212,
}


class Core:
    def __init__(self, plugin, logger):
        self.plugin = plugin
        self.logger = logger
        self.logger.info('[CoreService] - initialized')

    def string(self, string_id):
        if string_id in STRINGS:
            return self.plugin.get_string(STRINGS[string_id]).encode('utf-8')
        else:
            return string_id

    def get_storage(self):
        return self.plugin.get_storage('game_storage')

