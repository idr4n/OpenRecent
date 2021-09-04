# Open Recent Files and Folders

### Description

A Sublime Text plugin to open recent files and folders.

It stores the history of opened files and folders up to a maximum number of files and folders defined in the settings (the default is 50 files and 30 folders). The main difference with other plugins is that it automatically stores the recent opened folders together with the opened files associated to each folder. This means that when a folder is reopen using the `open_recent_folder` command, it will also open the last files you were working with associated to that folder. Something similar to a project manager, but without the need to manually store the project. It does not, however, store other information related to the folder or opened files, the way that a project manager would do.

All history is stored in Sublime's User directory in three files:

- `OpenRecent_recent_folders.json`
- `OpenRecent_folders_info.json`
- `OpenRecent_recent_files.json`

It also provides two commands to access Sublime's recent files and folders history, read from `Session.sublime_session`. The two commands are `open_file_history` and `open_folder_history`, which can be accessed from the command palette. Initially, the plugin was providing only this functionality, but somehow Sublime does not keep the history of all files and folders (i.e., sometimes I would try to reopen a file from history but I couldn't find it). The additional advantage of the plugin storing its own history is that it can also keep track of the opened files associated to recent folders.

Additionally, it adds two commands to open the current file in a new window or an existing window, trying to mimic a "move to window" functionality. It basically closes the current tab and opens the file in the specific window, preserving some view-specific settings such as bookmarks, selections, cursor position, and scroll position. Not all settings are preserved though, so use with caution. However, if there are unsaved changes, you will be prompted to save them first.

### Commands and keyboard shortcuts

The following shortcuts are provided by default:

```
[
  // Open folder history
  { "keys": ["super+shift+h"], "command": "open_recent_folder" },
  // Open folder history and add to project
  { "keys": ["ctrl+shift+h"], "command": "open_recent_folder",
    "args": { "add_to_project": true }
  },
  // Remove folder from history
  { "keys": ["ctrl+alt+shift+d"], "command": "remove_recent_folder" },
  // Open file history
  { "keys": ["super+shift+o"], "command": "open_recent_files" },
  // Move current tab to new window
  { "keys": ["super+ctrl+shift+n"], "command": "move_to_new_window" },
  // Move current tab to a particular window
  { "keys": ["ctrl+alt+shift+n"], "command": "move_to_window" },
]
```

If you want to access Sublime's files and folders history, you can also add these three mappings:

```
[
  { "keys": [...], "command": "open_folder_history" },
  { "keys": [...], "command": "open_folder_history",
    "args": { "add_to_project": true }
  },
  { "keys": [...], "command": "open_file_history" },
]
```


### Thanks To

Many thanks to the authors of [titoBouzout/SideBarFolders](https://github.com/titoBouzout/SideBarFolders), [FichteFoll/FileHistory](https://github.com/FichteFoll/FileHistory), [titoBouzout/BufferScroll](https://github.com/titoBouzout/BufferScroll), and [randy3k/ProjectManager](https://github.com/randy3k/ProjectManager), as many ideas and concepts are borrowed from these plugins.

### License

Licensed under the [MIT License](http://www.opensource.org/licenses/mit-license.php)