import os
from files.file import File
from launchbox.catalog import LaunchBox
from ael.launcher import LaunchersCatalog as AELLaunchersCatalog
from ael.game import Game as AELGame
from ael.category import Category as AELCategory
from lxml import etree as ET
import json
import time
import configparser

config = configparser.RawConfigParser()
config.read(File([os.path.dirname(__file__), 'config.ini']).absolute)

LBDIR = config.get('launchbox', 'dir')
AELDIR = os.path.expandvars(config.get('ael', 'dir'))
DOSBOX_EXE = config.get('dosbox', 'exe')
DOSBOX_ARGS = config.get('dosbox', 'args')

os.chdir(LBDIR)
launchbox = LaunchBox(LBDIR)


# Functions used
def generate_games(launcher):
    # loop in the games xml
    result = {}
    for game in launcher.games:
        result[game.id] = dict(AELGame(game, DOSBOX_EXE, DOSBOX_ARGS))
    return result


# Main code
def generate_data():
    categories = launchbox.categories
    # the concept of launcher is the different emulators or direct executables under a platform in AEL
    # is not the same as in launchbox se we need to generate this
    launchers = AELLaunchersCatalog(launchbox.games)
    games = {}
    for launcher in launchers:
        games[launcher.id] = generate_games(launcher)
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
        games_data = games[launcher_ael.id]
        f_rom_base_noext = os.path.join(AELDIR, 'db_ROMs', '{}.json'.format(launcher_ael['roms_base_noext']))
        f = open(f_rom_base_noext, 'w')
        json.dump(games_data, f, indent=2)
        f.close()


if __name__ == "__main__":
    categories, launchers, games = generate_data()
    write_files(categories, launchers, games)
