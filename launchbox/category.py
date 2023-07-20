import logging
import untangle
from hashlib import md5

logger = logging.getLogger(__name__)


class Category:
    def __init__(self, category_xml_node, resources_catalog):
        self.resources_catalog = resources_catalog
        self.name = category_xml_node.Name.cdata
        self.id = md5(self.name.encode()).hexdigest()
        self.notes = category_xml_node.Notes.cdata
        logger.debug('Successfully initialized the category %s', self.name)

    def search_images(self, image_type):
        return self.resources_catalog.search_images(image_type, category=self)


class CategoriesCatalog:
    def __init__(self, category_xml_file, resources_catalog):
        categories = {}
        category_xml = untangle.parse(category_xml_file)
        for category_xml_node in category_xml.LaunchBox.PlatformCategory:
            logger.debug('Read next category')
            category = Category(category_xml_node, resources_catalog)
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
