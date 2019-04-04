import os
import ntpath as path
from file_utils import absolute_path, find_files, find_first_file, extract_path_parts
import untangle
from lxml import etree as ET
import re
from collections import OrderedDict
import json
from hashlib import md5
import time
import winreg
import shlex
import configparser

config = configparser.RawConfigParser()
config.read('config.ini')
print(config.sections())

LBDIR = config.get('launchbox', 'dir')
AELDIR = config.get('ael', 'dir').replace('%LOCALAPPDATA%', os.getenv('LOCALAPPDATA'))
DOSBOX_EXE = config.get('dosbox', 'exe')
DOSBOX_ARGS = config.get('dosbox', 'args')

## Directories inside LaunchBox
LBDATADIR = os.path.join(LBDIR, "Data")
LBIMGDIR = os.path.join(LBDIR, "Images")

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


def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


def generate_categories(platforms_xml):
    categories = []
    xml = untangle.parse(platforms_xml)
    for category_xml in xml.LaunchBox.PlatformCategory:
        category = OrderedDict({})
        category_name = category_xml.Name.cdata
        category['id'] = md5(category_name.encode()).hexdigest()
        category['m_name'] = category_name
        category['m_genre'] = category_name
        category['m_plot'] = category_xml.Notes.cdata
        category['m_rating'] = ""
        category['finished'] = "False"
        category['default_thumb'] = "s_icon"
        category['default_fanart'] = "s_fanart"
        category['default_banner'] = "s_banner"
        category['default_poster'] = "s_poster"
        category['s_icon'] = ""
        category['s_fanart'] = ""
        category['s_banner'] = ""
        category['s_poster'] = ""
        category['s_clearlogo'] = ""
        category['s_trailer'] = ""
        categories.append(category)
    return categories

def generate_platform_launchers(games_xml, emulators):
    xml = untangle.parse(games_xml)
    launchers = {}
    for game_xml in xml.LaunchBox.Game:
        # get the emulator for this game. If not found, it's an executable file
        emulator_id = get_attribute_cdata(game_xml, 'Emulator', 'Executables')
        emulator = emulators[emulator_id]
        if not emulator_id in launchers:
            launchers[emulator_id] = {}
            launchers[emulator_id]['title'] = emulator['title']
            launchers[emulator_id]['emulator_path'] = emulator['path']
            launchers[emulator_id]['paths'] = []
            launchers[emulator_id]['extensions'] = []
            launchers[emulator_id]['game_count'] = 0
        launchers[emulator_id]['game_count'] += 1
        game_path = get_attribute_cdata(game_xml, 'ApplicationPath')
        if '://' not in game_path:
            f = extract_path_parts(absolute_path([LBDIR, game_path]))
            if f['dirname'] not in launchers[emulator_id]['paths']:
                launchers[emulator_id]['paths'].append(f['dirname'])
            if f['extension'] not in launchers[emulator_id]['extensions']:
                launchers[emulator_id]['extensions'].append(f['extension'])
    return launchers


def get_emulators(emulators_xml):
    xml = untangle.parse(emulators_xml)
    emulators = {}
    for emulators_xml in xml.LaunchBox.Emulator:
        emulator = {}
        emulator['path'] = get_attribute_cdata(emulators_xml, 'ApplicationPath')
        emulator['id'] = get_attribute_cdata(emulators_xml, 'ID')
        emulator['title'] = get_attribute_cdata(emulators_xml, 'Title')
        emulators[emulator['id']] = emulator
    # Add direct executables as another (fake) emulator
    emulator = {}
    emulator['path'] = r'E:\Juegos\Emulation\default_launcher.bat'
    emulator['id'] = 'Executables'
    emulator['title'] = 'Executables'
    emulators[emulator['id']] = emulator
    return emulators


