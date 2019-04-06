import untangle
from hashlib import md5
from files.file import find_files

class Category:
    def __init__(self, category_xml_node, images_dir):
        self.name = category_xml_node.Name.cdata
        self.id = md5(self.name.encode()).hexdigest()
        self.notes = category_xml_node.Notes.cdata
        self.clear_logo_imgs = find_files([images_dir, 'Platform Categories', self.name, 'Clear Logo'], '*.*')
        self.fanart_imgs = find_files([images_dir, 'Platform Categories', self.name, 'Fanart'], '*.*')
        self.banner_imgs = find_files([images_dir, 'Platform Categories', self.name, 'Banner'], '*.*')


class CategoriesCatalog:
    def __init__(self, category_xml_file, images_dir):
        categories = {}
        category_xml = untangle.parse(category_xml_file)
        for category_xml_node in category_xml.LaunchBox.PlatformCategory:
            category = Category(category_xml_node, images_dir)
            categories[category.id] = category

        self.categories = categories

    def __iter__(self):
        return iter(self.categories.values())

    def __getitem__(self, key):
        return self.categories[key]

    def search(self, name):
        for category in self:
            if category.name == name:
                return category


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
