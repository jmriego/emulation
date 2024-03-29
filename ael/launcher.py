from hashlib import md5
from collections import OrderedDict
import logging
import os
from launchbox.resource import clean_filename
from . import get_first_path
import time
from ael.game import Game

logger = logging.getLogger(__name__)


# launcher is the combination of platform and either an emulator id or executables
class Launcher(OrderedDict):
    def __init__(self, lb_platform, emulator, aeldir):
        self.name = '{} ({})'.format(lb_platform.name, emulator.name)
        self.id = md5(self.name.encode()).hexdigest()
        self.platform = lb_platform
        self.emulator = emulator
        self.games = []
        assets_dir = "{}\\asset-launchers\\{}".format(aeldir, lb_platform.name)
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
                ('application', emulator.path.absolute),
                ('args', emulator.command_line(lb_platform.name).format('$rom$')),
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
                ('s_icon', get_first_path(lb_platform.search_images('Banner'))),
                ('s_fanart', get_first_path(lb_platform.search_images('Fanart'))),
                ('s_banner', get_first_path(lb_platform.search_images('Banner'))),
                ('s_poster', ""),
                ('s_clearlogo', get_first_path(lb_platform.search_images('Clear Logo'))),
                ('s_trailer', "{}\\trailers".format(assets_dir)),
                ('path_3dbox', "{}\\3dbox".format(assets_dir)),
                ('path_banner', "{}\\banner".format(assets_dir)),
                ('path_clearlogo', "{}\\clearlogo".format(assets_dir)),
                ('path_fanart', "{}\\fanart".format(assets_dir)),
                ('path_title', "{}\\titles".format(assets_dir)),
                ('path_snap', "{}\\snap".format(assets_dir)),
                ('path_boxfront', "{}\\boxfront".format(assets_dir)),
                ('path_boxback', "{}\\boxback".format(assets_dir)),
                ('path_cartridge', "{}\\cartridges".format(assets_dir)),
                ('path_flyer', "{}\\flyers".format(assets_dir)),
                ('path_map', "{}\\maps".format(assets_dir)),
                ('path_manual', "{}\\manuals".format(assets_dir)),
                ('path_trailer', "{}\\trailers".format(assets_dir))
            ))
        logger.debug('Successfully initialized AEL launcher %s', self.name)

    def add_game(self, game, dosbox_exe=None, dosbox_args=None):
        ael_game = Game(game, dosbox_exe, dosbox_args)
        ael_game.launcher = self
        self.games.append(ael_game)
        self['num_roms'] = str(len(self.games))
        try:
            self['rompath'] = os.path.commonprefix(list(self.paths)) or list(self.paths)[0]
        except IndexError:
            # if rompath is empty, AEL will try to just open the application
            # we add the path to the app itself instead of its games
            # (e.g. path to Steam) which won't be used anyway
            self['rompath'] = ael_game['altapp']

        self['romext'] = '|'.join(sorted(list(self.extensions)))

    @property
    def paths(self):
        paths = set()
        for game in self.games:
            if '://' in game.rom.path:
                return ['.']
            try:
                paths.add(game.rom.absolute_dir)
            except:
                pass
        return paths

    @property
    def extensions(self):
        extensions = set()
        for game in self.games:
            if '://' not in game.rom.path and game.rom.extension:
                extensions.add(game.rom.extension)
            else:
                extensions.add("lnk")
        return extensions


class LaunchersCatalog:
    def __init__(self, games, dosbox_exe=None, dosbox_args=None, aeldir=None):
        self.launchers = {}
        logger.info('Generating list of AEL launchers from the games that use them')
        for game in games:
            launcher = Launcher(game.platform, game.emulator, aeldir)
            try:
                self.launchers[launcher.id].add_game(game, dosbox_exe, dosbox_args)
            except KeyError:
                launcher.add_game(game, dosbox_exe, dosbox_args)
                self.launchers[launcher.id] = launcher

        logger.info('Generating count of games for each AEL launcher')
        platform_launcher_count = {}
        for launcher in self.launchers.values():
            platform_launcher_count.setdefault(launcher.platform.name, list()).append(launcher)

        for platform, launchers in platform_launcher_count.items():
            if len(launchers) > 1:
                for launcher in launchers:
                    logger.debug('Launcher %s renamed to %s to avoid duplication', launcher['m_name'], launcher.name)
                    launcher['m_name'] = launcher.name

    def __iter__(self):
        return iter(self.launchers.values())

    def __getitem__(self, key):
        return self.launchers[key]

    def search(self, platform_name):
        for launcher in self.launchers.values():
            if launcher.platform.name == platform_name:
                yield launcher
