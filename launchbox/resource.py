import unicodedata
from files.file import find_files
from collections import defaultdict
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


def insert_ordered(resources_list, f):
    lo = 0
    hi = len(resources_list)
    while lo < hi:
        mid = (lo+hi)//2
        if get_resource_order(f) < get_resource_order(resources_list[mid]):
            hi = mid
        else:
            lo = mid+1
    resources_list.insert(lo, f)


class ResourcesCatalog:
    def __init__(self, images_dir, manuals_dir, trailers_dir):
        self.images_dir = images_dir
        self.manuals_dir = manuals_dir
        self.trailers_dir = trailers_dir

        # generate images
        image_files = find_files(images_dir, '*.*', as_file=True)

        # nested dictionaries. The internal level defaults to an empty list
        # categories = {category_name{image_type}}
        # platforms = {platform_name{image_type}}
        # games = {platform_name{resource_type}}
        self.categories = defaultdict(list)
        self.platforms = defaultdict(list)
        self.games = defaultdict(list)
        for f in image_files:
            if f.split_path[0] == 'Platform Categories' and len(f.split_path) >= 4:
                category_name = f.split_path[1]
                image_type = f.split_path[2]
                insert_ordered(self.categories[category_name, image_type], f)
            elif f.split_path[0] == 'Platforms' and len(f.split_path) >= 4:
                platform_name = f.split_path[1]
                image_type = f.split_path[2]
                insert_ordered(self.platforms[platform_name, image_type], f)
            elif len(f.split_path) >= 3:
                platform_name = f.split_path[0]
                image_type = f.split_path[1]
                game = f.rootname_nosuffix.lower()
                insert_ordered(self.games[platform_name, game, image_type], f)

        # generate manuals
        self.manuals = defaultdict(list)
        manual_files = find_files(manuals_dir, '*.*', as_file=True)
        for f in manual_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix.lower()
                insert_ordered(self.manuals[platform_name, game], f)

        # generate trailers
        self.trailers = defaultdict(list)
        trailer_files = find_files(trailers_dir, '*.*', as_file=True)
        for f in trailer_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix.lower()
                insert_ordered(self.trailers[platform_name, game], f)

    def search_images(self, resource_type, platform=None, category=None, game=None, as_file=False):
        if game:
            result = []
            possible_file_names = [game.name, game.rom.rootname]
            platform_name = game.platform.name
            for rootname in possible_file_names:
                clean_rootname = clean_filename(rootname).lower()
                result += self.games.get((platform_name, clean_rootname, resource_type), [])
            result.sort(key=get_resource_order)
            return result
        elif platform:
            return self.platforms.get((platform.name, resource_type), [])
        elif category:
            return self.categories.get((category.name, resource_type), [])

    def search_manuals(self, game):
        result = []
        possible_file_names = [game.name, game.rom.rootname]
        platform_name = game.platform.name
        for rootname in possible_file_names:
            clean_rootname = clean_filename(rootname).lower()
            result += self.manuals.get((platform_name, clean_rootname), [])
        result.sort(key=get_resource_order)
        return result

    def search_trailers(self, game):
        result = []
        possible_file_names = [game.name, game.rom.rootname]
        platform_name = game.platform.name
        for rootname in possible_file_names:
            clean_rootname = clean_filename(rootname).lower()
            result += self.trailers.get((platform_name, clean_rootname), [])
        result.sort(key=get_resource_order)
        return result
