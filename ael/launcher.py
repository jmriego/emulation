from hashlib import md5
from files.file import File

# launcher is the combination of platform and either an emulator id or executables
class Launcher:
    def __init__(self, platform, emulator):
        self.name = '{} ({})'.format(platform.name, emulator.name)
        self.id = md5(self.name.encode()).hexdigest()
        self.platform = platform
        self.emulator = emulator
        self.games = []

    def add_game(self, game):
        self.games.append(game)

    @property
    def paths(self):
        paths = set()
        for game in self.games:
            if '://' not in game.path:
                f = File(game.path)
                paths.add(f.absolute_dir)
        return paths

    @property
    def extensions(self):
        extensions = set()
        for game in self.games:
            if '://' not in game.path:
                f = File(game.path)
                extensions.add(f.extension)
        return extensions


class LaunchersCatalog:
    def __init__(self, games):
        self.launchers = {}
        for game in games:
            launcher = Launcher(game.platform, game.emulator)
            try:
                self.launchers[launcher.id].add_game(game)
            except KeyError:
                launcher.add_game(game)
                self.launchers[launcher.id] = launcher

    def __iter__(self):
        return iter(self.launchers.values())

    def __getitem__(self, key):
        return self.launchers[key]

    def search(self, platform_name):
        for launcher in self.launchers.values():
            if launcher.platform.name == platform_name:
                yield launcher
