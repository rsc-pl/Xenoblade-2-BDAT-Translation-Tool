import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
import shutil
import configparser
from tkinter import font
import atexit

# --- New Global Variables ---
BASE_DIR = None
SECOND_BASE_DIR = None  # For translated files
CURRENT_JSON_PATH = None
CURRENT_ORIGINAL_JSON_PATH = None  # Path to original language file
FOLDER_STATUS = {}  # Dictionary to store folder status (color)
CURRENT_JSON_DATA = None
CURRENT_ORIGINAL_JSON_DATA = None  # Original language data
TREE = None  # global tree variable
UNSAVED_CHANGES = False

# --- Helper Functions ---
def load_json(filepath):
    """Loads JSON data from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error Loading JSON", str(e))
        return None

def save_json(filepath, data):
    """Saves JSON data to a file, replacing the 'name' field with 'edited_text'."""
    try:
        # First, create a copy of the data to avoid modifying the original
        data_copy = json.loads(json.dumps(data))

        for row in data_copy['rows']:
            if 'edited_text' in row:
                row['name'] = row['edited_text']
                del row['edited_text']  # Remove the 'edited_text' field after saving

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Success", "JSON saved successfully!")
    except Exception as e:
        messagebox.showerror("Error Saving JSON", str(e))

def calculate_text_height(text, font, width):
    """Calculates the height of the text based on the font and width."""
    text_widget = tk.Text(root, font=font, wrap=tk.WORD, width=width)
    text_widget.insert("1.0", text)
    text_widget.update_idletasks()  # Force update of the widget
    bbox = text_widget.bbox("end")
    height = bbox[3] if bbox else 20  # Default height if bbox is None
    text_widget.destroy()
    return height + 10  # Add extra padding to make rows taller

def populate_table(tree, original_data, translated_data):
    """Populates the Treeview table with JSON data from both original and translated files."""
    # Clear existing data
    for item in tree.get_children():
        tree.delete(item)

    def format_text(text):
        if not text:
            return ""
        # Replace special characters with visible representations
        text = text.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
        # Handle square brackets by adding spaces around them for better visibility
        #text = text.replace('[', ' [ ').replace(']', ' ] ')
        return text

    # Use translated data if available, otherwise use original
    data = translated_data if translated_data else original_data
    
    if data and 'rows' in data:
        for idx, row in enumerate(data['rows']):
            # Get original text if available
            original_text = ""
            if original_data and 'rows' in original_data and len(original_data['rows']) > idx:
                original_text = original_data['rows'][idx].get('name', '')
            
            # Get translated text
            translated_text = row.get('name', '')
            
            tree.insert("", "end", values=(
                row.get('$id', ''),
                row.get('label', ''),
                format_text(original_text),
                format_text(translated_text)
            ))

            # Calculate text height for the "EDITED TEXT" column
            text = row.get('name', '')
            font_style = font.Font(family="MS Gothic", size=10)
            width = 200 // 7
            height = calculate_text_height(text, font_style, width)

            s = ttk.Style()
            s.configure('Treeview', rowheight=int(height + 15))

# --- GUI Functions ---

def browse_base_dir():
    """Opens a directory dialog to select the base directory."""
    global BASE_DIR
    BASE_DIR = filedialog.askdirectory()
    if BASE_DIR:
        base_dir_label.config(text=f"Base Directory: {BASE_DIR}")
        populate_file_list()
        save_gui_state()  # Save the GUI state

def browse_second_base_dir():
    """Opens a directory dialog to select the second base directory."""
    global SECOND_BASE_DIR
    SECOND_BASE_DIR = filedialog.askdirectory()
    if SECOND_BASE_DIR:
        second_base_dir_label.config(text=f"Second Directory: {SECOND_BASE_DIR}")
        save_gui_state()  # Save the GUI state

# Add this at the top with other global variables
ORIGINAL_FILE_LIST = []

def filter_folders(event=None):
    """Filters folders based on search text."""
    search_text = search_var.get().lower()
    
    # Clear the current view
    for item in file_list.get_children():
        file_list.delete(item)
    
    # Rebuild the tree from original list
    for folder in ORIGINAL_FILE_LIST:
        folder_name = folder['text'].lower()
        folder_matches = not search_text or search_text in folder_name
        
        # If folder matches or any child matches, show it
        if folder_matches or any(search_text in child['text'].lower() for child in folder['children']):
            # Recreate the folder item
            folder_id = file_list.insert("", "end", 
                text=folder['text'], 
                values=folder['values'],
                tags=folder.get('tags', ())
            )
            
            # Add matching children
            for child in folder['children']:
                if not search_text or search_text in child['text'].lower():
                    child_id = file_list.insert(folder_id, "end", 
                        text=child['text'], 
                        values=child['values']
                    )
                    # Apply color to child if it's in FOLDER_STATUS
                    rel_path = child['values'][1].replace(BASE_DIR + '\\', '').replace('\\', '/')
                    if rel_path in FOLDER_STATUS:
                        file_list.item(child_id, tags=(FOLDER_STATUS[rel_path],))

def populate_file_list():
    """Populates the file list with BDAT folders and JSON files."""
    global ORIGINAL_FILE_LIST
    # Clear existing list
    for item in file_list.get_children():
        file_list.delete(item)

    if BASE_DIR:
        ORIGINAL_FILE_LIST = []  # Reset the original list

        for bdat_folder in os.listdir(BASE_DIR):
            bdat_folder_path = os.path.join(BASE_DIR, bdat_folder)
            if os.path.isdir(bdat_folder_path):
                folder_id = file_list.insert("", "end", text=bdat_folder, values=("folder", bdat_folder_path))  # Store folder path
                # Store in original list
                ORIGINAL_FILE_LIST.append({
                    'id': folder_id,
                    'text': bdat_folder,
                    'values': ("folder", bdat_folder_path),
                    'children': []
                })
                
                # Apply background color based on config
                if bdat_folder in FOLDER_STATUS:
                    file_list.item(folder_id, tags=(FOLDER_STATUS[bdat_folder],))

                inner_folder_path = os.path.join(bdat_folder_path, bdat_folder)
                if os.path.isdir(inner_folder_path):
                    json_files = [f for f in os.listdir(inner_folder_path) if f.endswith(".json")]
                    for json_file in json_files:
                        json_path = os.path.join(inner_folder_path, json_file)
                        child_id = file_list.insert(folder_id, "end", text=json_file, values=("file", json_path))  # Store JSON path
                        # Store in original list
                        ORIGINAL_FILE_LIST[-1]['children'].append({
                            'id': child_id,
                            'text': json_file,
                            'values': ("file", json_path)
                        })


def load_table_data(json_path):
    """Loads the selected JSON file into the table."""
    global CURRENT_JSON_PATH, CURRENT_JSON_DATA, CURRENT_ORIGINAL_JSON_PATH, CURRENT_ORIGINAL_JSON_DATA

    CURRENT_JSON_PATH = json_path
    CURRENT_JSON_DATA = load_json(CURRENT_JSON_PATH)
    
    # Find corresponding file in second base dir if it exists
    CURRENT_ORIGINAL_JSON_DATA = None
    if SECOND_BASE_DIR:
        # Get relative path from first base dir
        rel_path = os.path.relpath(json_path, BASE_DIR)
        # Build path in second base dir
        original_path = os.path.join(SECOND_BASE_DIR, rel_path)
        if os.path.exists(original_path):
            CURRENT_ORIGINAL_JSON_PATH = original_path
            CURRENT_ORIGINAL_JSON_DATA = load_json(original_path)
    
    if CURRENT_JSON_DATA:
        populate_table(TREE, CURRENT_ORIGINAL_JSON_DATA, CURRENT_JSON_DATA)

def file_list_select(event):
    """Handles selection in the file list."""
    global CURRENT_JSON_PATH, UNSAVED_CHANGES

    # Check for unsaved changes before proceeding
    if UNSAVED_CHANGES and CURRENT_JSON_PATH:
        response = messagebox.askyesnocancel("Warning", "You have unsaved changes. Do you want to save them?", icon='warning')
        if response is True:  # Yes, save changes
            save_table_data()
        elif response is None:  # Cancel
            return  # Do nothing, stay on the current file

    selected_item = file_list.selection()
    if not selected_item:
        return

    item_type = file_list.item(selected_item, 'values')[0]
    item_path = file_list.item(selected_item, 'values')[1]

    if item_type == "file":
        load_table_data(item_path)
    elif item_type == "folder":
        # Load the first JSON file in the folder
        inner_folder_path = os.path.join(item_path, os.path.basename(item_path))
        if os.path.isdir(inner_folder_path):
            json_files = [f for f in os.listdir(inner_folder_path) if f.endswith(".json")]
            if json_files:
                first_json_path = os.path.join(inner_folder_path, json_files[0])
                load_table_data(first_json_path)
    
    UNSAVED_CHANGES = False  # Reset the flag after loading new data

def save_table_data():
    """Saves the edited data back to the JSON file."""
    global CURRENT_JSON_PATH, CURRENT_JSON_DATA, UNSAVED_CHANGES

    if not CURRENT_JSON_PATH or not CURRENT_JSON_DATA:
        messagebox.showerror("Error", "No JSON file loaded.")
        return

    # Get data from the treeview
    for index, item in enumerate(TREE.get_children()):
        edited_text = TREE.item(item)['values'][3]  # Get the value from the translated text column
        # Convert visible special characters back to actual characters
        if edited_text:
            edited_text = edited_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        if CURRENT_JSON_DATA and 'rows' in CURRENT_JSON_DATA and len(CURRENT_JSON_DATA['rows']) > index:
            CURRENT_JSON_DATA['rows'][index]['edited_text'] = edited_text

    save_json(CURRENT_JSON_PATH, CURRENT_JSON_DATA)
    UNSAVED_CHANGES = False  # Reset the flag after saving

def undo_changes():
    """Reloads the original JSON data into the table, discarding changes."""
    global CURRENT_JSON_PATH, CURRENT_JSON_DATA, CURRENT_ORIGINAL_JSON_DATA, UNSAVED_CHANGES
    if CURRENT_JSON_PATH:
        # Reload the JSON data
        CURRENT_JSON_DATA = load_json(CURRENT_JSON_PATH)
        if CURRENT_JSON_DATA:
            # Repopulate the table with original and translated data
            populate_table(TREE, CURRENT_ORIGINAL_JSON_DATA, CURRENT_JSON_DATA)
            messagebox.showinfo("Info", "Changes undone. Table reloaded from file.")
            UNSAVED_CHANGES = False  # Reset the flag after undo
    else:
        messagebox.showinfo("Info", "No file loaded.")

def edit_cell(event):
    """Handles cell editing in the Treeview."""
    global UNSAVED_CHANGES
    if not UNSAVED_CHANGES:
        UNSAVED_CHANGES = True  # Set flag on first edit
    for item in TREE.selection():
        # Identify column and row
        column = TREE.identify_column(event.x)
        row = TREE.identify_row(event.y)

        # Get column id
        column_id = int(column[1:]) - 1

        # Only allow editing of the "EDITED TEXT" column (column 4)
        if column_id == 3:
            # Get bounding box of the cell
            x, y, width, height = TREE.bbox(item, column)

            # Get current value of the cell (already formatted)
            value = TREE.item(item, 'values')[column_id]

            # Create a text widget for multiline editing
            text_widget = tk.Text(TREE, wrap=tk.WORD, width=width//7, height=4)
            # Display escaped special characters for editing
            edit_value = value.replace('\n', '\\n')
            text_widget.insert("1.0", edit_value)
            text_widget.place(x=x, y=y, width=width, height=height)
            text_widget.focus()

            def save_value(event=None):
                # Get the text and convert special characters back to visible format
                new_value = text_widget.get("1.0", "end-1c")
                formatted_value = new_value.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                
                # Update the tree values
                values = list(TREE.item(item, 'values'))
                values[column_id] = formatted_value  # Store formatted version
                TREE.item(item, values=values)
                UNSAVED_CHANGES = True  # Set the flag when a change is made
                
                # Update row height
                font_style = font.Font(family="MS Gothic", size=10)
                new_height = calculate_text_height(formatted_value, font_style, width//7)
                s = ttk.Style()
                s.configure('Treeview', rowheight=int(new_height + 15))
                
                text_widget.destroy()

            # Bind enter key to save the value
            text_widget.bind('<Return>', save_value)
            text_widget.bind('<Control-Return>', lambda e: text_widget.insert(tk.INSERT, '\n'))

            # Bind focus out to save the value and destroy the text widget
            text_widget.bind('<FocusOut>', save_value)

            # Bind escape key to cancel editing
            def cancel_edit(event):
                text_widget.destroy()
            text_widget.bind('<Escape>', cancel_edit)

def mark_folder(status):
    """Marks the selected folder or file with a background color."""
    selected_item = file_list.selection()
    if not selected_item:
        messagebox.showinfo("Info", "Please select a folder or file.")
        return

    item_text = file_list.item(selected_item, 'text')
    item_path = file_list.item(selected_item, 'values')[1]
    item_type = file_list.item(selected_item, 'values')[0]

    if status == "green":
        color = "green"
    elif status == "orange":
        color = "orange"
    else:
        color = ""  # Set color to empty string to clear the tag

    # For files, store relative path from the BDAT folder
    if item_type == "file":
        # Get the BDAT folder name (parent folder)
        bdat_folder = os.path.basename(os.path.dirname(os.path.dirname(item_path)))
        # Get relative path within BDAT folder
        rel_path = os.path.relpath(item_path, os.path.join(BASE_DIR, bdat_folder))
        # Convert to forward slashes for consistency
        key = rel_path.replace('\\', '/')
    else:
        # For folders, just use the folder name
        key = item_text

    # Update the status in the dictionary
    if key:
        if status:
            FOLDER_STATUS[key] = status  # Store the status
        else:
            FOLDER_STATUS.pop(key, None)  # Remove the item from the status if clearing

        # Apply the tag to the selected item
        file_list.item(selected_item, tags=(color,))

        save_config()  # Save the configuration

def load_config():
    """Loads the folder and file status from the config file."""
    global FOLDER_STATUS
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "translation_config.ini")

    try:
        config.read(config_path)
        if 'FOLDER_STATUS' in config:
            FOLDER_STATUS = {k: v for k, v in config['FOLDER_STATUS'].items()}
    except Exception as e:
        print(f"Error loading config: {e}")

    # Apply colors to both folders and files based on loaded config
    for item in file_list.get_children():
        item_text = file_list.item(item, 'text')
        item_path = file_list.item(item, 'values')[1]
        item_type = file_list.item(item, 'values')[0]

        if item_type == "folder":
            # For folders, check by name
            if item_text in FOLDER_STATUS:
                file_list.item(item, tags=(FOLDER_STATUS[item_text],))
            # Apply colors to child files as well
            for child in file_list.get_children(item):
                child_text = file_list.item(child, 'text')
                child_path = file_list.item(child, 'values')[1]
                # Get the BDAT folder name (parent folder)
                bdat_folder = os.path.basename(os.path.dirname(os.path.dirname(child_path)))
                # Get relative path within BDAT folder
                rel_path = os.path.relpath(child_path, os.path.join(BASE_DIR, bdat_folder))
                # Convert to forward slashes for consistency
                key = rel_path.replace('\\', '/')
                if key in FOLDER_STATUS:
                    file_list.item(child, tags=(FOLDER_STATUS[key],))

        elif item_type == "file":
            # For files, check by relative path
            # Get the BDAT folder name (parent folder)
            bdat_folder = os.path.basename(os.path.dirname(os.path.dirname(item_path)))
            # Get relative path within BDAT folder
            rel_path = os.path.relpath(item_path, os.path.join(BASE_DIR, bdat_folder))
            # Convert to forward slashes for consistency
            key = rel_path.replace('\\', '/')
            if key in FOLDER_STATUS:
                file_list.item(item, tags=(FOLDER_STATUS[key],))

def save_config():
    """Saves the folder status to the config file."""
    config = configparser.ConfigParser()
    config['FOLDER_STATUS'] = FOLDER_STATUS
    config_path = os.path.join(BASE_DIR, "translation_config.ini")

    try:
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        print(f"Error saving config: {e}")

def save_gui_state():
    """Saves the GUI state (base directories) to the config file."""
    config = configparser.ConfigParser()
    config['GUI_STATE'] = {
        'base_dir': BASE_DIR if BASE_DIR else "",
        'second_base_dir': SECOND_BASE_DIR if SECOND_BASE_DIR else ""
    }
    # Add quotes around the values
    for key in config['GUI_STATE']:
        config['GUI_STATE'][key] = f"\"{config['GUI_STATE'][key]}\""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    config_path = os.path.join(script_dir, f"{script_name}.ini")  # Save in the same directory as the script

    try:
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        print(f"Error saving GUI state: {e}")

def load_gui_state():
    """Loads the GUI state (base directories) from the config file."""
    global BASE_DIR, SECOND_BASE_DIR
    config = configparser.ConfigParser()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    config_path = os.path.join(script_dir, f"{script_name}.ini")

    try:
        config.read(config_path)
        if 'GUI_STATE' in config:
            BASE_DIR = config['GUI_STATE'].get('base_dir', "").strip('"')
            SECOND_BASE_DIR = config['GUI_STATE'].get('second_base_dir', "").strip('"')

            print(f"Loaded BASE_DIR: {BASE_DIR}")
            print(f"Loaded SECOND_BASE_DIR: {SECOND_BASE_DIR}")

            # Update the labels
            if BASE_DIR:
                base_dir_label.config(text=f"Base Directory: {BASE_DIR}")
                populate_file_list()
            if SECOND_BASE_DIR:
                second_base_dir_label.config(text=f"Second Directory: {SECOND_BASE_DIR}")

    except Exception as e:
        print(f"Error loading GUI state: {e}")
    print(f"Config file path: {config_path}")

# --- GUI Setup ---

root = tk.Tk()
root.title("BDAT Translation Tool")

# Call save_gui_state when the window is closed
root.protocol("WM_DELETE_WINDOW", lambda: [save_gui_state(), root.destroy()])

# --- Top Frame (Directory/File Navigation and Buttons) ---
top_frame = ttk.Frame(root, padding=10)
top_frame.pack(side=tk.TOP, fill=tk.X)

# Search filter
search_frame = ttk.Frame(top_frame)
search_frame.pack(side=tk.LEFT, padx=5, pady=5)

search_label = ttk.Label(search_frame, text="Search:")
search_label.pack(side=tk.LEFT)

search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind('<KeyRelease>', filter_folders)

base_dir_button = ttk.Button(top_frame, text="Select Base Dir", command=browse_base_dir)
base_dir_button.pack(side=tk.LEFT, padx=5, pady=5)

base_dir_label = ttk.Label(top_frame, text="Base Directory: None")
base_dir_label.pack(side=tk.LEFT, padx=5, pady=5)

second_base_dir_button = ttk.Button(top_frame, text="Select Second Dir", command=browse_second_base_dir)
second_base_dir_button.pack(side=tk.LEFT, padx=5, pady=5)

second_base_dir_label = ttk.Label(top_frame, text="Second Directory: None")
second_base_dir_label.pack(side=tk.LEFT, padx=5, pady=5)

# --- Panedwindow for Left/Right Sections ---
paned_window = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

# --- Left Frame (File List) ---
left_frame = ttk.Frame(paned_window, padding=10)
paned_window.add(left_frame)

# --- File List with Scrollbar ---
file_list_frame = ttk.Frame(left_frame)
file_list_frame.pack(fill=tk.BOTH, expand=True)

file_list_scrollbar = ttk.Scrollbar(file_list_frame)
file_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

file_list = ttk.Treeview(file_list_frame, columns=("Type", "Path"), yscrollcommand=file_list_scrollbar.set)
file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
file_list.heading("#0", text="Folders/Files", anchor=tk.W)
file_list.heading("Type", text="Type")
file_list.column("Type", width=50, stretch=False)
file_list.column("Path", width=0, stretch=False)  # Hide the path column
file_list.bind("<Double-1>", file_list_select)  # Double-click to load

def open_translated_dir(event=None):
    selected_item = file_list.selection()
    if selected_item:
        item_type = file_list.item(selected_item, 'values')[0]
        item_path = file_list.item(selected_item, 'values')[1]
        if item_type == "folder":
            inner_folder_path = os.path.join(item_path, os.path.basename(item_path))
            try:
                os.startfile(inner_folder_path)
            except OSError:
                messagebox.showerror("Error", "Unable to open directory.")
        elif item_type == "file":
            try:
                os.startfile(item_path)
            except OSError:
                messagebox.showerror("Error", "Unable to open file.")

def open_original_dir(event=None):
    selected_item = file_list.selection()
    if selected_item:
        item_type = file_list.item(selected_item, 'values')[0]
        item_path = file_list.item(selected_item, 'values')[1]
        
        # Check if a second base directory is set
        if SECOND_BASE_DIR:
            # Get the relative path from the base directory
            rel_path = os.path.relpath(item_path, BASE_DIR)
            # Construct the path in the second base directory
            original_path = os.path.join(SECOND_BASE_DIR, rel_path)
            
            # Check if the item is a folder or a file
            if item_type == "folder":
                # Check if the directory exists in the second base directory
                if os.path.isdir(original_path):
                    try:
                        os.startfile(original_path)
                    except OSError:
                        messagebox.showerror("Error", "Unable to open original directory.")
                else:
                    messagebox.showinfo("Info", "Original directory not found.")
            elif item_type == "file":
                # Check if the file exists in the second base directory
                if os.path.isfile(original_path):
                    try:
                        os.startfile(original_path)
                    except OSError:
                        messagebox.showerror("Error", "Unable to open original file.")
                else:
                    messagebox.showinfo("Info", "Original file not found.")
        else:
            messagebox.showinfo("Info", "Second base directory not set.")

def show_context_menu(event):
    selected_item = file_list.selection()
    if selected_item:
        context_menu.post(event.x_root, event.y_root)

# Create context menu
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Open Translated JSON Directory", command=open_translated_dir)
context_menu.add_command(label="Open Original JSON Directory", command=open_original_dir)

# Bind right click to show context menu
file_list.bind("<Button-3>", show_context_menu)

file_list_scrollbar.config(command=file_list.yview)

# --- Define tags for background colors ---
file_list.tag_configure("green", background="green")
file_list.tag_configure("orange", background="orange")

# --- Right Frame (Table Editor) ---
right_frame = ttk.Frame(paned_window, padding=10)
paned_window.add(right_frame)

# --- Buttons ---
button_frame = ttk.Frame(right_frame)
button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

save_button = ttk.Button(button_frame, text="Save", command=save_table_data)
save_button.pack(side=tk.LEFT, padx=5, pady=5)

undo_button = ttk.Button(button_frame, text="Undo", command=undo_changes)
undo_button.pack(side=tk.LEFT, padx=5, pady=5)

mark_green_button = ttk.Button(button_frame, text="Mark Green", command=lambda: mark_folder("green"))
mark_green_button.pack(side=tk.LEFT, padx=5, pady=5)

mark_orange_button = ttk.Button(button_frame, text="Mark Orange", command=lambda: mark_folder("orange"))
mark_orange_button.pack(side=tk.LEFT, padx=5, pady=5)

clear_color_button = ttk.Button(button_frame, text="Clear Color", command=lambda: mark_folder(None))
clear_color_button.pack(side=tk.LEFT, padx=5, pady=5)

# --- Treeview Table ---
s = ttk.Style()
s.configure('Treeview', rowheight=40)

TREE = ttk.Treeview(right_frame, columns=("ID", "LABEL", "ORIGINAL TEXT", "TRANSLATED TEXT"), show="headings", style='Treeview')
TREE.heading("ID", text="ID")
TREE.heading("LABEL", text="LABEL")
TREE.heading("ORIGINAL TEXT", text="ORIGINAL TEXT")
TREE.heading("TRANSLATED TEXT", text="TRANSLATED TEXT")

# Set column widths
TREE.column("ID", width=50, stretch=False)
TREE.column("LABEL", width=150, stretch=False)
TREE.column("ORIGINAL TEXT", width=200, anchor=tk.W)
TREE.column("TRANSLATED TEXT", width=200, anchor=tk.W)  # Allow text wrapping

# Add a Scrollbar to the Treeview Table
tree_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=TREE.yview)
TREE.configure(yscrollcommand=tree_scroll.set)
tree_scroll.pack(side="right", fill="y")
TREE.pack(fill=tk.BOTH, expand=True)

# Bind double click to edit cell
TREE.bind("<Double-1>", edit_cell)

def copy_cell_value():
    """Copies the value of the selected cell to the clipboard."""
    item = TREE.selection()[0]  # Get the selected item
    column_id = int(TREE.identify_column(event.x)[1:]) - 1  # Get the column ID
    value = TREE.item(item, 'values')[column_id]  # Get the cell value
    root.clipboard_clear()
    root.clipboard_append(value)
    root.update()

def show_tree_context_menu(event):
    """Shows the context menu for the Treeview."""
    for item in TREE.selection():
        tree_context_menu.post(event.x_root, event.y_root)

# Create context menu for the Treeview
tree_context_menu = tk.Menu(root, tearoff=0)
tree_context_menu.add_command(label="Copy Cell Value", command=lambda: copy_cell_value())

def show_tree_context_menu(event):
    """Shows the context menu for the Treeview."""
    tree_context_menu.post(event.x_root, event.y_root)
    global context_menu_event
    context_menu_event = event

def copy_cell_value():
    """Copies the value of the selected cell to the clipboard."""
    item = TREE.selection()[0]  # Get the selected item
    column_id = int(TREE.identify_column(context_menu_event.x)[1:]) - 1  # Get the column ID
    value = TREE.item(item, 'values')[column_id]  # Get the cell value
    root.clipboard_clear()
    root.clipboard_append(value)
    root.update()

# Bind right click to show context menu
TREE.bind("<Button-3>", show_tree_context_menu)

# Load GUI state on startup
load_gui_state()

# Load config after GUI state is loaded and BASE_DIR is set
if BASE_DIR:
    print(f"Loading config from: {os.path.join(BASE_DIR, 'translation_config.ini')}")
    load_config()
    # Apply colors to folders based on loaded config
    for item in file_list.get_children():
        folder_name = file_list.item(item, 'text')
        if folder_name in FOLDER_STATUS:
            file_list.item(item, tags=(FOLDER_STATUS[folder_name],))
    populate_file_list()  # Ensure the file list is populated with the correct colors
    
    # Apply colors to files after populating the file list
    for item in file_list.get_children():
        item_type = file_list.item(item, 'values')[0]
        if item_type == "folder":
            for child in file_list.get_children(item):
                child_path = file_list.item(child, 'values')[1]
                # Get the BDAT folder name (parent folder)
                bdat_folder = os.path.basename(os.path.dirname(os.path.dirname(child_path)))
                # Get relative path within BDAT folder
                rel_path = os.path.relpath(child_path, os.path.join(BASE_DIR, bdat_folder))
                # Convert to forward slashes for consistency
                key = rel_path.replace('\\', '/')
                if key in FOLDER_STATUS:
                    file_list.item(child, tags=(FOLDER_STATUS[key],))

root.mainloop()
