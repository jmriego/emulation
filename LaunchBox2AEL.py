import os
from files.file import File
from launchbox.catalog import LaunchBox
from ael.launcher import LaunchersCatalog as AELLaunchersCatalog
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


# Main code
def generate_data():
    categories = launchbox.categories
    # the concept of launcher is the different emulators or direct executables under a platform in AEL
    # is not the same as in launchbox se we need to generate this
    launchers = AELLaunchersCatalog(launchbox.games, DOSBOX_EXE, DOSBOX_ARGS)
    return categories, launchers


def write_files(categories, launchers):
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
    # generate recent games JSON file
    ###############################################

    all_games_data = {}
    for launcher_ael in launchers:
        for ael_game in launcher_ael.games:
            all_games_data[ael_game['id']] = {**dict(launcher_ael), **dict(ael_game)}

    def update_game(game):
        for key in game.keys():
            try:
                new_value = all_games_data[game['id']][key]
                if str(type(game[key])) == str(type(new_value)):
                    game[key] = new_value
                else:
                    if type(game[key]) is bool:
                        game[key] = new_value.lower() == 'true' 
            except KeyError:
                pass
        return game

    f_recent_games = os.path.join(AELDIR, 'history.json')
    with open(f_recent_games) as f:
        recents_data = json.load(f)
    recents_data[1] = [update_game(g) for g in recents_data[1]]
    f = open(f_recent_games, 'w', encoding='utf-8')
    json.dump(recents_data, f, indent=1, ensure_ascii=False)
    f.close()

    f_most_played_games = os.path.join(AELDIR, 'most_played.json')
    with open(f_most_played_games) as f:
        most_playeds_data = json.load(f)
    most_playeds_data[1] = {g_id: update_game(g) for g_id, g in most_playeds_data[1].items()}
    f = open(f_most_played_games, 'w', encoding='utf-8')
    json.dump(most_playeds_data, f, indent=1, ensure_ascii=False)
    f.close()

if __name__ == "__main__":
    categories, launchers = generate_data()
    write_files(categories, launchers)
