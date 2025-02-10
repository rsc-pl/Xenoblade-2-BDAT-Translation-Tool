import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import threading
import shutil
import configparser
from tkinter import font

# --- New Global Variables ---
BASE_DIR = None
CURRENT_JSON_PATH = None
FOLDER_STATUS = {}  # Dictionary to store folder status (color)
CURRENT_JSON_DATA = None
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

def populate_table(tree, data):
    """Populates the Treeview table with JSON data."""
    # Clear existing data
    for item in tree.get_children():
        tree.delete(item)

    if data and 'rows' in data:
        for row in data['rows']:
            # Convert special characters to visible format
            def format_text(text):
                if not text:
                    return ""
                # Replace special characters with visible representations
                text = text.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
                # Handle square brackets by adding spaces around them for better visibility
                text = text.replace('[', ' [ ').replace(']', ' ] ')
                return text
            
            original_text = row.get('name', '')
            formatted_text = format_text(original_text)
            tree.insert("", "end", values=(
                row.get('$id', ''),
                row.get('label', ''),
                row.get('style', ''),
                formatted_text,
                formatted_text  # Format edited text column too
            ))

            # Calculate text height for the "EDITED TEXT" column
            text = row.get('name', '')
            font_style = font.Font(family="MS Gothic", size=10)  # Use the same font as the Treeview
            width = 200 // 7  # Width of the "EDITED TEXT" column in characters
            height = calculate_text_height(text, font_style, width)

            # Set row height
            s = ttk.Style()
            s.configure('Treeview', rowheight=int(height + 15))  # Add more padding

# --- GUI Functions ---

def browse_base_dir():
    """Opens a directory dialog to select the base directory."""
    global BASE_DIR
    BASE_DIR = filedialog.askdirectory()
    if BASE_DIR:
        base_dir_label.config(text=f"Base Directory: {BASE_DIR}")
        populate_file_list()

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
                    file_list.insert(folder_id, "end", 
                        text=child['text'], 
                        values=child['values']
                    )

def populate_file_list():
    """Populates the file list with BDAT folders and JSON files."""
    global ORIGINAL_FILE_LIST
    # Clear existing list
    for item in file_list.get_children():
        file_list.delete(item)

    if BASE_DIR:
        load_config()  # Load the configuration file
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
    global CURRENT_JSON_PATH, CURRENT_JSON_DATA

    CURRENT_JSON_PATH = json_path
    CURRENT_JSON_DATA = load_json(CURRENT_JSON_PATH)
    if CURRENT_JSON_DATA:
        populate_table(TREE, CURRENT_JSON_DATA)

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
        edited_text = TREE.item(item)['values'][4]  # Get the value from the "EDITED TEXT" column
        # Convert visible special characters back to actual characters
        if edited_text:
            edited_text = edited_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        if CURRENT_JSON_DATA and 'rows' in CURRENT_JSON_DATA and len(CURRENT_JSON_DATA['rows']) > index:
            CURRENT_JSON_DATA['rows'][index]['edited_text'] = edited_text

    save_json(CURRENT_JSON_PATH, CURRENT_JSON_DATA)
    UNSAVED_CHANGES = False  # Reset the flag after saving

def undo_changes():
    """Reloads the original JSON data into the table, discarding changes."""
    global CURRENT_JSON_PATH, CURRENT_JSON_DATA, UNSAVED_CHANGES
    if CURRENT_JSON_PATH:
        CURRENT_JSON_DATA = load_json(CURRENT_JSON_PATH)
        if CURRENT_JSON_DATA:
            populate_table(TREE, CURRENT_JSON_DATA)
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
        if column_id == 4:
            # Get bounding box of the cell
            x, y, width, height = TREE.bbox(item, column)

            # Get current value of the cell (already formatted)
            value = TREE.item(item, 'values')[column_id]

            # Create a text widget for multiline editing
            text_widget = tk.Text(TREE, wrap=tk.WORD, width=width//7, height=4)
            # Display escaped special characters for editing
            edit_value = value
            # Remove extra spaces around square brackets for editing
            edit_value = edit_value.replace(' [ ', '[').replace(' ] ', ']')
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
                values[3] = formatted_value         # Update the display version
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
    """Marks the selected folder with a background color."""
    selected_item = file_list.selection()
    if not selected_item:
        messagebox.showinfo("Info", "Please select a folder.")
        return

    folder_name = file_list.item(selected_item, 'text')  # Get folder name from the text
    folder_path = file_list.item(selected_item, 'values')[1]

    if status == "green":
        color = "green"
    elif status == "orange":
        color = "orange"
    else:
        color = ""  # Set color to empty string to clear the tag

    # Update the folder status in the dictionary
    if folder_name:
        if status:
            FOLDER_STATUS[folder_name] = status  # Store the status
        else:
            FOLDER_STATUS.pop(folder_name, None)  # Remove the folder from the status if clearing

        # Apply the tag to the selected item
        file_list.item(selected_item, tags=(color,))

        save_config()  # Save the configuration

def load_config():
    """Loads the folder status from the config file."""
    global FOLDER_STATUS
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "translation_config.ini")

    try:
        config.read(config_path)
        if 'FOLDER_STATUS' in config:
            for folder, status in config['FOLDER_STATUS'].items():
                FOLDER_STATUS[folder] = status
    except Exception as e:
        print(f"Error loading config: {e}")

    # Apply colors to folders based on loaded config
    for item in file_list.get_children():
        folder_name = file_list.item(item, 'text')
        if folder_name in FOLDER_STATUS:
            file_list.item(item, tags=(FOLDER_STATUS[folder_name],))

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

# --- GUI Setup ---

root = tk.Tk()
root.title("BDAT Translation Tool")

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

# --- Folder Status Buttons ---
mark_green_button = ttk.Button(top_frame, text="Mark Green", command=lambda: mark_folder("green"))
mark_green_button.pack(side=tk.LEFT, padx=5, pady=5)

mark_orange_button = ttk.Button(top_frame, text="Mark Orange", command=lambda: mark_folder("orange"))
mark_orange_button.pack(side=tk.LEFT, padx=5, pady=5)

clear_color_button = ttk.Button(top_frame, text="Clear Color", command=lambda: mark_folder(None))
clear_color_button.pack(side=tk.LEFT, padx=5, pady=5)

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

# --- Treeview Table ---
s = ttk.Style()
s.configure('Treeview', rowheight=40)

TREE = ttk.Treeview(right_frame, columns=("ID", "LABEL", "STYLE", "NAME", "EDITED TEXT"), show="headings", style='Treeview')
TREE.heading("ID", text="ID")
TREE.heading("LABEL", text="LABEL")
TREE.heading("STYLE", text="STYLE")
TREE.heading("NAME", text="NAME")
TREE.heading("EDITED TEXT", text="EDITED TEXT")

# Set column widths
TREE.column("ID", width=50, stretch=False)
TREE.column("LABEL", width=150, stretch=False)
TREE.column("STYLE", width=50, stretch=False)
TREE.column("NAME", width=200)
TREE.column("EDITED TEXT", width=200, anchor=tk.W)  # Allow text wrapping

TREE.pack(fill=tk.BOTH, expand=True)

# Bind double click to edit cell
TREE.bind("<Double-1>", edit_cell)

# --- Buttons ---
save_button = ttk.Button(right_frame, text="Save", command=save_table_data)
save_button.pack(side=tk.LEFT, padx=5, pady=5)

undo_button = ttk.Button(right_frame, text="Undo", command=undo_changes)
undo_button.pack(side=tk.LEFT, padx=5, pady=5)

root.mainloop()
