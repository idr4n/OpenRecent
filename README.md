# Open Recent Files and Folders

### Description

A Sublime Text plugin to open recent folders and files. The plugin is at its early stages and should work in MacOS, Linux, and Windows.

At the moment, it only tries to read from `Session.sublime_session` to capture the folders and files history. I'm planning to add the functionality that the plugin keeps track of the history itself, instead of depending on Sublime's session data.

Additionally, it provides two commands to open the current file in a new window or an existing window. It closes the current tab and opens the file in the specific window, with the limitation that all view-specific settings such as bookmarks, highlights, scroll, cursor positions, etc, would be lost, therefore use with caution. However, if there are unsaved changes, you will be prompted to save them first.

### Commands and keyboard shortcuts

It provides three commands at the moment:

```
[
  // Open folder history
  { "keys": ["super+shift+h"], "command": "open_folder_history" },
  // Open file history
  { "keys": ["super+shift+o"], "command": "open_file_history" },
  // Move current tab to new window
  { "keys": ["super+ctrl+shift+n"], "command": "move_to_new_window" },
  // Move current tab to a particular window
  { "keys": ["ctrl+alt+shift+n"], "command": "move_to_window" },
]
```

### Thanks

Thanks to the authors of [titoBouzout/SideBarFolders](https://github.com/titoBouzout/SideBarFolders), [FichteFoll/FileHistory](https://github.com/FichteFoll/FileHistory), and [randy3k/ProjectManager](https://github.com/randy3k/ProjectManager), as many ideas and concepts are borrowed from these plugins.

### License

Licensed under the [MIT License](http://www.opensource.org/licenses/mit-license.php)