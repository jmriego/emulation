import os
from LaunchBox2AEL import generate_launchers, generate_platform_folders, generate_game_resources, LBDATADIR
from file_utils import absolute_path, extract_path_parts, rename_files, delete_file
##
launchers = generate_launchers(absolute_path([LBDATADIR, 'Platforms.xml'], mode='os'))
platform_folders = generate_platform_folders(absolute_path([LBDATADIR, 'Platforms.xml'], mode='os'))
duplicate_resources = {}
file_properties = {}
possible_platforms = set()
possible_resource_types = set()
possible_platforms.add('(Any)')
possible_resource_types.add('(Any)')
resource_to_platform_type = {}
for launcher, launcher_dict in launchers.iteritems():
    platform_name = launcher_dict['platform']
    game_resources_platform = generate_game_resources(platform_folders[platform_name])
    for game_name, resources in game_resources_platform.iteritems():
        for resource_type, filelist in resources.iteritems():
            if len(filelist) > 1:
                if not (platform_name, resource_type) in duplicate_resources:
                    duplicate_resources[(platform_name, resource_type)] = {}
                duplicate_resources[(platform_name, resource_type)][game_name] = filelist
                possible_platforms.add(platform_name)
                possible_resource_types.add(resource_type)
                for f in filelist:
                    file_properties[f] = (platform_name, resource_type, game_name)
possible_platforms = sorted(list(possible_platforms))
possible_resource_types = sorted(list(possible_resource_types))
##
def move_element_list(element, elements_list, move=-1):
    result = list(elements_list)
    element_pos = elements_list.index(element)
    new_pos = element_pos + move

    if new_pos < 0:
        new_pos = 0
    if new_pos > len(elements_list):
        new_pos = len(elements_list)

    result.insert(new_pos, result.pop(element_pos))
    return result
##
def regenerate_numbers_ordered_files(files):
    result = []
    for order, f in enumerate(files):
        file_parts = extract_path_parts(f)
        new_filename = '{}-{:02d}.{}'.format(file_parts['rootname_nosuffix'], order + 1, file_parts['extension'])
        result.append(absolute_path([file_parts['dirname'], new_filename], mode='os'))
    return result
##
# move a specified resource file to give it more or less priority
# negative numbers increase priority by changing the file name:
#   eg. a-03.jpg would be renamed to a-02.jpg
def reprioritize_resource(resource, move=-1, delete=False):
    #TODO better exception if the resource does not exist
    try:
        platform_name, resource_type, game_name = file_properties[resource]
        old_list = duplicate_resources[(platform_name, resource_type)][game_name]
        if delete:
            new_list = old_list
            new_list.remove(resource)
            delete_file(resource)
        else:
            new_list = move_element_list(resource, old_list, move=move)
            resource_pos = new_list.index(resource)
        new_list_renumbered = regenerate_numbers_ordered_files(new_list)
        duplicate_resources[(platform_name, resource_type)][game_name] = new_list_renumbered
        rename_files(new_list, new_list_renumbered)
        if delete:
            new_name_resource = None
        else:
            new_name_resource = new_list_renumbered[resource_pos]
        for f in new_list_renumbered:
            file_properties[f] = (platform_name, resource_type, game_name)
        return new_name_resource
    except:
        return resource
##
# return a list of all games and resources of the specified type and platform
# the result is a dictionary of dictionaries:
# outer_key = (platform_name, resource_type)
# inner_key = game
# values = list of files for the platform,resource,game combination
##
def get_list_to_check(chosen_platform, chosen_resource_type):
    result = {}
    if chosen_platform == '(Any)' or chosen_resource_type == '(Any)':
        for platform_name, resource_type in duplicate_resources.keys():
            if chosen_platform in [platform_name, '(Any)'] and chosen_resource_type in [resource_type, '(Any)']:
                try:
                    for game, resources in duplicate_resources[(platform_name, resource_type)].iteritems():
                        result[(platform_name, resource_type, game)] = resources
                except:
                    pass
    else:
        for game, resources in duplicate_resources[(chosen_platform, chosen_resource_type)].iteritems():
            result[(chosen_platform, chosen_resource_type, game)] = resources
    return result
##
import wx

def generate_image(path=None, maxW=None, maxH=None, highlight=False):
    if path:
        try:
            img = wx.Image(path, wx.BITMAP_TYPE_ANY)
            W = img.GetWidth()
            H = img.GetHeight()
            if W > H:
                NewW = maxW
                NewH = maxW * H / W
            else:
                NewH = maxW
                NewW = maxW * W / H
            img = img.Scale(NewW,NewH)
            if highlight:
                img = img.AdjustChannels(2.0, 2.0, 2.0)
        except:
            img = wx.EmptyImage(maxW,maxW)
    else:
        img = wx.EmptyImage(maxW,maxW)

    return img
