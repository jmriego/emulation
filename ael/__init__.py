# Prefered directories for each image type
GAME_RESOURCE_TYPES = {
  's_banner': ['Banner', 'Steam Banner', 'Arcade - Marquee'],
  's_flyer': ['Advertisement Flyer - Front'],
  's_boxback': ['Box - Back'],
  's_boxfront': ['Box - Front'],
  's_cartridge': ['Cart - Front', 'Cart - 3D', 'Cart - Back'],
  's_clearlogo': ['Clear Logo'],
  's_fanart': ['Fanart - Background'],
  's_poster': ['Advertisement Flyer - Front', 'Advertisement Flyer - Back'],
  's_snap': ['Screenshot - Gameplay'],
  's_title': ['Screenshot - Game Title'],
  's_manual': ['Manuals'],
  's_trailer': ['Videos']
}

def get_first_path(files):
    try:
        return files[0].absolute
    except IndexError:
        return None
