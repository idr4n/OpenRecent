import os
import re
import sublime
import sublime_plugin

SETTINGS_FILE = 'OpenRecent.sublime-settings'
OS = sublime.platform()

settings = {}
prefs = {}


def plugin_loaded():
    global settings, prefs
    settings = sublime.load_settings(SETTINGS_FILE)
    prefs = Pref()


class Pref():
    def __init__(self):
        self.session_file = 'Session.sublime_session'
        self.auto_session_file = 'Auto Save Session.sublime_session'

    def get_session_path(self):
        """
        Returns the folder where Sublime's session is stored in the system.
        """
        package_path = sublime.packages_path()
        session_folder = os.path.join(os.path.dirname(package_path), 'Local')

        if settings.get('session_folder'):
            session_folder = os.path.expanduser(settings.get('session_folder'))

        ses_path = os.path.join(session_folder, self.session_file)
        auto_ses_path = os.path.join(session_folder, self.auto_session_file)

        if os.path.exists(auto_ses_path):
            # print('Auto session exists: ', auto_ses_path)
            return auto_ses_path

        return ses_path


class Conf():
    def __init__(self, type='folders'):
        self.type = type
        self.items = []
        self.items_count = 0
        self.display_list = []
        self.cache = {'last_selection': '', 'last_index': 0}

    def load_items_data(self):
        """
        Loads the list of folders to be shown in the quick panel
        """
        fpath = prefs.get_session_path()
        # print(fpath)

        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as f:
                try:
                    session_json = sublime.decode_value(f.read())
                    # self.items = session_json['folder_history']
                    self.items = self.get_session_data(session_json)
                    self.items_count = len(self.items)
                except Exception as Inst:
                    print('OpenRecent Exception:', Inst)
                    sublime.message_dialog(
                        'Could not load JSON data from {}'.format(fpath))
        else:
            sublime.message_dialog(
                "Path '{}' does not exist".format(fpath))

    def get_session_data(self, object):
        data = []
        if self.type == 'folders':
            data = object['folder_history']
        if self.type == 'files':
            data = object['settings']['new_window_settings']['file_history']

        if OS == 'windows':
            data = list(map(self.windofy_path, data))

        return data

    def get_last_index(self):
        """
        Returns the index of the last selected item.
        """
        try:
            return self.items.index(self.cache['last_selection'])
        except Exception:
            # print('Open Recent: No previous selection found')
            return 0

    def update_cache(self, **kwargs):
        for key, value in kwargs.items():
            self.cache[key] = value

        self.cache['last_index'] = self.get_last_index()

    def set_display_list(self):
        """
        Sets the display list to be shown in the Quick Panel

        The first row of each item has the last component of the path, while
        the second row has the rest (first part) of the path
        """
        if self.items_count == 0:
            sublime.message_dialog('There are no items in history yet!')
            return

        prittified_items = list(map(self.prettify_path, self.items))
        if settings.get('display_two_lines'):
            self.display_list = [[os.path.basename(f), os.path.dirname(f)]
                                 for f in prittified_items]
        else:
            self.display_list = prittified_items

    @staticmethod
    def prettify_path(path: str):
        user_home = os.path.expanduser('~') + os.sep
        if path.startswith(os.path.expanduser('~')):
            return os.path.join('~', path[len(user_home):])
        return path

    @staticmethod
    def windofy_path(path: str):
        if re.match(r'^/[A-Z]/', path):
            return os.path.abspath(path[2:])
        else:
            return os.path.normpath(path)

# ------------------------------------------------------------
# TODO: keep track of folders and file history
# Need to add listeners to keep track of changes in project_data

# class FolderListener(sublime_plugin.ViewEventListener):
#     def on_load(self):
#         print('--View activated')
#         sublime.active_window().run_command('save_folder')

# class FolderListener(sublime_plugin.EventListener):
#     def on_new_window_async(self, window):
#         print('--New window opened')
#         window.run_command('save_folder')


# class SaveFolderCommand(sublime_plugin.WindowCommand):
#     def run(self):
#         folder = self.window.folders()
#         if folder:
#             print("Folder name:", folder)
#         else:
#             print('No folder in window')

# ------------------------------------------------------------

class OpenFolderHistoryCommand(sublime_plugin.WindowCommand):
    conf = Conf('folders')

    def get_window(self):
        """
        Returns the window in which the new data will be loaded.

        A new window if the active window is not empty, otherwise
        returns the active window
        """
        curwin = sublime.active_window()
        if not curwin.folders() and not curwin.views():
            return curwin

        self.window.run_command('new_window')
        return sublime.active_window()

    def open_folder(self, index):
        """
        Opens the selected folder in the active window

        :param  index:  The index of the folder in the quick panel list
        """
        if index >= 0:
            folder = self.conf.items[index]
            self.conf.update_cache(last_selection=folder)
            if os.path.isdir(os.path.expanduser(folder)):
                new_win = self.get_window()
                new_data = {'folders': [{'path': folder}]}
                new_win.set_project_data(new_data)
                new_win.set_sidebar_visible(True)

    def run(self):
        self.conf.load_items_data()
        self.conf.set_display_list()
        placeholder = "Open Recent folder (out of {})".format(
            self.conf.items_count)
        if len(self.conf.display_list) > 0:
            self.window.show_quick_panel(
                self.conf.display_list,
                self.open_folder,
                placeholder=placeholder,
                selected_index=self.conf.cache['last_index'])
        else:
            self.window.show_quick_panel(["No history found"], None)


