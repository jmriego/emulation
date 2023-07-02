import untangle
from files.file import File


class Game:
    def __init__(self, game_xml_node, platform, lbdir, resources_catalog):
        self.id = get_attribute_cdata(game_xml_node, 'ID')
        self.name = get_attribute_cdata(game_xml_node, 'Title')
        self.rom = File(get_attribute_cdata(game_xml_node, 'ApplicationPath'), lbdir)
        self.command_line = get_attribute_cdata(game_xml_node, 'CommandLine')
        self.emulator = get_attribute_cdata(game_xml_node, 'Emulator', 'Executables')
        self.notes = get_attribute_cdata(game_xml_node, 'Notes')
        self.star_rating = get_attribute_cdata(game_xml_node, 'StarRating')
        self.community_star_rating = get_attribute_cdata(game_xml_node, 'CommunityStarRating')
        self.community_star_rating_votes = get_attribute_cdata(game_xml_node, 'CommunityStarRatingTotalVotes')
        self.publisher = get_attribute_cdata(game_xml_node, 'Publisher')
        self.release_date = get_attribute_cdata(game_xml_node, 'ReleaseDate')
        self.release_year = get_attribute_cdata(game_xml_node, 'ReleaseDate')[:4]
        self.date_added = get_attribute_cdata(game_xml_node, 'DateAdded')
        self.date_modified = get_attribute_cdata(game_xml_node, 'DateModified')
        self.developer = get_attribute_cdata(game_xml_node, 'Developer')
        self.genre = get_attribute_cdata(game_xml_node, 'Genre')
        self.play_mode = get_attribute_cdata(game_xml_node, 'PlayMode')
        self.completed = get_attribute_cdata(game_xml_node, 'Completed')
        if get_attribute_cdata(game_xml_node, 'UseDosBox').lower() == 'true':
            self.dosbox_conf = get_attribute_cdata(game_xml_node, 'DosBoxConfigurationPath')
        else:
            self.dosbox_conf = None
        self.platform = platform
        self.resources_catalog = resources_catalog
        self.disks = []
        self.additional_applications = {}

    def add_application(self, additional_xml_node):
        use_emulator = get_attribute_cdata(additional_xml_node, 'UseEmulator').lower() == "true"
        emulator_id = get_attribute_cdata(additional_xml_node, 'EmulatorId')
        application_path = get_attribute_cdata(additional_xml_node, 'ApplicationPath')
        if use_emulator and emulator_id == self.emulator.id:
            self.disks.append(File(application_path, self.rom.basedir))
        else:
            additional_application_id = get_attribute_cdata(additional_xml_node, 'Id')
            self.additional_applications[additional_application_id] = {
                'name': get_attribute_cdata(additional_xml_node, 'Name'),
                'path': application_path,
                'command_line': get_attribute_cdata(additional_xml_node, 'CommandLine'),
                'autorun_before': get_attribute_cdata(additional_xml_node, 'AutoRunBefore') == "true",
                'autorun_after': get_attribute_cdata(additional_xml_node, 'AutoRunAfter') == "true"}

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
            print('Generating list of {} games '.format(platform.name))
            games_xml = untangle.parse(File([platforms_xml_dir, '{}.xml'.format(platform.name)]).absolute)
            for game_xml_node in games_xml.LaunchBox.Game:
                game = Game(game_xml_node, platform, lbdir, resources_catalog)
                try:
                    game.emulator = emulators[game.emulator]
                    games[game.id] = game
                except KeyError:
                    print('Game {} does not have a valid emulator configuration'.format(game.name))
            for additional_xml_node in getattr(games_xml.LaunchBox, 'AdditionalApplication', []):
                game_id = get_attribute_cdata(additional_xml_node, 'GameID')
                games[game_id].add_application(additional_xml_node)
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
