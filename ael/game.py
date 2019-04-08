from files.file import File
from collections import OrderedDict
from . import GAME_RESOURCE_TYPES

# launcher is the combination of platform and either an emulator id or executables
class Game(OrderedDict):
    def __init__(self, lb_game, dosbox_exe=None, dosbox_args=None):
        super(Game, self).__init__((
            ('altapp', ''),
            ('altarg', ''),
            ('filename', lb_game.path),
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
                self[field] = (lb_game.search_images(folder) + [None])[0]

        self['s_manual'] = (lb_game.search_manuals() + [None])[0]
        self['s_trailer'] = (lb_game.search_trailers() + [None])[0]

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
        self['disks'] = [] #TODO
