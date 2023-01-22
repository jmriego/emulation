from hashlib import md5
from collections import OrderedDict
import os
from launchbox.resource import clean_filename
from . import get_first_path
import time
from ael.game import Game


# launcher is the combination of platform and either an emulator id or executables
class Collection(OrderedDict):
    def __init__(self, lb_playlist):
        self.name = lb_playlist.name
        self.id = md5(self.name.encode()).hexdigest()
        self.games = []
        super(Collection, self).__init__((
                ('m_name', self.name),
                ('id', self.id),
                ('m_genre', ""),
                ('m_rating', ""),
                ('m_plot', ""),
                ('roms_base_noext', clean_filename("{}_{}".format(self.name.replace(' ', '_'), self.id[:6]))),
                ('default_icon', "s_icon"),
                ('default_fanart', "s_fanart"),
                ('default_banner', "s_banner"),
                ('default_poster', "s_poster"),
                ('default_clearlogo', "s_clearlogo"),
                ('s_icon', ""),
                ('s_fanart', ""),
                ('s_banner', ""),
                ('s_poster', ""),
                ('s_clearlogo', ""),
                ('s_trailer', "")
            ))

    def add_game(self, game):
        launcher = game.launcher
        game['application'] = launcher['application']
        game['args'] = launcher['args']
        game['platform'] = launcher['platform']
        game['romext'] = game.get('romext', launcher['romext'])
        game['rompath'] = launcher['rompath']
        game['roms_default_banner'] = launcher['roms_default_banner']
        game['roms_default_clearlogo'] = launcher['roms_default_clearlogo']
        game['roms_default_fanart'] = launcher['roms_default_fanart']
        game['roms_default_icon'] = launcher['roms_default_icon']
        game['roms_default_poster'] = launcher['roms_default_poster']

        game['args_extra'] = []
        game['fav_status'] = 'OK'
        game['launcherID'] = launcher.id

        self.games.append(game)


class CollectionsCatalog:
    def __init__(self, launchers, playlists):
        self.collections = {}
        self.games = {g['id']: g for launcher in launchers for g in launcher.games}

        for playlist in playlists:
            collection = Collection(playlist)
            for game in playlist.games:
                g = self.games[game.id]
                collection.add_game(g)
            self.collections[collection.id] = collection


    def __iter__(self):
        return iter(self.collections.values())

    def __getitem__(self, key):
        return self.collections[key]
