import configparser
import os
import xbmcaddon


class ConfigHelper:
    conf = 'moonlight.conf'

    def __init__(self, plugin, logger):
        self.plugin = plugin
        self.internal_path = xbmcaddon.Addon().getAddonInfo('path')
        self.logger = logger
        self._reset()
        self.configure(False)

    def _reset(self):
        self.file_path = None
        self.binary_path = None
        self.host_ip = None
        self.enable_custom_resolution = None
        self.resolution_width = None
        self.resolution_height = None
        self.resolution = None
        self.framerate = None
        self.host_optimizations = None
        self.remote_optimizations = None
        self.local_audio = None
        self.enable_custom_bitrate = None
        self.bitrate = None
        self.packetsize = None
        self.enable_custom_input = None
        self.full_path = None
        self.audio_device = None
        self.enable_moonlight_debug = None
        self.codec = None
        self.enable_surround_audio = None
        self.unsupported_flag = None

    def _configure(self, addon_path, binary_path=None, host_ip=None, enable_custom_resolution=False, resolution_width=None,
                   resolution_height=None, resolution=None,
                   framerate=None, graphics_optimizations=False, remote_optimizations=False, local_audio=False,
                   enable_custom_bitrate=False, bitrate=None, packetsize=None,
                   enable_custom_input=False, override_default_resolution=False, audio_device=None, enable_moonlight_debug=False, codec=None,
                   enable_surround_audio=False, unsupported_flag=None):

        self.addon_path = addon_path
        self.binary_path = binary_path
        self.host_ip = host_ip
        self.enable_custom_resolution = enable_custom_resolution
        self.resolution_width = resolution_width,
        self.resolution_height = resolution_height,
        self.resolution = resolution
        self.framerate = framerate
        self.graphics_optimizations = graphics_optimizations
        self.remote_optimizations = remote_optimizations
        self.local_audio = local_audio
        self.enable_custom_bitrate = enable_custom_bitrate
        self.bitrate = bitrate
        self.packetsize = packetsize
        self.enable_custom_input = enable_custom_input
        self.override_default_resolution = override_default_resolution
        self.audio_device = audio_device
        self.enable_moonlight_debug = enable_moonlight_debug
        self.codec = codec
        self.enable_surround_audio = enable_surround_audio
        self.unsupported_flag = unsupported_flag


    def configure(self, dump=True):
        binary_path = self._find_binary(self.internal_path)

        if binary_path is None:
            print('Moonlight binary could not be found. Configuration file saved at %s' % self.plugin.storage_path)
            self.full_path = self.plugin.storage_path + self.conf
        else:
            self.full_path = binary_path + self.conf

        settings = {
            'addon_path':                   self.plugin.storage_path,
            'binary_path':                  binary_path,
            'host_ip':                      self.plugin.get_setting('host', str),
            'enable_custom_resolution':     self.plugin.get_setting('enable_custom_resolution', bool),
            'resolution_width':             self.plugin.get_setting('resolution_width', str),
            'resolution_height':            self.plugin.get_setting('resolution_height', str),
            'resolution':                   self.plugin.get_setting('resolution', str),
            'framerate':                    self.plugin.get_setting('framerate', str),
            'graphics_optimizations':       self.plugin.get_setting('graphic_optimizations', str),
            'remote_optimizations':         self.plugin.get_setting('remote_optimizations', str),
            'local_audio':                  self.plugin.get_setting('local_audio', str),
            'enable_custom_bitrate':        self.plugin.get_setting('enable_custom_bitrate', bool),
            'bitrate':                      self.plugin.get_setting('bitrate', int),
            'packetsize':                   self.plugin.get_setting('packetsize', int),
            'enable_custom_input':          self.plugin.get_setting('enable_custom_input', bool),
            'override_default_resolution':  self.plugin.get_setting('override_default_resolution', bool),
            'audio_device':                 self.plugin.get_setting('audio_device', str),
            'enable_moonlight_debug':       self.plugin.get_setting('enable_moonlight_debug', str),
            'codec':                        self.plugin.get_setting('codec', str),
            'enable_surround_audio':        self.plugin.get_setting('enable_surround_audio', str),
            'unsupported_flag':             self.plugin.get_setting('unsupported_flag', str)
        }
        self._configure(**settings)

        if dump:
            self._dump_conf()

    def _dump_conf(self):
        """
        This dumps the currently configured helper into a file moonlight can read
        """
        config = configparser.ConfigParser()
        config.read(self.full_path)

        if 'Moonlight' not in config.sections():
            config.add_section('Moonlight')

        config.set('Moonlight', 'binpath', "" if self.binary_path is None else self.binary_path)
        config.set('Moonlight', 'address', self.host_ip)

        if not self.override_default_resolution:
            config.set('Moonlight', 'width', '1280')
            config.set('Moonlight', 'height', '720')
        
        if self.plugin.get_setting('enable_custom_resolution', str) == 'false':
            if self.override_default_resolution:
                if self.resolution == '3840x2160':
                    config.set('Moonlight', 'width', '3840')
                    config.set('Moonlight', 'height', '2160')
                if self.resolution == '2560x1440':
                    config.set('Moonlight', 'width', '2560')
                    config.set('Moonlight', 'height', '1440')
                if self.resolution == '1920x1080':
                    config.set('Moonlight', 'width', '1920')
                    config.set('Moonlight', 'height', '1080')
                if self.resolution == '1280x720':
                    config.set('Moonlight', 'width', '1280')
                    config.set('Moonlight', 'height', '720')
        else:
            config.set('Moonlight', 'width', str(self.resolution_width[0]))
            config.set('Moonlight', 'height', str(self.resolution_height[0]))

        if not self.framerate:
            config.set('Moonlight', 'fps', '30')
        else:
            config.set('Moonlight', 'fps', str(self.framerate))

        if self.enable_custom_bitrate:
            config.set('Moonlight', 'bitrate', str(int(self.bitrate) * 1000))
        else:
            config.set('Moonlight', 'bitrate', '-1')

        if self.packetsize != 1024:
            config.set('Moonlight', 'packetsize', str(self.packetsize))
        else:
            config.set('Moonlight', 'packetsize', '1024')

        config.set('Moonlight', 'sops', self.graphics_optimizations)
        config.set('Moonlight', 'remote', self.remote_optimizations)
        config.set('Moonlight', 'localaudio', self.local_audio)
        config.set('Moonlight', 'debug', self.enable_moonlight_debug)
        
        if self.plugin.get_setting('local_audio', str) == 'false':
            if self.plugin.get_setting('custom_audio_device', str) == 'true':
                if self.plugin.get_setting('audio_device_parameter', str):
                    config.set('Moonlight', 'audio', self.plugin.get_setting('audio_device_parameter', str))
                else:
                    config.set('Moonlight', 'audio', self.audio_device)
            else:
                config.set('Moonlight', 'audio', self.audio_device)
        else:
            config.remove_option('Moonlight', 'audio')

        config.set('Moonlight', 'codec', self.codec)
        config.set('Moonlight', 'surround', self.enable_surround_audio)
        config.set('Moonlight', 'unsupported', self.unsupported_flag)

        if config.has_option('Moonlight', 'mapping'):
            config.remove_option('Moonlight', 'mapping')

        if config.has_option('Moonlight', 'input'):
            config.remove_option('Moonlight', 'input')

        for section in config.sections():
            if section[:-2] == 'Input':
                config.remove_section(section)
                print('Removed section %s' % section)

        if self.enable_custom_input:
            input_storage = self.plugin.get_storage('input_storage')
            print(input_storage.raw_dict())
            unmapped_devices = []
            mapped_devices = []

            for key, device in list(input_storage.items()):
                if not device.mapping:
                    unmapped_devices.append(device)
                else:
                    mapped_devices.append(device)

            i = 0
            for device in unmapped_devices:
                config.add_section('Input ' + str(i))
                config.set('Input ' + str(i), 'input', device.get_evdev())
                i += 1
            for device in mapped_devices:
                config.add_section('Input ' + str(i))
                config.set('Input ' + str(i), 'mapping', device.mapping)
                config.set('Input ' + str(i), 'input', device.get_evdev())
                i += 1

        with open(self.full_path, 'w') as configfile:
            config.write(configfile)
        configfile.close()

        self.logger.info('[ConfigHelper] - Dumped config to disk.')

    def get_binary(self):
        cp = configparser.ConfigParser()

        try:
            cp.read(self.full_path)

            self.logger.info(
                    '[ConfigHelper] - Successfully loaded config file > trying to access binary path now')

            return self._config_map('Moonlight', cp)['binpath']

        except:
            self.logger.info(
                    '[ConfigHelper] - Exception occurred while attempting to read config from disk >' +
                    ' looking for binary file and dumping config file again.')

            binary_path = self._find_binary()
            self.configure(False)

            return binary_path

    def get_host(self):
        cp = configparser.ConfigParser()
        cp.read(self.full_path)
        return self._config_map('Moonlight', cp)['address']

    def check_for_config_file(self):
        return os.path.isfile(self.full_path)

    def get_section_setting(self, section, setting):
        cp = configparser.ConfigParser()
        cp.read(self.full_path)
        return self._config_map(section, cp)[setting]

    def get_config_path(self):
        return self.full_path

    @staticmethod
    def _find_binary(internal_path):
        binary_locations = [
            '/usr/bin/moonlight',
            '/usr/local/bin/moonlight',
            '/storage/moonlight/moonlight',
            os.path.join(internal_path, 'resources', 'bin', 'moonlight')
        ]

        for f in binary_locations:
            if os.path.isfile(f):
                return os.path.dirname(f) + '/'

        return None

    @staticmethod
    def _config_map(section, parser):
        """

        :param section: string
        :type parser: configparser.ConfigParser
        """
        dict1 = {}
        options = parser.options(section)
        for option in options:
            try:
                dict1[option] = parser.get(section, option)
            except:
                dict1[option] = None
        return dict1
