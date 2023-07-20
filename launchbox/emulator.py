import logging
import untangle
from files.file import File

logger = logging.getLogger(__name__)


class Emulator:
    def __init__(self, emulator_xml_node, base_dir, id=None, path=None, name=None):
        path = path if path else get_attribute_cdata(emulator_xml_node, 'ApplicationPath')
        self.path = File([base_dir, path])
        self.id = id if id else get_attribute_cdata(emulator_xml_node, 'ID')
        self.name = name if name else get_attribute_cdata(emulator_xml_node, 'Title')
        self.space = get_attribute_cdata(emulator_xml_node, 'NoSpace') != "true"
        self.quotes = get_attribute_cdata(emulator_xml_node, 'NoQuotes') != "true"
        self.args = {}
        command_line = get_attribute_cdata(emulator_xml_node, 'CommandLine')
        self.add_platform_parameters(platform='default', command_line=command_line)
        logger.debug('Successfully initialized emulator %s', self.name)

    def add_platform_parameters(self, emulatorplatform_xml_node=None, platform=None, command_line=None):
        if emulatorplatform_xml_node:
            platform = get_attribute_cdata(emulatorplatform_xml_node, 'Platform')
            command_line = get_attribute_cdata(emulatorplatform_xml_node, 'CommandLine')
            # if we are not overwriting the default command line, skip it
            if command_line == '':
                return

        args =  (
                command_line
                + (' ' if self.space else '')
                + ('"{}"' if self.quotes else '{}')
                ).lstrip()
        self.args[platform.lower()] = args
        logger.debug('Parameters for emulator %s platform %s are: %s', self.name, platform, args)

    def command_line(self, platform):
        return self.args.get(platform.lower(), self.args['default'])


class EmulatorCatalog:
    def __init__(self, emulator_xml_file, base_dir):
        emulators = {}
        emulator_xml = untangle.parse(emulator_xml_file)
        for emulator_xml_node in emulator_xml.LaunchBox.Emulator:
            logger.debug('Processing next emulator')
            emulator = Emulator(emulator_xml_node, base_dir)
            emulators[emulator.id] = emulator

        emulators['Executables'] = Emulator(None, base_dir, 'Executables', r'C:\Emulators\default_launcher.bat', 'Executables')

        for emulatorplatform_xml_node in getattr(emulator_xml.LaunchBox, 'EmulatorPlatform', []):
            logger.debug('Processing next emulator platform')
            emulator_id = get_attribute_cdata(emulatorplatform_xml_node, 'Emulator')
            emulators[emulator_id].add_platform_parameters(emulatorplatform_xml_node)
        self.emulators = emulators

    def __getitem__(self, key):
        return self.emulators[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
