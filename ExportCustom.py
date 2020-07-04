import os, json
import configparser
from LaunchBox2AEL import generate_data, launchbox, write_files, AELDIR
from launchbox.resource import clean_filename
from ael import get_first_path
from ael.launcher import Launcher
from files.file import File, find_files
from win32com.client import Dispatch

# Fix Oculus launcher
playlists = launchbox.playlists
for playlist in playlists:
    if playlist.name != 'VR':
        continue
    for game in playlist.games:
        if game.name == 'Oculus':
            oculus = game
            oculus_launcher = Launcher(oculus.platform, oculus.emulator, AELDIR)
            oculus_launcher.id = 'Oculus'
            oculus_launcher['id'] = 'Oculus'
            oculus_launcher['m_name'] = 'Oculus'
            oculus_launcher['m_plot'] = oculus.notes
            oculus_launcher['rompath'] = None
            oculus_launcher['application'] = oculus.rom.path
            oculus_launcher['roms_base_noext'] = None
            oculus_launcher['s_icon'] = get_first_path(game.search_images('Box - Front'))
            oculus_launcher['s_fanart'] = get_first_path(game.search_images('Fanart'))
            oculus_launcher['s_banner'] = get_first_path(game.search_images('Banner'))
            oculus_launcher['s_clearlogo'] = get_first_path(game.search_images('Clear Logo'))

# Create shortcuts for epic games in playnite that I dont have in LaunchBox yet
config = configparser.RawConfigParser()
config.read(File([os.path.dirname(__file__), 'config.ini']).absolute)
PLAYNITEDIR  = os.path.expandvars(config.get('playnite', 'dir'))

source_files = find_files(os.path.join(PLAYNITEDIR, 'library', 'sources'), '*.json')
sources = [json.load(open(f)) for f in source_files]
epic_source_id = [s['Id'] for s in sources if s['Name'] == 'Epic'][0]

game_files = find_files(os.path.join(PLAYNITEDIR, 'library', 'games'), '*.json')

games = [json.load(open(f, encoding='utf-8')) for f in game_files]
epic_games = [g for g in games if g['SourceId'] == epic_source_id]

for g in epic_games:
    dlcs = ['JayDLC1']
    target_path = 'com.epicgames.launcher://apps/{}?action=launch&silent=true'.format(g['GameId'])
    if target_path in [g.rom.path for g in launchbox.games] or g['GameId'] in dlcs:
        continue
    pathLink = os.path.join(os.path.dirname(__file__), clean_filename(g['Name']) + '.lnk')
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(pathLink)
    shortcut.Targetpath = target_path
    shortcut.save()
    print('{}: {}'.format(g['Name'], target_path))

# Write data to AEL
categories, launchers, collections = generate_data()
launchers.launchers[oculus_launcher.id] = oculus_launcher
write_files(categories, launchers, collections)
