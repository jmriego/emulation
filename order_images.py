from __future__ import print_function
import wx
# from LaunchBox2AEL import generate_launchers, generate_platform_folders, generate_game_resources, generate_data, get_game_resources, FOLDER_RESOURCE_TYPES, LBDIR
from LaunchBox2AEL import LBDIR
from launchbox.catalog import LaunchBox
from files.file import File, rename_files
from ael import GAME_RESOURCE_TYPES
from collections import defaultdict
##

launchbox = LaunchBox(LBDIR)

duplicate_resources = defaultdict(lambda: defaultdict(list))
file_properties = {}
possible_platforms = set()
possible_resource_types = set()
possible_platforms.add('(Any)')
possible_platforms.add('(Recent)')
possible_resource_types.add('(Any)')

for folder in [folder for res_type in GAME_RESOURCE_TYPES.values() for folder in res_type]:
    for game in launchbox.games:
        filelist = [f.absolute for f in game.search_images(folder)]
        if len(filelist) > 1:
            duplicate_resources[(game.platform.name, folder)][game.name] = filelist
            possible_platforms.add(game.platform.name)
            possible_resource_types.add(folder)
        for f in filelist:
            file_properties[f] = (game.platform.name, folder, game.name)

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
    for order, file_path in enumerate(files):
        resource_file = File(file_path)
        new_filename = '{}-{:02d}.{}'.format(resource_file.rootname_nosuffix, order + 1, resource_file.extension)
        result.append(File([resource_file.dirname, new_filename]).absolute)
    return result
##
# move a specified resource file to give it more or less priority
# negative numbers increase priority by changing the file name:
#   eg. a-03.jpg would be renamed to a-02.jpg
def reprioritize_resource(resource, move=-1, delete=False):
    # TODO better exception if the resource does not exist
    try:
        platform_name, resource_type, game_name = file_properties[resource]
        old_list = duplicate_resources[(platform_name, resource_type)][game_name]
        if delete:
            new_list = old_list
            new_list.remove(resource)
            File(resource).delete()
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
    if chosen_platform == '(Recent)':
        recent_date_limit = min(sorted(g.date_modified for g in launchbox.games)[-26:])
        recent_games = [g.name for g in launchbox.games if g.date_modified >= recent_date_limit]

    if chosen_platform in ['(Any)', '(Recent)'] or chosen_resource_type == '(Any)':
        for platform_name, resource_type in duplicate_resources.keys():
            if chosen_platform in [platform_name, '(Any)', '(Recent)'] and chosen_resource_type in [resource_type, '(Any)']:
                try:
                    for game, resources in duplicate_resources[(platform_name, resource_type)].items():
                        if chosen_platform == '(Recent)' and game not in recent_games:
                            continue
                        result[(platform_name, resource_type, game)] = resources
                except:
                    pass
    else:
        for game, resources in duplicate_resources[(chosen_platform, chosen_resource_type)].items():
            result[(chosen_platform, chosen_resource_type, game)] = resources
    return result
##
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
            img = img.Scale(NewW, NewH)
            if highlight:
                border = 5
                rectangle = wx.EmptyImage(NewW + border*2, NewH + border*2)
                rectangle.Replace(0,0,0,0,255,0)
                rectangle.Paste(img, border, border)
                img = rectangle
        except:
            img = wx.EmptyImage(maxW, maxW)
    else:
        img = wx.EmptyImage(maxW, maxW)

    return img
##

class PreviewPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent=parent)

        # preferences
        self.PreviewMaxSize = 400
        self.PreviewGridSize = (3, 3)

        # elements
        self._preview_image = self.generate_static_bitmap(maxW=self.PreviewMaxSize, maxH=self.PreviewMaxSize)

        # add fixed elements to the grid
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self._preview_image, 0, wx.EXPAND)

        self.SetSizer(self.sizer)

    def generate_static_bitmap(self, path='', maxW=100, maxH=100, highlight=False):
        img = generate_image(path, maxW, maxH, highlight)
        img_ctrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))
        return img_ctrl

    def change_preview_image(self, path):
        self._preview_image.SetBitmap(wx.BitmapFromImage(generate_image(path, self.PreviewMaxSize, self.PreviewMaxSize)))


