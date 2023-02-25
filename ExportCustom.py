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
dlcs = ['JayDLC1']
for playlist in playlists:
    if playlist.name == 'DLC':
        dlcs += [g.id for g in playlist.games]
    elif playlist.name == 'VR':
        try:
            oculus = [g for g in playlist.games if g.name == 'Oculus'][0]
        except IndexError:
            pass
        else:
            oculus_launcher = Launcher(oculus.platform, oculus.emulator, AELDIR)
            oculus_launcher.id = 'Oculus'
            oculus_launcher['id'] = 'Oculus'
            oculus_launcher['m_name'] = 'Oculus'
            oculus_launcher['m_plot'] = oculus.notes
            oculus_launcher['rompath'] = None
            oculus_launcher['application'] = oculus.rom.path
            oculus_launcher['roms_base_noext'] = None
            oculus_launcher['s_icon'] = get_first_path(oculus.search_images('Box - Front'))
            oculus_launcher['s_fanart'] = get_first_path(oculus.search_images('Fanart'))
            oculus_launcher['s_banner'] = get_first_path(oculus.search_images('Banner'))
            oculus_launcher['s_clearlogo'] = get_first_path(oculus.search_images('Clear Logo'))

categories, launchers, collections = generate_data()
# Add Oculus Launcher
launchers.launchers[oculus_launcher.id] = oculus_launcher
# Remove DLCs from the catalog
for launcher in launchers:
    launcher.games = [g for g in launcher.games if g['id'] not in dlcs]

    # this will make everything run without launchers like origin blocking
    if launcher.platform.name == 'Windows':
        launcher['romext'] = 'exe'

write_files(categories, launchers, collections)
