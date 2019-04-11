import unicodedata
from files.file import find_files
from collections import defaultdict, namedtuple
from . import BAD_CHARS_IN_FILENAME


def clean_filename(filename):
    filename_no_bad_chars = ''.join('_' if c in BAD_CHARS_IN_FILENAME else c for c in filename)
    try:
        return unicodedata.normalize('NFC', filename_no_bad_chars)
    except TypeError:
        return filename_no_bad_chars


def get_resource_order(f):
    try:
        order = abs(int(f.suffix))
    except TypeError:
        order = 9999
    return (order, f.rootname)


# these namedtuples will be used as the keys for the dict in ResourcesCatalog.resources
PlatformCategorySearch = namedtuple('PlatformSearch', 'category resource_type')
PlatformSearch = namedtuple('PlatformSearch', 'platform resource_type')
# game also includes the platform as there may be games with the same name in different platforms
GameSearch = namedtuple('PlatformSearch', 'platform game resource_type')
# for manuals and trailers we specify the resource type instead of getting it from the folder name
MANUAL_RESOURCE_TYPE = 'Manual'
TRAILER_RESOURCE_TYPE = 'Trailer'


class ResourcesCatalog:
    def __init__(self, images_dir, manuals_dir, trailers_dir):
        self.resources = defaultdict(list)
        self.fields = []
        return

        # loop folders with images, manuals and trailers
        # saving files in the self.resources dict using the namedtuples as keys
        # the files use a naming convention so we can later query them using
        # platform names, game names, etc.

        for f in find_files(images_dir, '*.*', as_file=True):
            if f.split_path[0] == 'Platform Categories' and len(f.split_path) >= 4:
                self.add_resource(
                        f,
                        PlatformCategorySearch(f.split_path[1], f.split_path[2]))
            elif f.split_path[0] == 'Platforms' and len(f.split_path) >= 4:
                self.add_resource(
                        f,
                        PlatformSearch(f.split_path[1], f.split_path[2]))
            elif len(f.split_path) >= 3:
                self.add_resource(
                        f,
                        GameSearch(f.split_path[0], f.rootname_nosuffix, f.split_path[1]))

        for f in find_files(manuals_dir, '*.*', as_file=True):
            if len(f.split_path) >= 2:
                self.add_resource(f,
                        GameSearch(f.split_path[0], f.rootname_nosuffix, MANUAL_RESOURCE_TYPE))

        for f in find_files(trailers_dir, '*.*', as_file=True):
            if len(f.split_path) >= 2:
                self.add_resource(f,
                        GameSearch(f.split_path[0], f.rootname_nosuffix, TRAILER_RESOURCE_TYPE))

    # this method will generate based on the passed gaame, platform or category,
    # the namedtuple(s) that could have been used when adding that file in __init__
    def get_keys(self, resource_type, platform=None, category=None, game=None):
        if game:
            # the resources for games can be named either with the game name or the rom file
            return [GameSearch(game.platform.name, game.name, resource_type),
                    GameSearch(game.platform.name, game.rom.rootname, resource_type)]
        elif platform:
            return [PlatformSearch(platform.name, resource_type)]
        elif category:
            return [PlatformCategorySearch(category.name, resource_type)]

    def search_resources(self, resource_type, **kwargs):
        result = []
        already_checked = set()
        possible_keys = self.get_keys(resource_type, **kwargs)
        for keys in possible_keys:
            if keys not in already_checked:
                already_checked.add(keys)
                result += self.resources.get(keys, [])
        result.sort(key=get_resource_order)
        return result

    def search_images(self, resource_type, **kwargs):
        return self.search_resources(resource_type, **kwargs)

    def search_manuals(self, **kwargs):
        return self.search_resources(MANUAL_RESOURCE_TYPE, **kwargs)

    def search_trailers(self, **kwargs):
        return self.search_resources(TRAILER_RESOURCE_TYPE, **kwargs)

    def add_resource(self, f, **keys):
        self.resources[keys].append(f)
