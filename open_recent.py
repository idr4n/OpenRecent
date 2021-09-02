import os
import re
import sublime
import sublime_plugin

DEBUG_ON = True
SETTINGS_FILE = 'OpenRecent.sublime-settings'
OS = sublime.platform()

RECENT_FOLDERS = 'OpenRecent_recent_folders.json'
FOLDERS_INFO = 'OpenRecent_folders_info.json'

settings = {}
prefs_subl_history = {}
folders_hist = []
folders_info = {}


def debug(var, message=''):
    if DEBUG_ON:
        if var:
            print('OpenRecent Debug - %s: %s' % (message, var))
        else:
            print('OpenRecent Debug: %s' % message)


def plugin_loaded():
    global settings, prefs_subl_history
    settings = sublime.load_settings(SETTINGS_FILE)
    prefs_subl_history = PrefSublHist()
    load_history_files()


def load_history_files():
    global folders_hist, folders_info
    recent_folders = os.path.join(
        sublime.packages_path(), 'User', RECENT_FOLDERS)
    recent_folders_info = os.path.join(
        sublime.packages_path(), 'User', FOLDERS_INFO)

    folders_hist = get_data(recent_folders, [])
    folders_info = get_data(recent_folders_info, {})


def get_data(path: str, default=[]):
    data = default
    if os.path.exists(path):
        with open(path, 'r', encoding="utf-8") as f:
            try:
                data = sublime.decode_value(f.read())
            except Exception as Inst:
                debug(Inst, 'OpenRecent Exception')
                sublime.message_dialog(
                    'Could not load JSON data from %s' % path)

            if not data:
                data = default
    else:
        with open(path, 'w', encoding="utf-8") as f:
            debug(path, 'creating file')
            data = default
            f.write(sublime.encode_value(data, True))

    return data


def prettify_path(path: str):
    user_home = os.path.expanduser('~') + os.sep
    if path.startswith(os.path.expanduser('~')):
        return os.path.join('~', path[len(user_home):])
    return path


def set_folders_list(str_list):
    """Prettifies paths and return list in reversed order"""
    return list(map(prettify_path, str_list[::-1]))


def display_list(str_list):
    """Displays list in one or two lines"""
    if settings.get('display_two_lines'):
        return [[os.path.basename(f), os.path.dirname(f)]
                for f in str_list]
    else:
        return str_list


class FoldersListener(sublime_plugin.ViewEventListener):
    def on_load_async(self):
        self._append_folders()

    def on_activated_async(self):
        self._update_folders_info()

    def _update_folders_info(self):
        window = self.view.window()
        if not window:
            return
        views = window.views()

        for folder in window.folders():
            opened_files_in_folder = []
            folder = prettify_path(folder)
            folder_info = folders_info.get(folder, {})
            if views:
                for view in views:
                    file_name = prettify_path(view.file_name())
                    if file_name.startswith(folder):
                        opened_files_in_folder.append(file_name)

                folder_info['opened_files'] = opened_files_in_folder
            else:
                folder_info['opened_files'] = []

            folders_info[folder] = folder_info

    def _append_folders(self):
        window = self.view.window()
        win_folders = window.folders()

        if win_folders:
            for folder in win_folders:
                folder = prettify_path(folder)
                if folder in folders_hist:
                    folders_hist.remove(folder)

                folders_hist.append(folder)


class PreCloseWinListener(sublime_plugin.EventListener):
    def on_pre_close_window(self, window):
        self._save_folders()
        self._save_folders_info()

    def _save_folders(self):
        folders_data = sublime.encode_value(folders_hist, True)
        recent_folders = os.path.join(
            sublime.packages_path(), 'User', RECENT_FOLDERS)
        with open(recent_folders, 'w', encoding="utf-8") as f:
            f.write(folders_data)

    def _save_folders_info(self):
        folders_info_data = sublime.encode_value(folders_info, True)
        recent_folders_info = os.path.join(
            sublime.packages_path(), 'User', FOLDERS_INFO)
        with open(recent_folders_info, 'w', encoding="utf-8") as f:
            f.write(folders_info_data)


class OpenRecentFolderCommand(sublime_plugin.WindowCommand):
    def __init__(self, window) -> None:
        super().__init__(window)
        self.folders = []

    def get_window(self, folder, add_to: bool):
        curwin = sublime.active_window()
        for window in sublime.windows():
            if os.path.expanduser(folder) in window.folders() and not add_to:
                return window, True
        if (not curwin.folders() and not curwin.views()) or add_to:
            return curwin, False

        self.window.run_command('new_window')
        return sublime.active_window(), False

    def on_selected(self, index, add_to: bool):
        if index >= 0:
            folder = self.folders[index]
            if os.path.isdir(os.path.expanduser(folder)):
                new_win, other_win_exists = self.get_window(folder, add_to)
                if other_win_exists:
                    new_win.bring_to_front()
                    return
                if self.window.project_data() and add_to:
                    win_folders = self.window.project_data().get('folders', [])
                else:
                    win_folders = []

                win_folders.append({'path': folder})
                new_data = {'folders': win_folders}
                new_win.set_project_data(new_data)
                new_win.set_sidebar_visible(True)
                self.open_folder_files(folder, new_win)

    def open_folder_files(self, folder, window):
        folder_info = folders_info.get(folder, {})
        opened_files = folder_info.get('opened_files', [])
        if opened_files:
            for file in folder_info['opened_files']:
                file = os.path.expanduser(file)
                if os.path.exists(file):
                    window.open_file(file)

    def run(self, add_to_project=False):
        self.folders = set_folders_list(folders_hist)
        placeholder = "Open Recent Folders (out of %s)" % len(self.folders)
        if len(self.folders) > 0:
            self.window.show_quick_panel(
                display_list(self.folders),
                on_select=lambda idx: self.on_selected(idx, add_to_project),
                placeholder=placeholder)
        else:
            self.window.show_quick_panel(["No history found"], None)