class ScrolledImagesGrid(wx.ScrolledWindow):
    def __init__(self, parent, handler):
        self.parent = parent
        self.handler = handler
        self.PhotoMaxSize = 100
        wx.ScrolledWindow.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        self._selected_file = None
        self._selected_row = None

        # elements
        self._gb = wx.GridBagSizer(vgap=0, hgap=3)

        # add fixed elements to the grid
        self._row_images = {}
        self.generate_grid_images()
        self.SetSizer(self._gb)
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.SetScrollRate(fontsz.x, fontsz.y)
        self.EnableScrolling(True,True)

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
        img_ctrl.Bind(wx.EVT_MOTION, lambda event: self.onMouseOver(event, path))
        img_ctrl.Bind(wx.EVT_LEFT_DOWN, lambda event: self.onMouseClick(event, path, row))
        return img_ctrl

    def replace_img_ctrl_path(self, img_ctrl, path, row, highlight=False):
        img_ctrl.SetBitmap(wx.BitmapFromImage(generate_image(path, maxW=self.PhotoMaxSize, maxH=self.PhotoMaxSize, highlight=highlight)))
        img_ctrl = self.generate_static_bitmap_events(img_ctrl, path, row)
        return img_ctrl

    def replace_row_images(self, row, files):
        try:
            existing_imgs = self._row_images[row]
        except:
            self._row_images[row] = []
            existing_imgs = []

        col = 0
        for img_ctrl, f in zip(existing_imgs, files):
            highlight = f == self._selected_file
            self.replace_img_ctrl_path(img_ctrl, f, row, highlight=highlight)
            col += 1

        for image_path in files[len(existing_imgs):]:
            highlight = image_path == self._selected_file
            img_ctrl = self.generate_static_bitmap(image_path, highlight=highlight)
            img_ctrl = self.generate_static_bitmap_events(img_ctrl, image_path, row)
            self._gb.Add(img_ctrl, (row, col), (1 ,1))
            self._row_images[row].append(img_ctrl)
            col += 1

        for img_ctrl in existing_imgs[len(files):]:
            del self._row_images[row][-1]
            img_ctrl.Destroy()

    def generate_grid_images(self):
        # loop to create images
        handler = self.handler
        row_number = 0
        for key, images_row in get_list_to_check(handler.chosen_platform, handler.chosen_resource_type).items():
            platform, resource_type, game = key
            col_number = 0
            self.replace_row_images(row_number, images_row)
            row_number += 1

        # it there were more, just delete them
        while row_number in self._row_images:
            self.replace_row_images(row_number, [])
            row_number += 1

        self.OnInnerSizeChanged()

    def get_current_img_ctrl(self):
        path = self._selected_file
        platform_name, resource_type, game_name = file_properties[path]
        images_row = duplicate_resources[(platform_name, resource_type)][game_name]
        pos = images_row.index(path)
        row_number = self._selected_row
        return self._row_images[row_number][pos]

    def OnInnerSizeChanged(self):
        w, h = self._gb.GetMinSize()
        self.SetVirtualSize((w, h))

    def onMouseOver(self, event, path):
        handler = self.handler
        if path != handler._preview_image_path:
            handler.SetStatusText(path)
            handler.change_preview_image(path)

    def onMouseClick(self, event, path, row_number):
        img_ctrl = event.GetEventObject()
        pos = self._gb.GetItemPosition(img_ctrl)
        # remove hightlight of current marked file
        if self._selected_file:
            self.replace_img_ctrl_path(
                    self.get_current_img_ctrl(),
                    self._selected_file,
                    self._selected_row,
                    highlight=False)

        self._selected_file = path
        self._selected_row = row_number
        platform_name, resource_type, game_name = file_properties[path]
        images_row = duplicate_resources[(platform_name, resource_type)][game_name]
        self.replace_row_images(row_number, images_row)
        self.OnInnerSizeChanged()


