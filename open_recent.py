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

SESSION_FOLDER = os.path.join(
    os.path.dirname(sublime.packages_path()), 'Local')

# whether to display one or two lines in the quick panel
display_two_lines = False
# display_two_lines = True

cache = {
    'last_selection': '',
    'last_index': 0,
}

# class FolderListener(sublime_plugin.ViewEventListener):
#     def on_load(self):
#         print('--View activated')
#         sublime.active_window().run_command('save_folder')


def prettify_path(path: str):
    user_home = os.path.expanduser('~') + os.sep
    if path.startswith(os.path.expanduser('~')):
        return os.path.join('~', path[len(user_home):])
    return path


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
    folders = []
    folders_count = 0
    fpath = os.path.join(SESSION_FOLDER, 'Session.sublime_session')
    display_list = []

    @classmethod
    def load_folders_data(cls):
        """
        Class method

        Loads the list of folders to be shown in the quick panel
        """
        auto_session_path = os.path.join(
            SESSION_FOLDER, 'Auto Save Session.sublime_session')
        if os.path.exists(auto_session_path):
            cls.fpath = auto_session_path

        if os.path.exists(cls.fpath):
            with open(cls.fpath, encoding="utf-8") as f:
                try:
                    # decodes a JSON string into an object
                    # use sublime's decode_value method instead of
                    # Python's JSON library
                    # session_json = json.loads(f.read())
                    session_json = sublime.decode_value(f.read())
                    cls.folders = session_json['folder_history']
                    cls.folders_count = len(cls.folders)
                except Exception as Inst:
                    print(Inst)
                    sublime.message_dialog(
                        'Could not load JSON data from {}'.format(cls.fpath))
        else:
            sublime.message_dialog(
                "Path '{}' does not exist".format(cls.fspath))

    @classmethod
    def get_last_index(cls):
        try:
            return cls.folders.index(cache['last_selection'])
        except Exception:
            # print('Open Recent: No previous selection found')
            return 0

    @classmethod
    def set_display_list(cls):
        """
        Sets the display list to be shown in the Quick Panel

        The first row of each item has the last component of the path, while the
        second row has the rest (first part) of the path
        """
        prittified_folders = list(map(prettify_path, cls.folders))
        if display_two_lines:
            cls.display_list = [[os.path.basename(f), os.path.dirname(f)]
                                for f in prittified_folders]
        else:
            cls.display_list = prittified_folders

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

        :param      index:  The index of the folder selected
        """
        if index >= 0:
            folder = self.folders[index]
            cache['last_selection'] = folder
            cache['last_index'] = self.get_last_index()
            if os.path.isdir(os.path.expanduser(folder)):
                # subl('-n', folders[index])
                new_win = self.get_window()
                new_data = {'folders': [{'path': folder}]}
                new_win.set_project_data(new_data)
                new_win.set_sidebar_visible(True)

    def run(self):
        self.load_folders_data()
        self.set_display_list()
        placeholder = "Open Recent folder (out of {})".format(
            self.folders_count)
        self.window.show_quick_panel(
            self.display_list, self.open_folder, placeholder=placeholder,
            selected_index=cache['last_index'])
