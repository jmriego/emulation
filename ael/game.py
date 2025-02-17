import logging
import os
import shlex
import subprocess
import winreg
from collections import OrderedDict
from . import GAME_RESOURCE_TYPES, get_first_path

logger = logging.getLogger(__name__)


def get_associated_app(uri):
    prefix, game = uri.split('://')
    key = r'{}\Shell\Open\Command'.format(prefix)

    if prefix == "xbox":
        explorer_exe = os.path.expandvars("%SystemRoot%\\System32\\cmd.exe")
        game_param = '/c "start shell:appsFolder\\{}!Game"'.format(game)
        return explorer_exe, game_param

    try:
        command = winreg.QueryValue(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key), None)
        app, *params = shlex.split(command)
        params = ' '.join(p.replace("%1", uri) for p in params)
    except OSError:
        app = None
        params = None

    logger.debug('Associated app for %s is %s, params %s', uri, app, params)
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
        self['non_blocking'] = True
        self['toggle_window'] = False

        if '://' in self.rom.path:
            uri = self.rom.path
            app, params = get_associated_app(uri)
            if app and params:
                self['altapp'] = app
                self['altarg'] = params
                self['romext'] = 'exe'
                self['filename'] = '.'
                self['non_blocking'] = False
                self['windows_close_fds'] = True
        elif lb_game.dosbox_conf:
            self['altapp'] = dosbox_exe
            self['altarg'] = dosbox_args.format(lb_game.dosbox_conf)
        elif lb_game.emulator.id == 'Executables':
            # TODO: check if there should be more than one additional application
            for app_id, app in lb_game.additional_applications.items():
                if app['path'] and not app['autorun_before'] and not app['autorun_after']:
                    self['altapp'] = app['path']
                    self['altarg'] = app['command_line']
                    self['filename'] = '.'
            else:
                self['altapp'] = self['filename']
                self['altarg'] = lb_game.command_line
                self['filename'] = '.'
        self['disks'] = [f.absolute for f in lb_game.disks]
        logger.debug('Initialized AEL game %s', self['m_name'])

        if lb_game.additional_applications:
            logger.debug('Adding additional applications to AEL game %s', self['m_name'])
            before = []
            after = []
            for app_id, app in lb_game.additional_applications.items():
                if app['path']:
                    if app['autorun_before']:
                        before.append(f'Start {app["path"]} {app["command_line"]}')
                    elif app['autorun_after']:
                        after.append(f'Start {app["path"]} {app["command_line"]}')
            if before or after:
                if self['altapp']:
                    game_command = 'Start "{}" "{}"'.format(self['altapp'], self['altarg'])
                else:
                    game_command = 'Start "{}" "{}"'.format(lb_game.emulator.command_line, self['filename'])
                self['altapp'] = subprocess.run(['where', 'powershell.exe'], capture_output=True, text=True).stdout.strip('\n')
                self['altarg'] = "'" + ';'.join(before + [game_command] + after) + "'"
            logger.debug('AEL game %s is launched as %s %s', self['m_name'], self['altapp'], self['altarg'])
