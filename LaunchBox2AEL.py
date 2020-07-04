import os
from files.file import File
from launchbox.catalog import LaunchBox
from ael.launcher import LaunchersCatalog as AELLaunchersCatalog
from ael.category import Category as AELCategory
from ael.collection import CollectionsCatalog as AELCollectionsCatalog
from lxml import etree as ET
import json
import time
import configparser

config = configparser.RawConfigParser()
config.read(File([os.path.dirname(__file__), 'config.ini']).absolute)

LBDIR = config.get('launchbox', 'dir')
if not File([LBDIR, 'Launchbox.exe']).exists():
    raise IOError('Incorrect LaunchBox configuration. Cannot find LaunchBox.exe on that folder')

AELDIR = os.path.expandvars(config.get('ael', 'dir'))
if not File([AELDIR, 'categories.xml']).exists():
    raise IOError('Incorrect AEL configuration. Cannot find categories.xml on that folder')

DOSBOX_EXE = config.get('dosbox', 'exe')
DOSBOX_ARGS = config.get('dosbox', 'args')

os.chdir(LBDIR)
launchbox = LaunchBox(LBDIR)


# Main code
def generate_data():
    categories = launchbox.categories
    # the concept of launcher is the different emulators or direct executables under a platform in AEL
    # is not the same as in launchbox se we need to generate this
    launchers = AELLaunchersCatalog(launchbox.games, DOSBOX_EXE, DOSBOX_ARGS, AELDIR)
    collections = AELCollectionsCatalog(launchers, launchbox.playlists)
    return categories, launchers, collections


def write_files(categories, launchers, collections):
    ###############################################
    # generate AEL categories
    ###############################################

    root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
    control = ET.SubElement(root, "control")
    ET.SubElement(control, "update_timestamp").text = str(time.time())

    for category in categories:
        category_xml = ET.SubElement(root, "category")
        for key, value in AELCategory(category).items():
            ET.SubElement(category_xml, key).text = value

    for launcher in launchers:
        launcher_xml = ET.SubElement(root, "launcher")
        for key, value in launcher.items():
            ET.SubElement(launcher_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'categories.xml'), pretty_print=True)

    ###############################################
    # generate AEL single launchers xml
    ###############################################

    single_launcher_xml_keys = ['id', 'm_name', 'categoryID', 'platform', 'rompath', 'romext']
    for launcher_ael in launchers:
        if not launcher_ael.games:
            continue
        root = ET.Element("advanced_emulator_launcher_ROMs", version="1")
        launcher_xml = ET.SubElement(root, "launcher")
        for key, value in launcher_ael.items():
            if key in single_launcher_xml_keys:
                ET.SubElement(launcher_xml, key).text = value
        tree = ET.ElementTree(root)
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.xml'.format(launcher_ael['roms_base_noext']))
        tree.write(f_rom_base_noext, pretty_print=True)

    ###############################################
    # generate games JSON files per launcher
    ###############################################

    for launcher_ael in launchers:
        if not launcher_ael.games:
            continue
        games_data = {g['id']: dict(g) for g in launcher_ael.games}
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_ael['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()

    ###############################################
    # generate AEL collections
    ###############################################

    root = ET.Element("advanced_emulator_launcher_Collection_index", version="1")
    control = ET.SubElement(root, "control")
    ET.SubElement(control, "update_timestamp").text = str(time.time())

    for collection in collections:
        if not collection.games:
            continue
        collection_xml = ET.SubElement(root, "Collection")
        for key, value in collection.items():
            ET.SubElement(collection_xml, key).text = value

    tree = ET.ElementTree(root)
    tree.write(os.path.join(AELDIR, 'collections.xml'), pretty_print=True)

    ###############################################
    # generate games JSON files per launcher
    ###############################################

    for collection in collections:
        if not collection.games:
            continue
        games_data = [dict(g) for g in collection.games]
        collection_data = []
        collection_data.append(
            {"control":"Advanced Emulator Launcher Collection ROMs",
             "version":1})
        collection_data.append(games_data)

        f_rom_base_noext = os.path.join(AELDIR, 'db_Collections', '{}.json'.format(collection['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(collection_data, f, indent=2)
        f.close()

if __name__ == "__main__":
    categories, launchers, collections = generate_data()
    write_files(categories, launchers, collections)
