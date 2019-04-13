import untangle
from files.file import File, find_files


class Playlist:
    def __init__(self, playlist_xml_file, games_catalog):
        playlist_xml = untangle.parse(playlist_xml_file)
        # there should really be only one Playlist node
        for playlist_xml_node in playlist_xml.LaunchBox.Playlist:
            self.id = get_attribute_cdata(playlist_xml_node, 'PlaylistId')
            self.name = get_attribute_cdata(playlist_xml_node, 'Name')

        self.games = []
        for game_xml_node in playlist_xml.LaunchBox.PlaylistGame:
            game_id = get_attribute_cdata(game_xml_node, 'GameId')
            try:
                self.games.append(games_catalog[game_id])
            except KeyError:
                pass


class PlaylistsCatalog:
    def __init__(self, playlist_xml_dir, games_catalog):
        self.playlists = {}
        for f in find_files(playlist_xml_dir, '*.xml'):
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