class RemoveRecentFolderCommand(sublime_plugin.WindowCommand):
    def on_selected(self, index):
        if index >= 0:
            folder = self.folders[index]
            for window in sublime.windows():
                if os.path.expanduser(folder) in window.folders():
                    msg = """First close the window with the folder
                    you want to remove."""
                    sublime.message_dialog(msg)
                    return
            validator = sublime.ok_cancel_dialog(
                'Remove "%s" from history?' % folder)
            if validator:
                msg = """The folder will be completely removed after closing
                a window or Sublime Text"""
                sublime.message_dialog(msg)
                folders_hist.remove(folder)
                folders_info.pop(folder, None)

    def run(self):
        self.folders = set_folders_list(folders_hist)
        placeholder = "Delete folder out of recent history"
        if len(self.folders) > 0:
            self.window.show_quick_panel(
                display_list(self.folders),
                on_select=lambda idx: self.on_selected(idx),
                placeholder=placeholder)
        else:
            self.window.show_quick_panel(["No history found"], None)


class PrefSublHist():
    """Set preferences for using Sublime history files"""

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


class ConfSublHist():
    """Set configuration for using Sublime history files"""

    def __init__(self, type='own_folders'):
        self.type = type
        self.items = []
        self.items_count = 0
        self.display_list = []
        self.cache = {'last_selection': '', 'last_index': 0}

    def load_items_data(self):
        """
        Loads the list of folders to be shown in the quick panel
        """

        fpath = prefs_subl_history.get_session_path()

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
        """Returns the index of the last selected item."""
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
        if self.items_count == 0:
            sublime.message_dialog('There are no items in history yet!')
            return

        prittified_items = list(map(prettify_path, self.items))
        if settings.get('display_two_lines'):
            self.display_list = [[os.path.basename(f), os.path.dirname(f)]
                                 for f in prittified_items]
        else:
            self.display_list = prittified_items

    @staticmethod
    def windofy_path(path: str):
        if re.match(r'^/[A-Z]/', path):
            return os.path.abspath(path[2:])
        else:
            return os.path.normpath(path)


class OpenFolderHistoryCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        # sublime_plugin.WindowCommand.__init__(self, window)
        super().__init__(window)
        self.conf = ConfSublHist('folders')

    def get_window(self, add_to: bool):
        """
        Returns the window in which the new data will be loaded.

        A new window if the active window is not empty, otherwise
        returns the active window
        """
        curwin = sublime.active_window()
        if (not curwin.folders() and not curwin.views()) or add_to:
            return curwin

        self.window.run_command('new_window')
        return sublime.active_window()

    def open_folder(self, index, add_to: bool):
        """
        Opens the selected folder in the active window

        :param  index:  The index of the folder in the quick panel list
        :param  add_to: Whether to add folder to current project
        """
        if index >= 0:
            folder = self.conf.items[index]
            self.conf.update_cache(last_selection=folder)
            if os.path.isdir(os.path.expanduser(folder)):
                new_win = self.get_window(add_to)
                if self.window.project_data() and add_to:
                    win_folders = self.window.project_data().get('folders', [])
                else:
                    win_folders = []
                win_folders.append({'path': folder})
                new_data = {'folders': win_folders}
                new_win.set_project_data(new_data)
                new_win.set_sidebar_visible(True)

    def run(self, add_to_project=False):
        self.conf.load_items_data()
        self.conf.set_display_list()
        placeholder = "Open Recent folder (out of {})".format(
            self.conf.items_count)
        if len(self.conf.display_list) > 0:
            self.window.show_quick_panel(
                self.conf.display_list,
                on_select=lambda idx: self.open_folder(idx, add_to_project),
                placeholder=placeholder,
                selected_index=self.conf.cache['last_index'])
        else:
            self.window.show_quick_panel(["No history found"], None)


class OpenFileHistoryCommand(sublime_plugin.WindowCommand):
    # conf = Conf('files')

    def __init__(self, window):
        super().__init__(window)
        self.conf = ConfSublHist('files')

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
                # new_win.set_sidebar_visible(True)
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
        # new_win.set_sidebar_visible(True)
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
                # selected_win.set_sidebar_visible(True)
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
