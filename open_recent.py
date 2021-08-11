import os
import sublime
import sublime_plugin

# mylist = [
#     '/Users/ivan/pCloud/Dev/Rust/Rust_Web_Programming/todo_app',
#     '/Users/ivan/Dropbox/Notes-Database'
# ]

# the Session.sublime_session that contains the folders and files history is
# located in '/Users/ivan/Library/Application Support/Sublime Text 3/Local'

# SESSION_FOLDER = '/Users/ivan/Library/Application Support\
# /Sublime Text 3/Local/'


class Conf():
    SETTINGS_DICT = {
        'osx': 'OpenRecent (OSX).sublime-settings',
        'windows': 'OpenRecent (Windows).sublime-settings',
        'linux': 'OpenRecent (Linux).sublime-settings',
    }
    OS = sublime.platform()

    def __init__(self):
        self.settings = sublime.load_settings(Conf.SETTINGS_DICT[Conf.OS])
        self.session_path = self.get_session_folder()
        self.folders = []
        self.folders_count = 0
        self.fpath = os.path.join(self.session_path, 'Session.sublime_session')
        self.display_list = []
        self.cache = {'last_selection': '', 'last_index': 0}

    def get_session_folder(self):
        """
        Returns the folder where Sublime's session is stored in the system.
        """
        if self.settings.get('session_folder'):
            return self.settings.get('session_folder')

        pack_path = sublime.packages_path()
        if self.OS == 'osx':
            return os.path.join(os.path.dirname(pack_path), 'Local')

    def load_folders_data(self):
        """
        Loads the list of folders to be shown in the quick panel
        """
        auto_session_path = os.path.join(self.session_path,
                                         'Auto Save Session.sublime_session')
        if os.path.exists(auto_session_path):
            self.fpath = auto_session_path

        if os.path.exists(self.fpath):
            with open(self.fpath, encoding="utf-8") as f:
                try:
                    # decodes a JSON string into an object
                    # use sublime's decode_value method instead of
                    # Python's JSON library
                    # session_json = json.loads(f.read())
                    session_json = sublime.decode_value(f.read())
                    self.folders = session_json['folder_history']
                    self.folders_count = len(self.folders)
                except Exception as Inst:
                    print('OpenRecent Exception:', Inst)
                    sublime.message_dialog(
                        'Could not load JSON data from {}'.format(self.fpath))
        else:
            sublime.message_dialog(
                "Path '{}' does not exist".format(self.fpath))

    def get_last_index(self):
        """
        Returns the index of the last selected item.
        """
        try:
            return self.folders.index(self.cache['last_selection'])
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
        prittified_folders = list(map(self.prettify_path, self.folders))
        if conf.settings.get('display_two_lines', False):
            self.display_list = [[os.path.basename(f), os.path.dirname(f)]
                                 for f in prittified_folders]
        else:
            self.display_list = prittified_folders

    @staticmethod
    def prettify_path(path: str):
        user_home = os.path.expanduser('~') + os.sep
        if path.startswith(os.path.expanduser('~')):
            return os.path.join('~', path[len(user_home):])
        return path


# class FolderListener(sublime_plugin.ViewEventListener):
#     def on_load(self):
#         print('--View activated')
#         sublime.active_window().run_command('save_folder')

class FolderListener(sublime_plugin.EventListener):
    def on_new_window_async(self, window):
        print('--New window opened')
        window.run_command('save_folder')


class SaveFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()
        if folder:
            print("Folder name:", folder)
        else:
            print('No folder in window')


class OpenFolderHistoryCommand(sublime_plugin.WindowCommand):
    conf = Conf()

    def get_window(self):
        """
        Returns the window in which the new data will be loaded.

        Returns a new window if the active window is not empty, otherwise
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

        :param  index:  The index of the folder in the quick panel display
        list
        """
        if index >= 0:
            folder = self.conf.folders[index]
            self.conf.update_cache(last_selection=folder)
            if os.path.isdir(os.path.expanduser(folder)):
                new_win = self.get_window()
                new_data = {'folders': [{'path': folder}]}
                new_win.set_project_data(new_data)
                new_win.set_sidebar_visible(True)

    def run(self):
        self.conf.load_folders_data()
        self.conf.set_display_list()
        placeholder = "Open Recent folder (out of {})".format(
            self.conf.folders_count)
        self.window.show_quick_panel(
            self.conf.display_list, self.open_folder, placeholder=placeholder,
            selected_index=self.conf.cache['last_index'])
