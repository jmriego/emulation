from hashlib import md5
from collections import OrderedDict

class Category(OrderedDict):
    def __init__(self, lb_category):
        super(Category, self).__init__((
            ('id', lb_category.id),
            ('m_name', lb_category.name),
            ('m_genre', lb_category.name),
            ('m_plot', lb_category.notes),
            ('m_rating', ""),
            ('finished', "False"),
            ('default_thumb', "s_icon"),
            ('default_fanart', "s_fanart"),
            ('default_banner', "s_banner"),
            ('default_poster', "s_poster"),
            # get the first file found or None
            ('s_icon', (lb_category.clear_logo_imgs + [None])[0]),
            ('s_fanart', (lb_category.fanart_imgs + [None])[0]),
            ('s_banner', (lb_category.banner_imgs + [None])[0]),
            ('s_poster', ""),
            ('s_clearlogo', (lb_category.clear_logo_imgs + [None])[0]),
            ('s_trailer', "")
        ))
