from collections import OrderedDict
from . import GAME_RESOURCE_TYPES, get_first_path
import winreg
import shlex


def get_associated_app(uri):
    prefix, game = uri.split('://')
    key = r'{}\Shell\Open\Command'.format(prefix)
    try:
        command = winreg.QueryValue(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key), None)
        app, params = shlex.split(command)
    except OSError:
        app = None
    return app


# launcher is the combination of platform and either an emulator id or executables
class Game(OrderedDict):
    def __init__(self, lb_game, dosbox_exe=None, dosbox_args=None):
        super(Game, self).__init__((
            ('altapp', ''),
            ('altarg', ''),
            ('filename', lb_game.rom.absolute),
            ('m_nplayers', ''),
            ('finished', lb_game.completed),
            ('id', lb_game.id),
            ('m_genre', lb_game.genre),
            ('m_name', lb_game.name),
            ('m_plot', lb_game.notes),
            ('m_rating', ''),
            ('m_esrb', ''),
            ('m_developer', lb_game.developer),
            ('m_year', lb_game.release_year),
            ('nointro_status', 'None'),
            ('s_map', ''),
            ('pclone_status', '')
            ))

        for field, resource_types in GAME_RESOURCE_TYPES.items():
            for folder in resource_types:
                self[field] = get_first_path(lb_game.search_images(folder))

        self['s_manual'] = get_first_path(lb_game.search_manuals())
        self['s_trailer'] = get_first_path(lb_game.search_trailers())

        if '://' in self['filename']:
            uri = self['filename']
            self['altapp'] = get_associated_app(uri)
            self['altarg'] = uri
            self['filename'] = '.'
        elif lb_game.dosbox_conf:
            self['altapp'] = dosbox_exe
            self['altarg'] = dosbox_args.format(lb_game.dosbox_conf)
        elif lb_game.emulator.id == 'Executables':
            self['altapp'] = self['filename']
            self['altarg'] = ' '
        self['disks'] = [f.absolute for f in lb_game.disks]
