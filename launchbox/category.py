import untangle
from hashlib import md5

class Category:
    def __init__(self, category_xml_node):
        self.name = category_xml_node.Name.cdata
        self.id = md5(self.name.encode()).hexdigest()
        self.notes = category_xml_node.Notes.cdata


class CategoriesCatalog:
    def __init__(self, category_xml_file):
        categories = {}
        category_xml = untangle.parse(category_xml_file)
        for category_xml_node in category_xml.LaunchBox.PlatformCategory:
            category = Category(category_xml_node)
            categories[category.id] = category

        self.categories = categories

    def __iter__(self):
        return iter(self.categories.values())

    def __getitem__(self, key):
        return self.categories[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
