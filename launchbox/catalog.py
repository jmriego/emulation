from files.file import File
import untangle
from launchbox.emulator import Emulator, EmulatorCatalog

class LaunchBox:
    def __init__(self, lb_dir):
        # Directories inside LaunchBox
        self.base_dir = File(lb_dir).absolute
        self.data_dir = File([self.base_dir, "Data"]).absolute
        self.images_dir = File([self.base_dir, "Images"]).absolute
        self.emulators = EmulatorCatalog(File([self.data_dir, "Emulators.xml"]).absolute)
