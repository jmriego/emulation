from collections import OrderedDict
from . import get_first_path


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
            ('s_icon', (
                get_first_path(lb_category.search_images('Device'))
                or get_first_path(lb_category.search_images('Clear Logo'))
                )),
            ('s_fanart', get_first_path(lb_category.search_images('Fanart'))),
            ('s_banner', get_first_path(lb_category.search_images('Banner'))),
            ('s_poster', ""),
            ('s_clearlogo', get_first_path(lb_category.search_images('Clear Logo'))),
            ('s_trailer', "")
        ))
