# Prefered directories for each image type
GAME_RESOURCE_TYPES = {
  's_banner': ['Banner', 'Steam Banner', 'Arcade - Marquee'],
  's_flyer': ['Advertisement Flyer - Front'],
  's_boxback': ['Box - Back'],
  's_boxfront': ['Box - Front', 'Box - Front - Reconstructed', 'Fanart - Box - Front', 'Steam Poster', 'GOG Poster', 'Amazon Poster', 'Epic Games Poster'],
  's_3dbox': ['Box - 3D'],
  's_cartridge': ['Cart - Front', 'Cart - 3D', 'Cart - Back'],
  's_clearlogo': ['Clear Logo'],
  's_fanart': ['Fanart - Background'],
  's_poster': ['Advertisement Flyer - Front', 'Advertisement Flyer - Back', 'Steam Poster', 'GOG Poster', 'Amazon Poster', 'Epic Games Poster'],
  's_snap': ['Screenshot - Gameplay'],
  's_title': ['Screenshot - Game Title'],
}

def get_first_path(files):
    try:
        return files[0].absolute
    except IndexError:
        return ''
