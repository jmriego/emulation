from collections import OrderedDict
from . import GAME_RESOURCE_TYPES, get_first_path
import winreg
import shlex


def get_associated_app(uri):
    prefix, game = uri.split('://')
    key = r'{}\Shell\Open\Command'.format(prefix)
    try:
        command = winreg.QueryValue(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key), None)
        app, *params = shlex.split(command)
        params = ' '.join(params)
    except OSError:
        app = None
        params = None
    return app, params


# launcher is the combination of platform and either an emulator id or executables
class Game(OrderedDict):
    def __init__(self, lb_game, dosbox_exe=None, dosbox_args=None):
        super(Game, self).__init__((
            ('altapp', ''),
            ('altarg', ''),
            ('filename', lb_game.rom.absolute),
            ('m_nplayers',lb_game.play_mode),
            ('finished', lb_game.completed),
            ('id', lb_game.id),
            ('m_genre', lb_game.genre),
            ('m_name', lb_game.name),
            ('m_plot', lb_game.notes),
            # launchbox rating is 0-5 and Kodi expects 0-10
            ('m_rating', str(round(float(lb_game.community_star_rating)*2.0)) if int(lb_game.community_star_rating_votes) else ""),
            ('m_esrb', ''),
            ('m_developer', lb_game.developer),
            ('m_year', lb_game.release_year),
            ('nointro_status', 'None'),
            ('s_map', ''),
            ('pclone_status', '')
            ))
        self.rom = lb_game.rom

        for field, resource_types in GAME_RESOURCE_TYPES.items():
            found_imgs = []
            for folder in resource_types:
                found_imgs += lb_game.search_images(folder)
            self[field] = get_first_path(found_imgs)


        self['s_manual'] = get_first_path(lb_game.search_manuals())
        self['s_trailer'] = get_first_path(lb_game.search_trailers())

        if '://' in self.rom.path:
            uri = self.rom.path
            app, params = get_associated_app(uri)
            if app and params:
                self['altapp'] = app
                self['altarg'] = uri
                self['romext'] = 'lnk'
                self['filename'] = '.'
        elif lb_game.dosbox_conf:
            self['altapp'] = dosbox_exe
            self['altarg'] = dosbox_args.format(lb_game.dosbox_conf)
        elif lb_game.emulator.id == 'Executables':
            self['altapp'] = self['filename']
            self['altarg'] = ' '
        self['disks'] = [f.absolute for f in lb_game.disks]
