import os
import ntpath as path
from files.file import File, find_files
from launchbox.catalog import LaunchBox
from ael.utils import clean_filename
from ael.launcher import LaunchersCatalog as AELLaunchersCatalog
from ael.game import Game as AELGame
from ael.category import Category as AELCategory
import untangle
from lxml import etree as ET
import re
from collections import OrderedDict
import json
import time
import winreg
import shlex
import configparser

config = configparser.RawConfigParser()
config.read(File([os.path.dirname(__file__), 'config.ini']).absolute)

LBDIR = config.get('launchbox', 'dir')
AELDIR = os.path.expandvars(config.get('ael', 'dir'))
DOSBOX_EXE = config.get('dosbox', 'exe')
DOSBOX_ARGS = config.get('dosbox', 'args')

os.chdir(LBDIR)
launchbox = LaunchBox(LBDIR)

## Prefered directories for each image type
FOLDER_RESOURCE_TYPES = {
  's_banner': ['Banner', 'Steam Banner', 'Arcade - Marquee'],
  's_flyer': ['Advertisement Flyer - Front'],
  's_boxback': ['Box - Back'],
  's_boxfront': ['Box - Front'],
  's_cartridge': ['Cart - Front', 'Cart - 3D', 'Cart - Back'],
  's_clearlogo': ['Clear Logo'],
  's_fanart': ['Fanart - Background'],
  's_poster': ['Advertisement Flyer - Front', 'Advertisement Flyer - Back'],
  's_snap': ['Screenshot - Gameplay'],
  's_title': ['Screenshot - Game Title'],
  's_manual': ['Manual'],
  's_trailer': ['Video']
}


## Functions used
def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default


def generate_platform_folders(platforms_xml):
    platform_folders = OrderedDict({})
    xml = untangle.parse(platforms_xml)
    for folder_xml in xml.LaunchBox.PlatformFolder:
        platform_name = get_attribute_cdata(folder_xml, 'Platform')
        media_type = get_attribute_cdata(folder_xml, 'MediaType')
        media_path = get_attribute_cdata(folder_xml, 'FolderPath')
        if not platform_name in platform_folders:
            platform_folders[platform_name] = {}
        platform_folders[platform_name][media_type] = File([LBDIR, media_path]).absolute
    return platform_folders


def get_associated_app(uri):
    prefix, game = uri.split('://')
    key = '{}\Shell\Open\Command'.format(prefix)
    try:
        command = winreg.QueryValue(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key), None)
        app, params = shlex.split(command)
    except FileNotFoundError:
        app = None
    return app


def generate_games(launcher):
    # loop in the games xml
    result = {}
    for game in launcher.games:
        result[game.id] = dict(AELGame(game, DOSBOX_EXE, DOSBOX_ARGS))
    return result


def get_resource_order(f):
    file_suffix = re.compile('-?[0-9]*$')
    try:
        order = abs(int(File(f).suffix))
    except TypeError:
        order = 9999
    return order


# generate a list of resources per game
def generate_game_resources(folders):
    file_suffix = re.compile('-[0-9]*$')
    resources = {}
    # for each pair of resource type and folder, generate all found resources
    for folder_type, folder in folders.items():
        for f in find_files(folder, '*.*'):
            filename = File(f).rootname
            game = re.sub(file_suffix, '', clean_filename(filename)).lower()
            if game not in resources:
                resources[game] = {}
            if folder_type not in resources[game]:
                resources[game][folder_type] = []
            resources[game][folder_type].append(f)
    for game in resources.keys():
        for folder_type, files in resources[game].items():
            resources[game][folder_type].sort(key=get_resource_order)
    return resources


def get_game_resources(game_data, game_resources, resource_folders):
    game_title_clean = clean_filename(game_data['m_name']).lower()
    romname_clean = clean_filename(File(game_data['filename']).rootname_nosuffix).lower()
    if game_title_clean != romname_clean:
        possible_resource_names = [game_title_clean, romname_clean]
    else:
        possible_resource_names = [game_title_clean]
    possible_images = []
    for folder in resource_folders:
        for f in possible_resource_names:
            try:
                possible_images.extend(game_resources[f][folder])
            except KeyError:
                pass
    return possible_images


def add_game_resources(games, game_resources):
    for game_id, game_data in games.items():
        for resource_type, resource_folders in FOLDER_RESOURCE_TYPES.items():
            possible_images = get_game_resources(game_data, game_resources, resource_folders)
            try:
                chosen_image = possible_images[0]
            except:
                chosen_image = ''
            try:
                games[game_id][resource_type] = chosen_image
            except KeyError:
                games [game_id] = {}
                games[game_id][resource_type] = chosen_image

## Main code
def generate_data():
    categories = launchbox.categories
    # the concept of launcher is the different emulators or direct executables under a platform in AEL
    # is not the same as in launchbox se we need to generate this
    launchers = AELLaunchersCatalog(launchbox.games)

    platform_folders = generate_platform_folders(os.path.join(launchbox.data_dir, 'Platforms.xml'))

    games = {}
    for launcher in launchers:
        game_resources = generate_game_resources(platform_folders[launcher.platform.name])
        games[launcher.id] = generate_games(launcher)
        add_game_resources(games[launcher.id], game_resources)
    return categories, launchers, games


def write_files(categories, launchers, games):
    ###############################################
    # generate AEL categories
    ###############################################

    root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
    control = ET.SubElement(root, "control")
    ET.SubElement(control, "update_timestamp").text = str(time.time())

    for category in categories:
        category_xml = ET.SubElement(root, "category")
        for key,value in AELCategory(category).items():
            ET.SubElement(category_xml, key).text = value

    for launcher in launchers:
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher.items():
            ET.SubElement(launcher_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'categories.xml'), pretty_print=True)

    ###############################################
    # generate AEL single launchers xml
    ###############################################

    single_launcher_xml_keys = ['id', 'm_name', 'categoryID', 'platform', 'rompath', 'romext']
    for launcher_ael in launchers:
        root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher_ael.items():
            if key in single_launcher_xml_keys:
                ET.SubElement(launcher_xml, key).text = value
        tree = ET.ElementTree(root)
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.xml'.format(launcher_ael['roms_base_noext']))
        tree.write(f_rom_base_noext, pretty_print=True)


    ###############################################
    # generate games JSON files per launcher
    ###############################################

    for launcher_ael in launchers:
        games_data = games[launcher_ael.id]
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_ael['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()

if __name__ == "__main__":
    categories, launchers, games = generate_data()
    write_files(categories, launchers, games)
