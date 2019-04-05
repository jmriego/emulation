import untangle
from hashlib import md5
from files.file import File

class Game:
    def __init__(self, game_xml_node, platform):
        self.id = get_attribute_cdata(game_xml_node, 'ID')
        self.name = get_attribute_cdata(game_xml_node, 'Title')
        self.path = get_attribute_cdata(game_xml_node, 'ApplicationPath')
        self.emulator = get_attribute_cdata(game_xml_node, 'Emulator')
        self.notes = get_attribute_cdata(game_xml_node, 'Notes')
        self.publisher = get_attribute_cdata(game_xml_node, 'Publisher')
        self.release_date = get_attribute_cdata(game_xml_node, 'ReleaseDate')
        self.release_year = get_attribute_cdata(game_xml_node, 'ReleaseDate')[:4]
        self.developer = get_attribute_cdata(game_xml_node, 'Developer')
        self.genre = get_attribute_cdata(game_xml_node, 'Genre')
        if get_attribute_cdata(game_xml_node, 'UseDosBox'):
            self.dosbox_conf = get_attribute_cdata(game_xml_node, 'DosBoxConfigurationPath')
        self.platform = platform


class GamesCatalog:
    def __init__(self, platforms_xml_dir, platforms):
        games = {}
        for platform in platforms:
            games_xml = untangle.parse(File([platforms_xml_dir, '{}.xml'.format(platform.name)]).absolute)
            for game_xml_node in games_xml.LaunchBox.Game:
                game = Game(game_xml_node, platform)
                games[game.id] = game
            self.games = games

    def __iter__(self):
        return iter(self.games.values())

    def __getitem__(self, key):
        return self.games[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
