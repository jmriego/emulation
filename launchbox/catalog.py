from files.file import File
import untangle
from launchbox.emulator import Emulator, EmulatorCatalog
from launchbox.category import Category, CategoriesCatalog
from launchbox.platform import Platform, PlatformsCatalog
from launchbox.game import Game, GamesCatalog
from launchbox.resource import ResourcesCatalog

class LaunchBox:
    def __init__(self, lb_dir):
        # Directories inside LaunchBox
        self.base_dir = File(lb_dir).absolute
        self.data_dir = File([self.base_dir, "Data"]).absolute
        self.images_dir = File([self.base_dir, "Images"]).absolute
        self.manuals_dir = File([self.base_dir, "Manuals"]).absolute
        self.trailers_dir = File([self.base_dir, "Videos"]).absolute
        self._emulators = None
        self._categories = None
        self._platforms = None
        self._games = None
        self._resources = None

    @property
    def emulators(self):
        if self._emulators is None:
            self._emulators = EmulatorCatalog(
                    File([self.data_dir, "Emulators.xml"]).absolute)
        return self._emulators

    @property
    def categories(self):
        if self._categories is None:
            # platforms.xml has the categories inside
            self._categories = CategoriesCatalog(
                    File([self.data_dir, "Platforms.xml"]).absolute,
                    self.resources)
        return self._categories

    @property
    def platforms(self):
        if self._platforms is None:
            # platforms.xml has the categories inside
            # parents.xml has the relationships between platforms and categories
            self._platforms = PlatformsCatalog(
                    File([self.data_dir, "Platforms.xml"]).absolute,
                    File([self.data_dir, "Parents.xml"]).absolute,
                    self.categories,
                    self.resources)
        return self._platforms

    @property
    def games(self):
        if self._games is None:
            # the games are inside the Platforms folder
            # one .xml file per platform with the games inside
            self._games = GamesCatalog(
                    File([self.data_dir, "Platforms"]).absolute,
                    self.platforms,
                    self.emulators,
                    self.base_dir,
                    self.resources)
        return self._games

    @property
    def resources(self):
        if self._resources is None:
            self._resources = ResourcesCatalog(
                    self.images_dir,
                    self.manuals_dir,
                    self.trailers_dir)
        return self._resources