##

class PreviewWindow(wx.ScrolledWindow):
    def __init__(self, parent):
        self.parent = parent
        wx.ScrolledWindow.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)

        # preferences
        self.PreviewMaxSize = 300
        self.PreviewGridSize = (3,3)

        # elements
        self._gb = wx.GridBagSizer(vgap=0, hgap=3)
        self._preview_image = self.generate_static_bitmap(maxW=self.PreviewMaxSize, maxH=self.PreviewMaxSize)

        # add fixed elements to the grid
        self._gb.Add(self._preview_image, (0,0), self.PreviewGridSize)

        self.SetSizer(self._gb)
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.SetScrollRate(fontsz.x, fontsz.y)
        self.EnableScrolling(True,True)

    def generate_static_bitmap(self, path='', maxW=100, maxH=100, highlight=False):
        img = generate_image(path, maxW, maxH, highlight)
        img_ctrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))
        return img_ctrl

    def OnInnerSizeChanged(self):
        w,h = self._gb.GetMinSize()
        self.SetVirtualSize((w,h))

class AScrolledWindow(wx.ScrolledWindow):
    def __init__(self, parent):
        self.parent = parent
        wx.ScrolledWindow.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)

        # preferences
        self.PhotoMaxSize = 100
        self.PreviewMaxSize = 300
        self.PreviewGridSize = (3,3)
        self._selected_file = None
        self._selected_row = None
        self.chosen_platform = 'MS-DOS'
        self.chosen_resource_type = 'Screenshot - Gameplay'

        # elements
        self._gb = wx.GridBagSizer(vgap=0, hgap=3)
        self._combo_platforms = wx.Choice(parent, choices=sorted(list(possible_platforms)))
        self._combo_resource_types = wx.Choice(parent, choices=sorted(list(possible_resource_types)))
        self._row_images = {}
        self._preview_image = self.generate_static_bitmap(maxW=self.PreviewMaxSize, maxH=self.PreviewMaxSize)
        self._preview_image_path = None

        # add fixed elements to the grid
        self._gb.Add(self._combo_platforms, (0,0), (1,1))
        self._gb.Add(self._combo_resource_types, (0,1), (1,1))
        self._gb.Add(self._preview_image, (1,0), self.PreviewGridSize)
        self._combo_platforms.Bind(wx.EVT_CHOICE, self.onChoice)
        self._combo_resource_types.Bind(wx.EVT_CHOICE, self.onChoice)
        self.parent.CreateStatusBar()
        self.parent.SetStatusText("Welcome to wxPython!")

        self.generate_grid_images()

        self.SetSizer(self._gb)
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.SetScrollRate(fontsz.x, fontsz.y)
        self.EnableScrolling(True,True)
        self.make_menu_bar()


    def generate_static_bitmap(self, path='', maxW=100, maxH=100, highlight=False):
        img = generate_image(path, maxW, maxH, highlight)
        img_ctrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))
        return img_ctrl

    def generate_static_bitmap_events(self, img_ctrl, path, row):
        try:
            img_ctrl.Unbind(wx.EVT_MOTION)
            img_ctrl.Unbind(wx.EVT_LEFT_DOWN)
        except:
            pass
        img_ctrl.Bind(wx.EVT_MOTION, lambda event:self.onMouseOver(event, path))
        img_ctrl.Bind(wx.EVT_LEFT_DOWN, lambda event:self.onMouseClick(event, path, row))
        return img_ctrl


    def replace_img_ctrl_path(self, img_ctrl, path, row, highlight=False):
        img_ctrl.SetBitmap(wx.BitmapFromImage(generate_image(path, maxW=self.PhotoMaxSize, maxH=self.PhotoMaxSize, highlight=highlight)))
        img_ctrl = self.generate_static_bitmap_events(img_ctrl, path, row)
        return img_ctrl

    def replace_row_images(self, row, col, files):
        try:
            existing_imgs = self._row_images[row]
        except:
            self._row_images[row] = []
            existing_imgs = []

        for img_ctrl, f in zip(existing_imgs, files):
            highlight = f == self._selected_file
            self.replace_img_ctrl_path(img_ctrl, f, row, highlight=highlight)
            col += 1

        for image_path in files[len(existing_imgs):]:
            highlight = image_path == self._selected_file
            img_ctrl = self.generate_static_bitmap(image_path, highlight=highlight)
            img_ctrl = self.generate_static_bitmap_events(img_ctrl, image_path, row)
            self._gb.Add(img_ctrl, (row,col), (1,1))
            self._row_images[row].append(img_ctrl)
            col += 1
        
        for img_ctrl in existing_imgs[len(files):]:
            del self._row_images[row][-1]
            img_ctrl.Destroy()


    def generate_grid_images(self):
        # loop to create images
        row_number = 1
        for key, images_row in get_list_to_check(self.chosen_platform, self.chosen_resource_type).iteritems():
            platform, resource_type, game = key
            col_number = self.PreviewGridSize[1]
            self.replace_row_images(row_number, col_number, images_row)
            row_number += 1

        # it there were more, just delete them
        while row_number in self._row_images:
            self.replace_row_images(row_number, col_number, [])
            row_number += 1

        self.OnInnerSizeChanged()


    def get_current_img_ctrl(self):
        path = self._selected_file
        platform_name, resource_type, game_name = file_properties[path]
        images_row = duplicate_resources[(platform_name, resource_type)][game_name]
        pos = images_row.index(path)
        row_number = self._selected_row
        return self._row_images[row_number][pos]

    def make_menu_bar(self):
        # Make a file menu with reprioritize and delete buttons
        file_menu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        move_left_item = file_menu.Append(-1, "&Move Left\tCtrl-F",
                "Prioritise this file. The first one of the row will be in AEL")
        move_right_item = file_menu.Append(-1, "&Move Right\tCtrl-B",
                "Lower priority this file. The first one of the row will be in AEL")
        file_menu.AppendSeparator()
        delete_item = file_menu.Append(-1, "&Delete selected file\tCtrl-D",
                "Delete the selected file from disk")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        # Make the menu bar and add the two menus to it. The '&' defines the mnemonic
        menuBar = wx.MenuBar()
        menuBar.Append(file_menu, "&File")

        # Give the menu bar to the frame
        self.parent.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.parent.Bind(wx.EVT_MENU, self.move_left_current_file, move_left_item)
        self.parent.Bind(wx.EVT_MENU, self.move_right_current_file, move_right_item)
        self.parent.Bind(wx.EVT_MENU, self.delete_current_file, delete_item)
        self.parent.Bind(wx.EVT_MENU, self.onExit, exit_item)

    def onChoice(self, event):
        self.chosen_platform = self._combo_platforms.GetString(self._combo_platforms.GetSelection())
        self.chosen_resource_type = self._combo_resource_types.GetString(self._combo_resource_types.GetSelection())
        self.generate_grid_images()
        self.OnInnerSizeChanged()

    def change_current_file(self, move=-1, delete=False):
        if self._selected_file is None:
            wx.MessageBox("Select a file first")
            return False
        else:
            path = self._selected_file
            platform_name, resource_type, game_name = file_properties[path]
            row_number = self._selected_row
            col_number = self.PreviewGridSize[1]
            new_filename = reprioritize_resource(path, move=move, delete=delete)
            self._selected_file = new_filename
            images_row = duplicate_resources[(platform_name, resource_type)][game_name]
            self.replace_row_images(row_number, col_number, images_row)

    def move_left_current_file(self, event):
        self.change_current_file(move=-1, delete=False)

    def move_right_current_file(self, event):
        self.change_current_file(move=+1, delete=False)

    def delete_current_file(self, event):
        self.change_current_file(move=0, delete=True)

    def OnInnerSizeChanged(self):
        w,h = self._gb.GetMinSize()
        self.SetVirtualSize((w,h))

    def onMouseOver(self, event, path):
        if path != self._preview_image_path:
            self.parent.SetStatusText(path)
            self._preview_image.SetBitmap(wx.BitmapFromImage(generate_image(path, self.PreviewMaxSize, self.PreviewMaxSize)))

    def onMouseClick(self, event, path, row_number):
        # remove hightlight of current marked file
        if self._selected_file:
            self.replace_img_ctrl_path(
                    self.get_current_img_ctrl(),
                    self._selected_file,
                    self._selected_row,
                    highlight=False)

        self._selected_file = path
        self._selected_row = row_number
        col_number = self.PreviewGridSize[1]
        platform_name, resource_type, game_name = file_properties[path]
        images_row = duplicate_resources[(platform_name, resource_type)][game_name]
        self.replace_row_images(row_number, col_number, images_row)

    def onExit(self, event):
        self.parent.Close(True)


class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Programmatic size change')
        sz = wx.BoxSizer(wx.VERTICAL)
        pa = AScrolledWindow(self)
        sz.Add(pa, 1, wx.EXPAND)
        self.SetSizer(sz)



if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    wx.Log.EnableLogging(False)
    frm = TestFrame()
    frm.Show()
    app.MainLoop()
