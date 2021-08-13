# Open Recent Files and Folders

### Description

A Sublime Text plugin to open recent folders and files. The plugin is at its early stages and should only work in MacOS at the moment, but integration for Windows and Linux will be added soon.

At the moment, it only tries to read from `Session.sublime_session` to capture the folders and files history. I'm planning to add the functionality that the plugin itself keeps track of the history, instead of depending on Sublime's session data.

### Commands and keyboard shortcuts

It provides two commands at the moment:

```json
[
  // Open folder history
  { "keys": ["super+shift+h"], "command": "open_folder_history" },
  // Open file history
  { "keys": ["super+shift+o"], "command": "open_file_history" },
]

```

### Thanks

Thanks to the authors of [titoBouzout/SideBarFolders](https://github.com/titoBouzout/SideBarFolders), [FichteFoll/FileHistory](https://github.com/FichteFoll/FileHistory), and [randy3k/ProjectManager](https://github.com/randy3k/ProjectManager), as many ideas and concepts are borrowed from these plugins.

### License


OpenRecent is MIT licensed