import logging
import untangle
from files.file import File, find_files

logger = logging.getLogger(__name__)


class Playlist:
    def __init__(self, playlist_xml_file, games_catalog):
        playlist_xml = untangle.parse(playlist_xml_file)
        # there should really be only one Playlist node
        for playlist_xml_node in playlist_xml.LaunchBox.Playlist:
            logger.debug('Processing next emulator platform')
            self.id = get_attribute_cdata(playlist_xml_node, 'PlaylistId')
            self.name = get_attribute_cdata(playlist_xml_node, 'Name')
            logger.debug('Adding games to playlist %s', self.name)

        self.games = []
        for game_xml_node in playlist_xml.LaunchBox.PlaylistGame:
            logger.debug('Processing next playlist game')
            game_id = get_attribute_cdata(game_xml_node, 'GameId')
            try:
                game = games_catalog[game_id]
                self.games.append(game)
                logger.debug('Assigned game %s to playlist %s', game.name, self.name)
            except KeyError:
                logger.warn('This game id doesnt seem to exist: %s', game_id)
                pass


class PlaylistsCatalog:
    def __init__(self, playlist_xml_dir, games_catalog):
        self.playlists = {}
        for f in find_files(playlist_xml_dir, '*.xml'):
            logger.debug('Processing next emulator platform in file %s', f)
            playlist = Playlist(f, games_catalog)
            self.playlists[playlist.id] = playlist

    def __iter__(self):
        return iter(self.playlists.values())

    def __getitem__(self, key):
        return self.playlists[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
