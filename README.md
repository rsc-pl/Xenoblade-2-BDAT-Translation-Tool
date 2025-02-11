# 🌐 Xenoblade 2 BDAT Translation Tool

<div align="center">

*A GUI tool for translating Xenoblade 2 BDAT files*

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![For Xenoblade 2](https://img.shields.io/badge/For-Xenoblade%202-red.svg)](https://www.nintendo.com/games/detail/xenoblade-chronicles-2-switch/)

</div>

## 📋 Overview

This translation tool provides a user-friendly interface for translating Xenoblade 2 extracted BDAT files. It's designed to work with BDAT files that have been extracted using the [BDAT Batch Extract/Unpack GUI Tool](https://github.com/rsc-pl/Xenoblade2-BDAT-Batch-Extract-Unpack-GUI).

![Screen](graphics/GUI.jpg)

## ✨ Features

- 🔍 Easy navigation through BDAT folders and files
- 📝 Side-by-side original text and translation editing
- 🎨 Translation progress tracking with color coding
- 🔄 Automatic progress saving
- 🔎 Quick search/filter functionality
- ⚡ Real-time text editing with special character support
- 💾 Automatic configuration saving

## 📋 Requirements

- 🐍 Python 3.x
- 📦 tkinter (usually included with Python)
- 📂 Extracted BDAT files from the Xenoblade2-BDAT-Batch-Extract-Unpack-GUI Tool

## 🚀 Installation

1. 📥 Clone the repository
2. 📦 Ensure Python 3.x is installed with tkinter
3. ▶️ Run `python Xenoblade2-Translation-GUI.py`

## 📖 Usage Guide

### Initial Setup

1. Click "Select Base Dir" and choose the directory containing your extracted BDAT folders
2. The file tree will populate with all available BDAT folders and their JSON files

### Navigation

- 🔍 Use the search bar to filter folders and files
- 📂 Double-click folders or files to load them
- 📑 The right panel shows the content of the selected JSON file

### Translation Process

1. Select a BDAT folder or JSON file from the left panel
2. Double-click the "EDITED TEXT" cell to begin translation
3. Edit the text:
   - Press Enter to save changes
   - Use Ctrl+Enter for new lines
   - Press Escape to cancel editing
4. Special characters are handled automatically:
   - `\n` for new lines
   - `\t` for tabs
   - `\r` for carriage returns
   - Square brackets `[ ]` are preserved

### Progress Tracking

The tool includes a color-coding system for tracking translation progress:

- 🟢 **Green**: Translation completed
- 🟧 **Orange**: Translation in progress
- ⬜ **No Color**: Not started

Use the buttons at the top to:
- "Mark Green" - Mark selected folder as completed
- "Mark Orange" - Mark selected folder as in progress
- "Clear Color" - Remove progress marking

### Saving and Undoing Changes

- 💾 Click "Save" to save your translations
- ↩️ Click "Undo" to revert to the last saved version
- ⚠️ The tool will prompt to save unsaved changes when switching files

## 🗃️ File Structure

The tool expects the following structure (created by the BDAT Extract tool):
```
Base Directory/
├── BDAT_Folder1/
│   └── BDAT_Folder1/
│       ├── file1.json
│       └── file2.json
├── BDAT_Folder2/
│   └── BDAT_Folder2/
│       ├── file1.json
│       └── file2.json
└── translation_config.ini
```

## 💾 Progress Saving

- Translation progress (color coding) is automatically saved in `translation_config.ini`
- The file is created automatically in your base directory
- Progress is restored when reopening the tool

## 🔧 Technical Details

### JSON Structure
The tool preserves the original JSON structure, saving the name field where the original text is stored:
```json
{
  "rows": [
    {
      "$id": "1",
      "label": "example",
      "style": "0",
      "name": "Text",
    }
  ]
}
```

### Special Character Handling
- Special characters are displayed in a readable format during editing
- They are automatically converted back to proper format when saving
- The tool maintains proper formatting for game compatibility

## ⚠️ Important Notes

1. Always back up your original files before translation
2. Save frequently to prevent loss of work
3. The tool automatically tracks unsaved changes
4. Use the search function to quickly find specific files
5. Color coding is saved across sessions

## 🔄 Workflow Tips

1. Start by marking folders orange as you begin translation
2. Use the search function to find related content across files
3. Mark folders green only when completely translated
4. Regularly save your progress
5. Use Ctrl+Enter for multi-line translations

## 🎮 Game Compatibility

- The tool is designed specifically for Xenoblade 2 BDAT files
- It maintains the correct file structure and formatting for game compatibility
- Special characters are handled according to the game's requirements

## 🔗 Related Tools

- [BDAT Batch Extract/Unpack GUI Tool](https://github.com/rsc-pl/Xenoblade2-BDAT-Batch-Extract-Unpack-GUI) - Required for extracting BDAT files before translation
