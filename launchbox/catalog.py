from files.file import File
import untangle
from launchbox.emulator import Emulator, EmulatorCatalog
from launchbox.category import Category, CategoriesCatalog

class LaunchBox:
    def __init__(self, lb_dir):
        # Directories inside LaunchBox
        self.base_dir = File(lb_dir).absolute
        self.data_dir = File([self.base_dir, "Data"]).absolute
        self.images_dir = File([self.base_dir, "Images"]).absolute
        self._emulators = None
        self._categories = None

    @property
    def emulators(self):
        if self._emulators is None:
            self._emulators = EmulatorCatalog(
                    File([self.data_dir, "Emulators.xml"]).absolute)
        return self._emulators

    @property
    def categories(self):
        if self._categories is None:
            self._categories = CategoriesCatalog(
                    File([self.data_dir, "Platforms.xml"]).absolute)
        return self._categories
