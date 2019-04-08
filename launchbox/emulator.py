import untangle


class Emulator:
    def __init__(self, emulator_xml_node, id=None, path=None, name=None):
        self.path = path if path else get_attribute_cdata(emulator_xml_node, 'ApplicationPath')
        self.id = id if id else get_attribute_cdata(emulator_xml_node, 'ID')
        self.name = name if name else get_attribute_cdata(emulator_xml_node, 'Title')
        command_line = get_attribute_cdata(emulator_xml_node, 'CommandLine')
        space = get_attribute_cdata(emulator_xml_node, 'NoSpace') != "true"
        quotes = get_attribute_cdata(emulator_xml_node, 'NoQuotes') != "true"
        self.args = (
                command_line
                + (' ' if space else '')
                + ('"{}"' if quotes else '{}')
                ).lstrip()


class EmulatorCatalog:
    def __init__(self, emulator_xml_file):
        emulators = {}
        emulator_xml = untangle.parse(emulator_xml_file)
        for emulator_xml_node in emulator_xml.LaunchBox.Emulator:
            emulator = Emulator(emulator_xml_node)
            emulators[emulator.id] = emulator

        emulators['Executables'] = Emulator(None, 'Executables', r'C:\Emulators\default_launcher.bat', 'Executables')
        self.emulators = emulators

    def __getitem__(self, key):
        return self.emulators[key]


def get_attribute_cdata(node, attribute, default=''):
    try:
        result = getattr(node, attribute).cdata
    except:
        result = default
    return result if result else default
