from files.file import File
from collections import OrderedDict

# launcher is the combination of platform and either an emulator id or executables
class Game(OrderedDict):
    def __init__(self, game, dosbox_exe=None, dosbox_args=None):
        super(Game, self).__init__((
            ('altapp', ''),
            ('altarg', ''),
            ('filename', game.path),
            ('m_nplayers', ''),
            ('finished', game.completed),
            ('id', game.id),
            ('m_genre', game.genre),
            ('m_name', game.name),
            ('m_plot', game.notes),
            ('m_rating', ''),
            ('m_esrb', ''),
            ('m_developer', game.developer),
            ('m_year', game.release_year),
            ('nointro_status', 'None'),
            ('s_map', ''),
            ('pclone_status', '')
            ))

        if '://' in self['filename']:
            uri = self['filename']
            self['altapp'] = get_associated_app(uri)
            self['altarg'] = uri
            self['filename'] = '.'
        elif game.dosbox_conf:
            self['altapp'] = dosbox_exe
            self['altarg'] = dosbox_args.format(game.dosbox_conf)
        elif game.emulator.id == 'Executables':
            self['altapp'] = self['filename']
            self['altarg'] = ' '
        self['disks'] = [] #TODO
