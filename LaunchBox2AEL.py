import os
import ntpath as path
from file_utils import absolute_path, find_files, clean_filename, extract_path_parts
import untangle
from lxml import etree as ET
import re
from collections import OrderedDict
import json
from hashlib import md5
import time
import pandas as pd

## REQUIRED SETTINGS !!!
#Use forward slashes / instead of backslashes \
LBDIR = "/Users/jvalenzuela/LaunchBox"
AELDIR = "/Users/jvalenzuela/LaunchBox/ael/kodi"
## END REQUIRED SETTINGS !!!

## Directories inside LaunchBox
LBDATADIR = os.path.join(LBDIR, "Data")
LBIMGDIR = os.path.join(LBDIR, "Images")

## Prefered directories for each image type
folder_resource_types = {
  's_banner': ['Banner', 'Steam Banner', 'Arcade - Marquee'],
  's_boxback': ['Box - Back'],
  's_boxfront': ['Box - Front'],
  's_cartridge': ['Cart - Front', 'Cart - 3D', 'Cart - Back'],
  's_clearlogo': ['Clear Logo'],
  's_fanart': ['Fanart'],
  's_flyer': ['Flyer - Front', 'Flyer - Back'],
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
        category['default_thumb'] = "s_thumb"
        category['default_fanart'] = "s_fanart"
        category['default_banner'] = "s_banner"
        category['default_poster'] = "s_flyer"
        category['s_thumb'] = ""
        category['s_fanart'] = ""
        category['s_banner'] = ""
        category['s_flyer'] = ""
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
        game_path = game_xml.ApplicationPath.cdata
        dirname,file = path.split(game_path)
        filename,extension = path.splitext(file)
        extension = extension[1:] # remove the dot
        if dirname not in launchers[emulator_id]['paths']:
            launchers[emulator_id]['paths'].append(dirname)
        if extension not in launchers[emulator_id]['extensions']:
            launchers[emulator_id]['extensions'].append(extension)
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
    emulator['path'] = ''
    emulator['id'] = 'Executables'
    emulator['title'] = 'Executables'
    emulators[emulator['id']] = emulator
    return emulators


def generate_launchers(platforms_xml):
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
            launcher['categoryID'] = md5(get_attribute_cdata(platform_xml, 'Category').encode()).hexdigest()
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
            launcher['default_thumb'] = "s_thumb"
            launcher['default_fanart'] = "s_fanart"
            launcher['default_banner'] = "s_banner"
            launcher['default_poster'] = "s_flyer"
            launcher['roms_default_thumb'] = "s_boxfront"
            launcher['roms_default_fanart'] = "s_fanart"
            launcher['roms_default_banner'] = "s_banner"
            launcher['roms_default_poster'] = "s_flyer"
            launcher['roms_default_clearlogo'] = "s_clearlogo"
            launcher['s_thumb'] = absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Banner', platform_name + '.jpg'])
            launcher['s_fanart'] = absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Fanart', platform_name + '.jpg'])
            launcher['s_banner'] = absolute_path([LBIMGDIR, 'Platforms', platform_name, 'Banner', platform_name + '.jpg'])
            launcher['s_flyer'] = ""
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
        #TODO don't replace
        platform_folders[platform_name][media_type] = absolute_path([LBDIR, media_path]).replace('\\', '/')
    return platform_folders


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
        'm_studio':'Developer',
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
        result[game_id] = {}
        for key,value in game_info.iteritems():
            result[game_id][key] = get_attribute_cdata(game_xml, value)
        # these values are special in some way
        result[game_id]['m_year'] = result[game_id]['m_year'][:4]
        result[game_id]['disks'] = []
        result[game_id]['nointro_status'] = "None"
    return result


def get_resource_order(f):
    file_suffix = re.compile('-?[0-9]*$')
    filename,extension = path.splitext(f)
    try:
        order = abs(int(file_suffix.search(filename).group(0)))
    except ValueError:
        order = 9999
    return order


# generate a list of resources per game
def generate_game_resources(folders):
    file_suffix = re.compile('-?[0-9]*$')
    resources = {}
    # for each pair of resource type and folder, generate all found resources
    for folder_type, folder in folders.iteritems():
        for f in find_files(folder, '*.*'):
            f = f.replace('\\', '/') #TODO remove this in windows
            dirname,file = path.split(f)
            filename,extension = path.splitext(file)
            game = re.sub(file_suffix, '', clean_filename(filename))
            if game not in resources:
                resources[game] = {}
            if folder_type not in resources[game]:
                resources[game][folder_type] = []
            resources[game][folder_type].append(f)
    for game in resources.keys():
        for folder_type, files in resources[game].iteritems():
            resources[game][folder_type].sort(key=get_resource_order)
    return resources


def add_game_resources(games, game_resources):
    for game_id, game_data in games.iteritems():
        for resource_type, resource_folders in folder_resource_types.iteritems():
            game_title_clean = clean_filename(game_data['m_name'])
            possible_images = []
            for folder in resource_folders:
                try:
                    possible_images.extend(game_resources[game_title_clean][folder])
                except:
                    pass
            try:
                chosen_image = possible_images[0]
            except:
                chosen_image = ''
            games[game_id][resource_type] = chosen_image
    return games

## Main code
def write_files():
    categories = generate_categories(os.path.join(LBDATADIR, 'Platforms.xml'))
    launchers = generate_launchers(os.path.join(LBDATADIR, 'Platforms.xml'))
    platform_folders = generate_platform_folders(os.path.join(LBDATADIR, 'Platforms.xml'))

    games = {}
    for launcher, launcher_dict in launchers.iteritems():
        game_resources = generate_game_resources(platform_folders[launcher_dict['platform']])
        games[launcher] = generate_games(launcher_dict['platform'], launcher_dict['id'])
        games[launcher] = add_game_resources(games[launcher], game_resources)

    ###############################################
    # generate AEL categories
    ###############################################

    root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
    control = ET.SubElement(root, "control")
    ET.SubElement(control, "update_timestamp").text = str(time.time())

    for category in categories:
        category_xml = ET.SubElement(root, "category")
        for key,value in category.iteritems():
            ET.SubElement(category_xml, key).text = value

    for launcher_name, launcher_data in launchers.iteritems():
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher_data.iteritems():
            ET.SubElement(launcher_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'categories.xml'), pretty_print=True)

    ###############################################
    # generate AEL single launchers xml
    ###############################################

    single_launcher_xml_keys = ['id', 'm_name', 'categoryID', 'platform', 'rompath', 'romext']
    for launcher_name, launcher_data in launchers.iteritems():
        root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
        launcher_xml = ET.SubElement(root, "launcher")
        for key,value in launcher_data.iteritems():
            if key in single_launcher_xml_keys:
                ET.SubElement(launcher_xml, key).text = value
        tree = ET.ElementTree(root)
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.xml'.format(launcher_data['roms_base_noext']))
        tree.write(f_rom_base_noext, pretty_print=True)


    ###############################################
    # generate games JSON files per launcher
    ###############################################

    for launcher, launcher_data in launchers.iteritems():
        games_data = games[launcher]
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_data['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()

if __name__ == "__main__":
    write_files()
