import unicodedata
from files.file import File, find_files
from collections import defaultdict

BAD_CHARS_IN_FILENAME = ":/'"

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
                self.categories[category_name, image_type].append(f)
            elif f.split_path[0] == 'Platforms' and len(f.split_path) >= 4:
                platform_name = f.split_path[1]
                image_type = f.split_path[2]
                self.platforms[platform_name, image_type].append(f)
            elif len(f.split_path) >= 3:
                platform_name = f.split_path[0]
                image_type = f.split_path[1]
                game = f.rootname_nosuffix.lower()
                self.games[platform_name, game, image_type].append(f)

        # generate manuals
        self.manuals = defaultdict(list)
        manual_files = find_files(manuals_dir, '*.*', as_file=True)
        for f in manual_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix.lower()
                self.manuals[platform_name, game].append(f)

        # generate trailers
        self.trailers = defaultdict(list)
        trailer_files = find_files(trailers_dir, '*.*', as_file=True)
        for f in trailer_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix.lower()
                self.trailers[platform_name, game].append(f)


    def search_images(self, resource_type, platform=None, category=None, game=None, as_file=False):
        result = []
        if game:
            where = self.games
            possible_file_names = [game.name, game.path_file.rootname]
            platform_name = game.platform.name
            for rootname in possible_file_names:
                result += self.games[platform_name, rootname, resource_type]
            result.sort(key=get_resource_order)
        elif platform:
            where = self.platforms
            result = sorted(self.platforms[platform.name, resource_type])
        elif category:
            where = self.categories
            result = sorted(self.categories[category.name, resource_type])

        if as_file:
            return result
        else:
            if result is None:
                return []
            return [f.absolute for f in result]

    def search_manuals(self, game, as_file=False):
        result = (
                self.manuals[game.platform.name, clean_filename(game.name).lower()]
                + self.manuals[game.platform.name, clean_filename(game.path_file.rootname).lower()] )
        return result

    def search_trailers(self, game, as_file=False):
        result = (
                self.manuals[game.platform.name, clean_filename(game.name).lower()]
                + self.manuals[game.platform.name, clean_filename(game.path_file.rootname).lower()] )

        if as_file:
            return result
        else:
            return