class OpenFileHistoryCommand(sublime_plugin.WindowCommand):
    conf = Conf('files')

    def get_window(self):
        """
        Returns the window in which the file will be opened.
        """
        curwin = sublime.active_window()

        if settings.get('open_in_new_window'):
            if not curwin.folders() and not curwin.views():
                return curwin
            else:
                self.window.run_command('new_window')
                return sublime.active_window()

        return curwin

    def is_transient(self, view):
        opened_views = self.window.views()
        if view in opened_views:
            return False

        return True

    def show_preview(self, index):
        if index >= 0 and settings.get('show_file_preview'):
            file = self.conf.items[index]
            if os.path.isfile(os.path.expanduser(file)):
                self.window.open_file(file, sublime.TRANSIENT)

    def open_file(self, index):
        """
        Opens the selected folder in the active window

        :param  index:  The index of the file in the quick panel list
        """
        active_view = self.window.active_view()
        if index >= 0:
            if self.is_transient(active_view):
                active_view.close()
            file = self.conf.items[index]
            self.conf.update_cache(last_selection=file)
            if os.path.isfile(os.path.expanduser(file)):
                new_win = self.get_window()
                new_win.set_sidebar_visible(True)
                new_win.open_file(file)

        else:
            if self.is_transient(active_view):
                active_view.close()

    def run(self):
        self.conf.load_items_data()
        self.conf.set_display_list()
        placeholder = "Open Recent file (out of {})".format(
            self.conf.items_count)
        if len(self.conf.display_list) > 0:
            self.window.show_quick_panel(
                self.conf.display_list,
                self.open_file, placeholder=placeholder,
                selected_index=self.conf.cache['last_index'],
                on_highlight=self.show_preview)
        else:
            self.window.show_quick_panel(["No history found"], None)


class ViewSettings():
    def __init__(self, view) -> None:
        self.view = view
        self.settings = self._saveSettings()

    def _bookmarks(self):
        return self.view.get_regions('bookmarks')

    def _selections(self):
        return [region for region in self.view.sel()]

    def _saveSettings(self):
        return {
            'bookmarks': self._bookmarks(),
            'selections': self._selections(),
            'viewport': self.view.viewport_position()
        }

    def copyTo(self, other_view):
        if other_view.is_loading():
            sublime.set_timeout(lambda: self.copyTo(other_view), 0)
        else:
            # Bookmarks
            other_view.add_regions(
                'bookmarks',
                self.settings['bookmarks'],
                'bookmarks', 'bookmark',
                sublime.HIDDEN | sublime.PERSISTENT)

            # Selections
            other_view.sel().clear()
            for region in self.settings['selections']:
                other_view.sel().add(region)

            # Scroll the viewport to given layout position
            other_view.set_viewport_position(self.settings['viewport'])


class MoveToNewWindowCommand(sublime_plugin.WindowCommand):
    def run(self):
        tab = self.window.active_view()
        tab_settings = ViewSettings(tab)
        file = tab.file_name()
        if tab.is_dirty() or tab.is_scratch():
            sublime.message_dialog('You need to save your changes first!')
            return
        tab.close()
        self.window.run_command('new_window')
        new_win = sublime.active_window()
        new_win.set_sidebar_visible(True)
        new_view = new_win.open_file(file)
        tab_settings.copyTo(new_view)


class MoveToWindowCommand(sublime_plugin.WindowCommand):
    wins_list = []
    display_list = []

    @staticmethod
    def get_file_name(path):
        return os.path.basename(path)

    def clear_lists(self):
        self.wins_list = []
        self.display_list = []

    @staticmethod
    def win_is_empty(win):
        if len(win.views()) == 0:
            return True
        return False

    def set_wins(self):
        self.wins_list = sublime.windows()
        for win in self.wins_list:
            win_files = []
            views = win.views()
            for view in views:
                win_files.append(self.get_file_name(view.file_name()))

            if win_files:
                display_item = []
                display_item.append(win_files[0])
                display_item.append(" | ".join(win_files))
                self.display_list.append(display_item)
            else:
                self.display_list.append(['Empty Window', '--'])

    def on_open(self, index):
        tab = self.window.active_view()
        tab_settings = ViewSettings(tab)
        if tab.is_dirty() or tab.is_scratch():
            sublime.message_dialog('You need to save your changes first!')
            return
        if index >= 0:
            current_win = sublime.active_window()
            selected_win = self.wins_list[index]
            if current_win != selected_win:
                file = tab.file_name()
                tab.close()
                selected_win.set_sidebar_visible(True)
                new_view = selected_win.open_file(file)
                tab_settings.copyTo(new_view)

                selected_win.bring_to_front()

            if self.win_is_empty(current_win):
                current_win.run_command('close_window')

    def run(self):
        self.clear_lists()
        self.set_wins()
        placeholder = 'Select window (out of {})'.format(len(self.wins_list))
        self.window.show_quick_panel(
            self.display_list,
            self.on_open, placeholder=placeholder)
