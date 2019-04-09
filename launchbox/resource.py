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


class ResourcesCatalog:
    def __init__(self, images_dir, manuals_dir, trailers_dir):
        self.resources = defaultdict(list)
        self.fields = []
        return

    # save images
        for f in find_files(images_dir, '*.*', as_file=True):
            if f.split_path[0] == 'Platform Categories' and len(f.split_path) >= 4:
                self.add_resource(
                        f,
                        category=f.split_path[1],
                        resource_type=f.split_path[2])
            elif f.split_path[0] == 'Platforms' and len(f.split_path) >= 4:
                self.add_resource(
                        f,
                        platform=f.split_path[1],
                        resource_type=f.split_path[2])
            elif len(f.split_path) >= 3:
                self.add_resource(
                        f,
                        platform=f.split_path[0],
                        game=f.rootname_nosuffix,
                        resource_type=f.split_path[1])

        # save manuals
        for f in find_files(manuals_dir, '*.*', as_file=True):
            if len(f.split_path) >= 2:
                self.add_resource(f,
                    platform=f.split_path[0],
                    game=f.rootname_nosuffix,
                    resource_type='Manual')

        # save trailers
        for f in find_files(trailers_dir, '*.*', as_file=True):
            if len(f.split_path) >= 2:
                self.add_resource(f,
                    platform=f.split_path[0],
                    game=f.rootname_nosuffix,
                    resource_type='Trailer')

    def get_keys(self, resource_type, platform=None, category=None, game=None):
        if game:
            return [{'platform': game.platform.name, 'game': game.name, 'resource_type': resource_type},
                    {'platform': game.platform.name, 'game': game.rom.rootname, 'resource_type': resource_type}]
        elif platform:
            return [{'platform': platform.name, 'resource_type': resource_type}]
        elif category:
            return [{'category': category.name, 'resource_type': resource_type}]

    def search_resources(self, resource_type, **kwargs):
        possible_keys = self.get_keys(resource_type, **kwargs)
        result = self.search(keys)

    def search_images(self, resource_type, **kwargs):
        return self.search_resources(resource_type, **kwargs)

    def search_manuals(self, **kwargs):
        return self.search_resources('Manual', **kwargs)

    def search_trailers(self, **kwargs):
        return self.search_resources('Trailer', **kwargs)

    def keys_to_tuple(self, **kwargs):
        tuple_as_dict = {}
        for key, value in kwargs.items():
            try:
                index = self.fields.index(key)
            except ValueError:
                self.fields.append(key)
                index = len(self.fields) - 1
            tuple_as_dict[index] = clean_filename(value).lower()
        return tuple(tuple_as_dict.get(i, '') for i in range(max(tuple_as_dict.keys())+1))

    def add_resource(self, f, **keys):
        keys = self.keys_to_tuple(keys)
        self.resources[keys].append(f)

    def search(self, possible_keys):
        result = []
        already_checked = set()
        for keys in possible_keys:
            keys = self.keys_to_tuple(keys)
            if keys not in already_checked:
                already_checked.add(keys)
                result += self.resources.get(keys, [])
        result.sort(key=get_resource_order)
        return result