class TestFrame(wx.Frame):
    def __init__(self):
        # preferences
        wx.Frame.__init__(self, None, -1, 'Programmatic size change')
        self.PhotoMaxSize = 100
        self.PreviewMaxSize = 300
        self.chosen_platform = 'MS-DOS'
        self.chosen_resource_type = 'Screenshot - Gameplay'

        # elements
        self._combo_platforms = wx.Choice(self, choices=sorted(list(possible_platforms)))
        self._combo_platforms.SetSelection(0)
        self._combo_resource_types = wx.Choice(self, choices=sorted(list(possible_resource_types)))
        self._combo_resource_types.SetSelection(0)
        self._preview_image_path = None

        # add elements of the app
        self.splitter = wx.SplitterWindow(self)
        self.preview_img = PreviewPanel(self.splitter)
        self.preview_img.SetMaxSize((400, -1))
        self.grid_img = ScrolledImagesGrid(self.splitter, self)
        self.splitter.SplitVertically(self.preview_img, self.grid_img)
        self.splitter.SetMinimumPaneSize(300)
        szh = wx.BoxSizer(wx.HORIZONTAL)
        szv = wx.BoxSizer(wx.VERTICAL)
        szh.Add(self._combo_platforms, 1, wx.EXPAND)
        szh.Add(self._combo_resource_types, 1, wx.EXPAND)
        szv.Add(szh, 0, wx.EXPAND)
        szv.Add(self.splitter, 1, wx.EXPAND)

        # add event handlers
        self._combo_platforms.Bind(wx.EVT_CHOICE, self.onChoice)
        self._combo_resource_types.Bind(wx.EVT_CHOICE, self.onChoice)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashDrag)
        self.CreateStatusBar()
        self.SetStatusText("Welcome to wxPython!")

        # set up everything
        self.make_menu_bar()
        self.SetSizer(szv)

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
        export_item = file_menu.Append(-1, "&Export CSV found resources\tCtrl-S",
                "Export a list of games and the resources found for them")
        export_orphan_item = file_menu.Append(-1, "&Export CSV orphan resources",
                "Export a list of images for which we find no associated game")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT)

        # Make the menu bar and add the two menus to it. The '&' defines the mnemonic
        menuBar = wx.MenuBar()
        menuBar.Append(file_menu, "&File")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.move_left_current_file, move_left_item)
        self.Bind(wx.EVT_MENU, self.move_right_current_file, move_right_item)
        self.Bind(wx.EVT_MENU, self.delete_current_file, delete_item)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, export_item)
        self.Bind(wx.EVT_MENU, self.OnSaveOrphan, export_orphan_item)
        self.Bind(wx.EVT_MENU, self.onExit, exit_item)

    def change_preview_image(self, path):
        self._preview_image_path = path
        self.preview_img.change_preview_image(path)

    def change_current_file(self, move=-1, delete=False):
        if self.grid_img._selected_file is None:
            wx.MessageBox("Select a file first")
            return False
        else:
            path = self.grid_img._selected_file
            platform_name, resource_type, game_name = file_properties[path]
            row_number = self.grid_img._selected_row
            new_filename = reprioritize_resource(path, move=move, delete=delete)
            self.grid_img._selected_file = new_filename
            images_row = duplicate_resources[(platform_name, resource_type)][game_name]
            self.grid_img.replace_row_images(row_number, images_row)

    def move_left_current_file(self, event):
        self.change_current_file(move=-1, delete=False)

    def move_right_current_file(self, event):
        self.change_current_file(move=+1, delete=False)

    def delete_current_file(self, event):
        self.change_current_file(move=0, delete=True)

    def onSashDrag(self, event):
        self.splitter.UpdateSize()
        preview_pane_size = self.splitter.GetSashPosition() - 10
        preview_pane_size = self.splitter.GetWindow1().GetClientSize()[0]
        self.preview_img.PreviewMaxSize = preview_pane_size
        # force regenerating the preview image
        self.change_preview_image(self._preview_image_path)

    def OnSaveAs(self, event):
        with wx.FileDialog(self, "Save CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    self.PrintCSVFoundResources(file)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def OnSaveOrphan(self, event):
        with wx.FileDialog(self, "Save CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    self.PrintCSVMissingResources(file)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def PrintCSVLine(self, line, f):
        for field in line:
            # field = field.encode('utf-8')
            print(u'"{}",'.format(field), end='', file=f)
        print("", file=f)

    def PrintCSVFoundResources(self, f):
        header = ['platform', 'game'] + list(GAME_RESOURCE_TYPES.keys()) + ['s_manual', 's_trailer']
        self.PrintCSVLine(header, f)

        # generate lines with games and their number of resources found by type
        for game in launchbox.games:
            line = [game.platform.name, game.name]
            for resource_type, folders in GAME_RESOURCE_TYPES.items():
                found_images = []
                for folder in folders:
                    found_images += game.search_images(folder)
                line.append(str(len(found_images)))
            line.append(str(len(game.search_manuals())))
            line.append(str(len(game.search_trailers())))
            self.PrintCSVLine(line, f)

    def PrintCSVMissingResources(self, fcsv):
        resource_files = [f.absolute for resource in launchbox.resources.resources.values() for f in resource]
        image_types = list(set(key[-1] for key in launchbox.resources.resources.keys()))
        used_resources = []
        for folder in image_types:
            for game in launchbox.games:
                used_resources += [r.absolute for r in game.search_images(folder)]
            for platform in launchbox.platforms:
                used_resources += [r.absolute for r in platform.search_images(folder)]
            for category in launchbox.categories:
                used_resources += [r.absolute for r in category.search_images(folder)]
        orphan_resources = [f for f in resource_files if f not in used_resources]
        for line in orphan_resources:
            self.PrintCSVLine([line], fcsv)

    def onChoice(self, event):
        self.chosen_platform = self._combo_platforms.GetString(self._combo_platforms.GetSelection())
        self.chosen_resource_type = self._combo_resource_types.GetString(self._combo_resource_types.GetSelection())
        self._selected_file = None
        self.grid_img.generate_grid_images()

    def onExit(self, event):
        self.Close(True)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    wx.Log.EnableLogging(False)
    frm = TestFrame()
    frm.Show()
    app.MainLoop()
