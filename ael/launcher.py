from hashlib import md5
from files.file import File
from collections import OrderedDict
import os
from .utils import clean_filename
import time

# launcher is the combination of platform and either an emulator id or executables
class Launcher(OrderedDict):
    def __init__(self, lb_platform, emulator):
        self.name = '{} ({})'.format(lb_platform.name, emulator.name)
        self.id = md5(self.name.encode()).hexdigest()
        self.platform = lb_platform
        self.emulator = emulator
        self.games = []
        super(Launcher, self).__init__((
                ('id', self.id),
                ('m_name', lb_platform.name),
                ('categoryID', lb_platform.category.id),
                ('platform', lb_platform.name),
                ('rompath', ""),
                ('romext', ""),
                ('m_year', lb_platform.release_year),
                ('m_genre', ""),
                ('m_studio', lb_platform.developer),
                ('m_plot', lb_platform.notes),
                ('m_rating', ""),
                ('application', emulator.path),
                ('args', emulator.args.format('$rom$')),
                ('finished', "False"),
                ('minimize', "False"),
                ('roms_base_noext', clean_filename("LB2AEL_{}_roms".format(self.name.replace(' ', '_')))),
                ('nointro_xml_file', ""),
                ('nointro_display_mode', "All ROMs"),
                ('pclone_launcher', "False"),
                ('num_roms', "0"),
                ('num_parents', "0"),
                ('num_clones', "0"),
                ('timestamp_launcher', str(time.time())),
                ('timestamp_report', "0.0"),
                ('default_thumb', "s_icon"),
                ('default_fanart', "s_fanart"),
                ('default_banner', "s_banner"),
                ('default_poster', "s_poster"),
                ('roms_default_icon', "s_boxfront"),
                ('roms_default_fanart', "s_fanart"),
                ('roms_default_banner', "s_banner"),
                ('roms_default_poster', "s_poster"),
                ('roms_default_clearlogo', "s_clearlogo"),
                ('s_icon', (lb_platform.search_images('Banner') + [None])[0]),
                ('s_fanart', (lb_platform.search_images('Fanart') + [None])[0]),
                ('s_banner', (lb_platform.search_images('Banner') + [None])[0]),
                ('s_poster', ""),
                ('s_clearlogo', (lb_platform.search_images('Clear Logo') + [None])[0]),
                ('s_trailer', ""), #TODO this and lower down
                ('path_banner', "E:\\Juegos\\Emulation\\AEL\\{}\\banner".format(lb_platform.name)),
                ('path_clearlogo', "E:\\Juegos\\Emulation\\AEL\\{}\\clearlogo".format(lb_platform.name)),
                ('path_fanart', "E:\\Juegos\\Emulation\\AEL\\{}\\fanart".format(lb_platform.name)),
                ('path_title', "E:\\Juegos\\Emulation\\AEL\\{}\\titles".format(lb_platform.name)),
                ('path_snap', "E:\\Juegos\\Emulation\\AEL\\{}\\snap".format(lb_platform.name)),
                ('path_boxfront', "E:\\Juegos\\Emulation\\AEL\\{}\\boxfront".format(lb_platform.name)),
                ('path_boxback', "E:\\Juegos\\Emulation\\AEL\\{}\\boxback".format(lb_platform.name)),
                ('path_cartridge', "E:\\Juegos\\Emulation\\AEL\\{}\\cartridges".format(lb_platform.name)),
                ('path_flyer', "E:\\Juegos\\Emulation\\AEL\\{}\\flyers".format(lb_platform.name)),
                ('path_map', "E:\\Juegos\\Emulation\\AEL\\{}\\maps".format(lb_platform.name)),
                ('path_manual', "E:\\Juegos\\Emulation\\AEL\\{}\\manuals".format(lb_platform.name)),
                ('path_trailer', "E:\\Juegos\\Emulation\\AEL\\{}\\trailers".format(lb_platform.name))
            ))

    def add_game(self, game):
        self.games.append(game)
        self['m_name'] = self.name if len(self.games) > 1 else self.platform.name
        self['num_roms'] = str(len(self.games))
        self['rompath'] = os.path.commonprefix(list(self.paths))
        self['romext'] = ','.join(self.extensions)

    @property
    def paths(self):
        paths = set()
        for game in self.games:
            if '://' not in game.path:
                f = File(game.path)
                paths.add(f.absolute_dir)
        return paths

    @property
    def extensions(self):
        extensions = set()
        for game in self.games:
            if '://' not in game.path:
                f = File(game.path)
                extensions.add(f.extension)
        return extensions


class LaunchersCatalog:
    def __init__(self, games):
        self.launchers = {}
        for game in games:
            launcher = Launcher(game.platform, game.emulator)
            try:
                self.launchers[launcher.id].add_game(game)
            except KeyError:
                launcher.add_game(game)
                self.launchers[launcher.id] = launcher

    def __iter__(self):
        return iter(self.launchers.values())

    def __getitem__(self, key):
        return self.launchers[key]

    def search(self, platform_name):
        for launcher in self.launchers.values():
            if launcher.platform.name == platform_name:
                yield launcher
