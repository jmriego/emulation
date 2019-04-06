import os
import ntpath as path
from files.file import File, find_files
from launchbox.catalog import LaunchBox
from ael.launcher import AELLaunchersCatalog
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
import unicodedata

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

BAD_CHARS_IN_FILENAME = ":/'"

## Functions used

def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default


def clean_filename(filename):
    filename_no_bad_chars = ''.join('_' if c in BAD_CHARS_IN_FILENAME else c for c in filename)
    try:
        return unicodedata.normalize('NFC', filename_no_bad_chars)
    except TypeError:
        return filename_no_bad_chars


def find_first_file(startdir, pattern, mode='win'):
    results = find_files(startdir, pattern, mode)
    try:
        return results[0]
    except IndexError:
        return None


def launcher_to_ael(launcher):
    return OrderedDict((
                ('id', launcher.id),
                ('m_name', launcher.platform.name if len(launcher.games) == 1 else launcher.name),
                ('categoryID', launcher.platform.category.id),
                ('platform', launcher.platform.name),
                ('rompath', path.commonprefix(list(launcher.paths))),
                ('romext', ','.join(launcher.extensions)),
                ('m_year', launcher.platform.release_year),
                ('m_genre', ""),
                ('m_studio', launcher.platform.developer),
                ('m_plot', ""),
                ('m_rating', ""),
                ('application', launcher.emulator.path),
                ('args', launcher.emulator.args.format('$rom$')),
                ('finished', "False"),
                ('minimize', "False"),
                ('roms_base_noext', clean_filename("LB2AEL_{}_roms".format(launcher.name.replace(' ', '_')))),
                ('nointro_xml_file', ""),
                ('nointro_display_mode', "All ROMs"),
                ('pclone_launcher', "False"),
                ('num_roms', str(len(launcher.games))),
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
                ('s_icon', find_first_file([launchbox.images_dir, 'Platforms', launcher.platform.name, 'Banner'], '*.*')),
                ('s_fanart', find_first_file([launchbox.images_dir, 'Platforms', launcher.platform.name, 'Fanart'], '*.*')),
                ('s_banner', find_first_file([launchbox.images_dir, 'Platforms', launcher.platform.name, 'Banner'], '*.*')),
                ('s_poster', ""),
                ('s_clearlogo', find_first_file([launchbox.images_dir, 'Platforms', launcher.platform.name, 'Clear Logo'], '*.*')),
                ('s_trailer', ""), #TODO this and lower down
                ('path_banner', "E:\\Juegos\\Emulation\\AEL\\{}\\banner".format(launcher.platform.name)),
                ('path_clearlogo', "E:\\Juegos\\Emulation\\AEL\\{}\\clearlogo".format(launcher.platform.name)),
                ('path_fanart', "E:\\Juegos\\Emulation\\AEL\\{}\\fanart".format(launcher.platform.name)),
                ('path_title', "E:\\Juegos\\Emulation\\AEL\\{}\\titles".format(launcher.platform.name)),
                ('path_snap', "E:\\Juegos\\Emulation\\AEL\\{}\\snap".format(launcher.platform.name)),
                ('path_boxfront', "E:\\Juegos\\Emulation\\AEL\\{}\\boxfront".format(launcher.platform.name)),
                ('path_boxback', "E:\\Juegos\\Emulation\\AEL\\{}\\boxback".format(launcher.platform.name)),
                ('path_cartridge', "E:\\Juegos\\Emulation\\AEL\\{}\\cartridges".format(launcher.platform.name)),
                ('path_flyer', "E:\\Juegos\\Emulation\\AEL\\{}\\flyers".format(launcher.platform.name)),
                ('path_map', "E:\\Juegos\\Emulation\\AEL\\{}\\maps".format(launcher.platform.name)),
                ('path_manual', "E:\\Juegos\\Emulation\\AEL\\{}\\manuals".format(launcher.platform.name)),
                ('path_trailer', "E:\\Juegos\\Emulation\\AEL\\{}\\trailers".format(launcher.platform.name))
            ))


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
        result[game.id] = {
            'altapp':'',
            'altarg':'',
            'filename':game.path,
            'disks':'',
            'm_nplayers':'',
            'finished':game.completed,
            'id':game.id,
            'm_genre':game.genre,
            'm_name':game.name,
            'm_plot':game.notes,
            'm_rating':'',
            'm_esrb':'',
            'm_developer':game.developer,
            'm_year':game.release_year,
            'nointro_status':'',
            's_map':'',
            'pclone_status':''}

        # these values are special in some way
        if '://' in result[game.id]['filename']:
            uri = result[game.id]['filename']
            result[game.id]['altapp'] = get_associated_app(uri)
            result[game.id]['altarg'] = uri
            result[game.id]['filename'] = '.'
        elif game.dosbox_conf:
            result[game.id]['altapp'] = DOSBOX_EXE
            result[game.id]['altarg'] = DOSBOX_ARGS.format(game.dosbox_conf)
        elif game.emulator.id == 'Executables':
            result[game.id]['altapp'] = result[game.id]['filename']
            result[game.id]['altarg'] = ' '
        else:
            result[game.id]['filename'] = File([LBDIR, result[game.id]['filename']]).absolute
        result[game.id]['m_year'] = result[game.id]['m_year'][:4]
        result[game.id]['disks'] = []
        result[game.id]['nointro_status'] = "None"
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
        for key,value in launcher_to_ael(launcher).items():
            ET.SubElement(launcher_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'categories.xml'), pretty_print=True)

    ###############################################
    # generate AEL single launchers xml
    ###############################################

    single_launcher_xml_keys = ['id', 'm_name', 'categoryID', 'platform', 'rompath', 'romext']
    for launcher in launchers:
        launcher_ael = launcher_to_ael(launcher)
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

    for launcher in launchers:
        launcher_ael = launcher_to_ael(launcher)
        games_data = games[launcher.id]
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_ael['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()

if __name__ == "__main__":
    categories, launchers, games = generate_data()
    write_files(categories, launchers, games)
