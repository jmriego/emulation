import untangle
from files.file import File


class Game:
    def __init__(self, game_xml_node, platform, lbdir, resources_catalog):
        self.id = get_attribute_cdata(game_xml_node, 'ID')
        self.name = get_attribute_cdata(game_xml_node, 'Title')
        self.path_file = File([lbdir, get_attribute_cdata(game_xml_node, 'ApplicationPath')])
        self.path = self.path_file.absolute
        self.emulator = get_attribute_cdata(game_xml_node, 'Emulator', 'Executables')
        self.notes = get_attribute_cdata(game_xml_node, 'Notes')
        self.publisher = get_attribute_cdata(game_xml_node, 'Publisher')
        self.release_date = get_attribute_cdata(game_xml_node, 'ReleaseDate')
        self.release_year = get_attribute_cdata(game_xml_node, 'ReleaseDate')[:4]
        self.developer = get_attribute_cdata(game_xml_node, 'Developer')
        self.genre = get_attribute_cdata(game_xml_node, 'Genre')
        self.completed = get_attribute_cdata(game_xml_node, 'Completed')
        if get_attribute_cdata(game_xml_node, 'UseDosBox') == 'True':
            self.dosbox_conf = get_attribute_cdata(game_xml_node, 'DosBoxConfigurationPath')
        else:
            self.dosbox_conf = None
        self.platform = platform
        self.resources_catalog = resources_catalog

    def search_images(self, image_type):
        return self.resources_catalog.search_images(image_type, game=self)

    def search_manuals(self):
        return self.resources_catalog.search_manuals(game=self)

    def search_trailers(self):
        return self.resources_catalog.search_trailers(game=self)


class GamesCatalog:
    def __init__(self, platforms_xml_dir, platforms, emulators, lbdir, resources_catalog):
        games = {}
        for platform in platforms:
            games_xml = untangle.parse(File([platforms_xml_dir, '{}.xml'.format(platform.name)]).absolute)
            for game_xml_node in games_xml.LaunchBox.Game:
                game = Game(game_xml_node, platform, lbdir, resources_catalog)
                game.emulator = emulators[game.emulator]
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