def generate_launchers(platforms_xml, parents_xml):
    categories = {}
    xml = untangle.parse(parents_xml)
    for parent_xml in xml.LaunchBox.Parent:
        platform_name = get_attribute_cdata(parent_xml, 'PlatformName')
        category_name = get_attribute_cdata(parent_xml, 'ParentPlatformCategoryName')
        categories[platform_name] = categories.get(platform_name, category_name)

    launchers = OrderedDict({})
    xml = untangle.parse(platforms_xml)
    emulators = get_emulators(os.path.join(LBDATADIR, 'Emulators.xml'))
    for platform_xml in xml.LaunchBox.Platform:
        platform_name = get_attribute_cdata(platform_xml, 'Name')
        platform_launchers = generate_platform_launchers(os.path.join(LBDATADIR,'Platforms','{}.xml'.format(platform_name)), emulators)
        for launcher_id in platform_launchers:
            platform_launcher_name = '{} ({})'.format(platform_name, platform_launchers[launcher_id]['title'])
            launcher = OrderedDict({})
            launcher['id'] = md5('{} {}'.format(platform_name, launcher_id).encode()).hexdigest()
            launcher['m_name'] = platform_name if len(platform_launchers)==1 else platform_launcher_name
            launcher['categoryID'] = md5(categories[platform_name].encode()).hexdigest()
            launcher['platform'] = platform_name
            launcher['rompath'] = path.commonprefix(platform_launchers[launcher_id]['paths'])
            launcher['romext'] = ','.join(platform_launchers[launcher_id]['extensions'])
            launcher['m_year'] = get_attribute_cdata(platform_xml, 'ReleaseDate')[:4]
            launcher['m_genre'] = ""
            launcher['m_studio'] = get_attribute_cdata(platform_xml, 'Developer')
            launcher['m_plot'] = ""
            launcher['m_rating'] = ""
            launcher['application'] = platform_launchers[launcher_id]['emulator_path']
            launcher['args'] = '"$rom$"' # TODO get from LaunchBox
            launcher['finished'] = "False"
            launcher['minimize'] = "False"
            launcher['roms_base_noext'] = clean_filename("LB2AEL_{}_roms".format(platform_launcher_name.replace(' ', '_')))
            launcher['nointro_xml_file'] = ""
            launcher['nointro_display_mode'] = "All ROMs"
            launcher['pclone_launcher'] = "False"
            launcher['num_roms'] = str(platform_launchers[launcher_id]['game_count'])
            launcher['num_parents'] = "0"
            launcher['num_clones'] = "0"
            launcher['timestamp_launcher'] = str(time.time())
            launcher['timestamp_report'] = "0.0"
            launcher['default_thumb'] = "s_icon"
            launcher['default_fanart'] = "s_fanart"
            launcher['default_banner'] = "s_banner"
            launcher['default_poster'] = "s_poster"
            launcher['roms_default_icon'] = "s_boxfront"
            launcher['roms_default_fanart'] = "s_fanart"
            launcher['roms_default_banner'] = "s_banner"
            launcher['roms_default_poster'] = "s_poster"
            launcher['roms_default_clearlogo'] = "s_clearlogo"
            launcher['s_icon'] = find_first_file(absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Banner']), '*.*')
            launcher['s_fanart'] = find_first_file(absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Fanart']), '*.*')
            launcher['s_banner'] = find_first_file(absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Banner']), '*.*')
            launcher['s_poster'] = ""
            launcher['s_clearlogo'] = absolute_path([LBIMGDIR, 'Platforms', platform_launcher_name, 'Clear Logo'])
            launcher['s_trailer'] = ""
            launcher['path_banner'] = "E:\\Juegos\\Emulation\\AEL\\{}\\banner".format(platform_launcher_name)
            launcher['path_clearlogo'] = "E:\\Juegos\\Emulation\\AEL\\{}\\clearlogo".format(platform_launcher_name)
            launcher['path_fanart'] = "E:\\Juegos\\Emulation\\AEL\\{}\\fanart".format(platform_launcher_name)
            launcher['path_title'] = "E:\\Juegos\\Emulation\\AEL\\{}\\titles".format(platform_launcher_name)
            launcher['path_snap'] = "E:\\Juegos\\Emulation\\AEL\\{}\\snap".format(platform_launcher_name)
            launcher['path_boxfront'] = "E:\\Juegos\\Emulation\\AEL\\{}\\boxfront".format(platform_launcher_name)
            launcher['path_boxback'] = "E:\\Juegos\\Emulation\\AEL\\{}\\boxback".format(platform_launcher_name)
            launcher['path_cartridge'] = "E:\\Juegos\\Emulation\\AEL\\{}\\cartridges".format(platform_launcher_name)
            launcher['path_flyer'] = "E:\\Juegos\\Emulation\\AEL\\{}\\flyers".format(platform_launcher_name)
            launcher['path_map'] = "E:\\Juegos\\Emulation\\AEL\\{}\\maps".format(platform_launcher_name)
            launcher['path_manual'] = "E:\\Juegos\\Emulation\\AEL\\{}\\manuals".format(platform_launcher_name)
            launcher['path_trailer'] = "E:\\Juegos\\Emulation\\AEL\\{}\\trailers".format(platform_launcher_name)
            launchers[platform_launcher_name] = launcher
    return launchers

def generate_platform_folders(platforms_xml):
    platform_folders = OrderedDict({})
    xml = untangle.parse(platforms_xml)
    for folder_xml in xml.LaunchBox.PlatformFolder:
        platform_name = get_attribute_cdata(folder_xml, 'Platform')
        media_type = get_attribute_cdata(folder_xml, 'MediaType')
        media_path = get_attribute_cdata(folder_xml, 'FolderPath')
        if not platform_name in platform_folders:
            platform_folders[platform_name] = {}
        platform_folders[platform_name][media_type] = absolute_path([LBDIR, media_path])
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


def generate_games(platform, launcher_id):
    xml = untangle.parse(os.path.join(LBDATADIR,'Platforms','{}.xml'.format(platform)))
    # mapping of keys and values in the xml file
    game_info = {
        'altapp':'',
        'altarg':'',
        'filename':'ApplicationPath',
        'disks':'',
        'm_nplayers':'',
        'finished':'Completed',
        'id':'ID',
        'm_genre':'Genre',
        'm_name':'Title',
        'm_plot':'Notes',
        'm_rating':'',
        'm_esrb':'',
        'm_developer':'Developer',
        'm_year':'ReleaseDate',
        'nointro_status':'',
        's_map':'',
        'pclone_status':''
    }
    # loop in the games xml
    result = {}
    for game_xml in xml.LaunchBox.Game:
        # Only get the games inside this platform and launcher
        emulator_id = get_attribute_cdata(game_xml, 'Emulator', 'Executables')
        if launcher_id != md5('{} {}'.format(platform, emulator_id).encode()).hexdigest():
            continue
        game_id = get_attribute_cdata(game_xml, 'ID')
        dosbox_conf = get_attribute_cdata(game_xml, 'DosBoxConfigurationPath')
        result[game_id] = {}
        for key,value in game_info.items():
            result[game_id][key] = get_attribute_cdata(game_xml, value)
        # these values are special in some way
        if '://' in result[game_id]['filename']:
            uri = result[game_id]['filename']
            result[game_id]['altapp'] = get_associated_app(uri)
            result[game_id]['altarg'] = uri
            result[game_id]['filename'] = '.'
        elif dosbox_conf:
            result[game_id]['altapp'] = DOSBOX_EXE
            result[game_id]['altarg'] = DOSBOX_ARGS.format(dosbox_conf)
        elif emulator_id == 'Executables':
            result[game_id]['altapp'] = result[game_id]['filename']
            result[game_id]['altarg'] = ' '
        else:
            result[game_id]['filename'] = absolute_path([LBDIR, result[game_id]['filename']])
        result[game_id]['m_year'] = result[game_id]['m_year'][:4]
        result[game_id]['disks'] = []
        result[game_id]['nointro_status'] = "None"
    return result


def get_resource_order(f):
    file_suffix = re.compile('-?[0-9]*$')
    try:
        order = abs(int(extract_path_parts(f, 'suffix')))
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
            filename = extract_path_parts(f, 'rootname')
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
    romname_clean = clean_filename(extract_path_parts(game_data['filename'], 'rootname_nosuffix')).lower()
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
    categories = generate_categories(os.path.join(LBDATADIR, 'Platforms.xml'))
    launchers = generate_launchers(os.path.join(LBDATADIR, 'Platforms.xml'), os.path.join(LBDATADIR, 'Parents.xml'))
    platform_folders = generate_platform_folders(os.path.join(LBDATADIR, 'Platforms.xml'))

    games = {}
    for launcher, launcher_dict in launchers.items():
        game_resources = generate_game_resources(platform_folders[launcher_dict['platform']])
        games[launcher] = generate_games(launcher_dict['platform'], launcher_dict['id'])
        add_game_resources(games[launcher], game_resources)
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
        for key,value in category.items():
            ET.SubElement(category_xml, key).text = value

    for launcher_name, launcher_data in launchers.items():
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher_data.items():
            ET.SubElement(launcher_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'categories.xml'), pretty_print=True)

    ###############################################
    # generate AEL single launchers xml
    ###############################################

    single_launcher_xml_keys = ['id', 'm_name', 'categoryID', 'platform', 'rompath', 'romext']
    for launcher_name, launcher_data in launchers.items():
        root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher_data.items():
            if key in single_launcher_xml_keys:
                ET.SubElement(launcher_xml, key).text = value
        tree = ET.ElementTree(root)
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.xml'.format(launcher_data['roms_base_noext']))
        tree.write(f_rom_base_noext, pretty_print=True)


    ###############################################
    # generate games JSON files per launcher
    ###############################################

    for launcher, launcher_data in launchers.items():
        games_data = games[launcher]
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_data['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()

if __name__ == "__main__":
    categories, launchers, games = generate_data()
    write_files(categories, launchers, games)
