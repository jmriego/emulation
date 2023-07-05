import logging
import untangle

logger = logging.getLogger(__name__)


class Platform:
    def __init__(self, platform_xml_node, resources_catalog):
        self.resources_catalog = resources_catalog
        platform_name = get_attribute_cdata(platform_xml_node, 'Name')
        self.name = platform_name
        self.release_year = get_attribute_cdata(platform_xml_node, 'ReleaseDate')[:4]
        self.developer = get_attribute_cdata(platform_xml_node, 'Developer')
        self.notes = get_attribute_cdata(platform_xml_node, 'Notes')
        logger.debug('Successfully initialized platform %s', self.name)

    def search_images(self, image_type):
        return self.resources_catalog.search_images(image_type, platform=self)


class PlatformsCatalog:
    def __init__(self, platform_xml_file, platform_categories_xml_file, categories, resources_catalog):
        platforms = {}
        platform_xml = untangle.parse(platform_xml_file)
        for platform_xml_node in platform_xml.LaunchBox.Platform:
            logger.debug('Processing next platform')
            platform = Platform(platform_xml_node, resources_catalog)
            platforms[platform.name] = platform
        self.platforms = platforms

        # after we have created the dictionary of platforms, assign categories
        platform_categories_xml = untangle.parse(platform_categories_xml_file)
        for parent_xml in platform_categories_xml.LaunchBox.Parent:
            logger.debug('Processing next platform category')
            # some nodes in parents.xml file seem to have incomplete information. ignore them
            try:
                platform_name = getattr(parent_xml, 'PlatformName').cdata
            except AttributeError:
                logger.warn('This category mapping doesnt seem to include a platform')
                continue
            category_name = get_attribute_cdata(parent_xml, 'ParentPlatformCategoryName')
            self.platforms[platform_name].category = categories.search(category_name)
            logger.debug('Assigned platform %s to category %s', platform_name, category_name)

    def __iter__(self):
        return iter(self.platforms.values())

    def __getitem__(self, key):
        return self.platforms[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
