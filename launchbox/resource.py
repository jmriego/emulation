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
    return order


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
        self.categories = defaultdict(lambda:defaultdict(list))
        self.platforms = defaultdict(lambda:defaultdict(list))
        self.games = defaultdict(lambda:defaultdict(list))
        for f in image_files:
            if f.split_path[0] == 'Platform Categories' and len(f.split_path) >= 4:
                category_name = f.split_path[1]
                image_type = f.split_path[2]
                self.categories[category_name][image_type].append(f)
            elif f.split_path[0] == 'Platforms' and len(f.split_path) >= 4:
                platform_name = f.split_path[1]
                image_type = f.split_path[2]
                self.platforms[platform_name][image_type].append(f)
            elif len(f.split_path) >= 3:
                platform_name = f.split_path[0]
                image_type = f.split_path[1]
                game = f.rootname_nosuffix
                self.games[platform_name][image_type].append(f)

        # generate manuals
        manual_files = find_files(manuals_dir, '*.*', as_file=True)
        for f in manual_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix
                self.games[platform_name]['Manuals'].append(f)

        # generate trailers
        trailer_files = find_files(trailers_dir, '*.*', as_file=True)
        for f in trailer_files:
            if len(f.split_path) >= 2:
                platform_name = f.split_path[0]
                game = f.rootname_nosuffix
                self.games[platform_name]['Videos'].append(f)


    def search(self, resource_type, platform=None, category=None, game=None, as_file=False):
        try:
            platform_name = platform.name
        except AttributeError:
            platform_name = platform

        try:
            category_name = category.name
        except AttributeError:
            category_name = category

        try:
            game_names = [game.name, game.path_file.rootname]
            platform_name = game.platform.name
        except AttributeError:
            game_names = [game] if game else []

        result = []
        try:
            if game_names:
                for game_name in game_names:
                    for f in self.games[platform_name][resource_type]:
                        if clean_filename(f.rootname_nosuffix).lower() == clean_filename(game_name).lower():
                                result.append(f)
                result.sort(key=get_resource_order)
            elif platform_name:
                result = sorted(self.platforms[platform_name][resource_type])
            elif category_name:
                result = sorted(self.categories[category_name][resource_type])
        except KeyError:
            return []

        if as_file:
            return result
        else:
            if result is None:
                return []
            return [f.absolute for f in result]
