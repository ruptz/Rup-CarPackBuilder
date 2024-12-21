import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import sys
import sv_ttk
import pywinstyles

# Define main folders
BASE_FOLDER = ""
STREAM_FOLDER = ""
DATA_FOLDER = ""
STREAM_DATA_FOLDER = ""
DLC_FOLDER = ""
DLC_TXT_FILE = "dlc_files.txt"

skipped_meta_files = []
skipped_stream_folders = []
dlc_folders = []
results = []

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

def update_folders(base_path):
    global BASE_FOLDER, STREAM_FOLDER, DATA_FOLDER, STREAM_DATA_FOLDER, DLC_FOLDER
    BASE_FOLDER = base_path
    STREAM_FOLDER = os.path.join(BASE_FOLDER, "stream")
    DATA_FOLDER = os.path.join(BASE_FOLDER, "data")
    STREAM_DATA_FOLDER = os.path.join(STREAM_FOLDER, "data")
    DLC_FOLDER = os.path.join(BASE_FOLDER, "dlc_files")
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(DLC_FOLDER, exist_ok=True)

def delete_invalid_manifests_and_lua(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file == 'fxmanifest.lua' or file == '__resource.lua':
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted invalid manifest/LUA: {file_path}")
                results_text.insert(tk.END, "Deleted invalid manifest/LUA: {file_path}")

def organize_meta_and_stream():
    os.makedirs(DATA_FOLDER, exist_ok=True)

    stream_folders = {name for name in os.listdir(STREAM_FOLDER) if os.path.isdir(os.path.join(STREAM_FOLDER, name))}
    stream_data_folders = {name for name in os.listdir(STREAM_DATA_FOLDER) if os.path.isdir(os.path.join(STREAM_DATA_FOLDER, name))} if os.path.exists(STREAM_DATA_FOLDER) else set()

    matching_folders = stream_folders & stream_data_folders

    for folder_name in matching_folders:
        car_stream_path = os.path.join(STREAM_FOLDER, folder_name)
        car_meta_path = os.path.join(STREAM_DATA_FOLDER, folder_name)
        car_data_path = os.path.join(DATA_FOLDER, folder_name)

        os.makedirs(car_data_path, exist_ok=True)

        for file_name in os.listdir(car_meta_path):
            if file_name.endswith(".meta"):
                shutil.move(os.path.join(car_meta_path, file_name), os.path.join(car_data_path, file_name))
            else:
                skipped_meta_files.append(os.path.join(car_meta_path, file_name))

        if not os.listdir(car_meta_path):
            os.rmdir(car_meta_path)

        delete_invalid_manifests_and_lua(car_stream_path)

        if 'dlc.rpf' in os.listdir(car_stream_path):
            dlc_folders.append(folder_name)
            dlc_rpf_path = os.path.join(car_stream_path, 'dlc.rpf')
            shutil.move(dlc_rpf_path, os.path.join(DLC_FOLDER, f"{folder_name}_dlc.rpf"))

    print("Meta files reorganized successfully!")
    results_text.insert(tk.END, "Meta files reorganized successfully!")

def handle_old_format():
    for folder_name in os.listdir(STREAM_FOLDER):
        car_path = os.path.join(STREAM_FOLDER, folder_name)

        if os.path.isdir(car_path):
            car_data_path = os.path.join(DATA_FOLDER, folder_name)
            car_meta_path = car_path

            os.makedirs(car_data_path, exist_ok=True)

            for file_name in os.listdir(car_meta_path):
                if file_name.endswith(".meta"):
                    shutil.move(os.path.join(car_meta_path, file_name), os.path.join(car_data_path, file_name))
                else:
                    skipped_meta_files.append(os.path.join(car_meta_path, file_name))

            for file_name in os.listdir(car_meta_path):
                if file_name.endswith(".meta"):
                    os.remove(os.path.join(car_meta_path, file_name))

            stream_subfolder_path = os.path.join(car_path, "stream")
            if os.path.exists(stream_subfolder_path) and os.path.isdir(stream_subfolder_path):
                for stream_file in os.listdir(stream_subfolder_path):
                    shutil.move(os.path.join(stream_subfolder_path, stream_file), os.path.join(car_path, stream_file))
                os.rmdir(stream_subfolder_path)

            delete_invalid_manifests_and_lua(car_path)

            if 'dlc.rpf' in os.listdir(car_path):
                dlc_folders.append(folder_name)
                dlc_rpf_path = os.path.join(car_path, 'dlc.rpf')
                shutil.move(dlc_rpf_path, os.path.join(DLC_FOLDER, f"{folder_name}_dlc.rpf"))

    print("Reorganized old format stream and meta files successfully!")
    results_text.insert(tk.END, "Reorganized old format stream and meta files successfully!")

def clean_empty_folders():
    for folder in [STREAM_FOLDER, STREAM_DATA_FOLDER]:
        if not os.path.exists(folder):
            print(f"Folder '{folder}' does not exist, skipping.")
            results_text.insert(tk.END, "Folder '{folder}' does not exist, skipping.")
            continue
        for car_folder in os.listdir(folder):
            car_path = os.path.join(folder, car_folder)
            if os.path.isdir(car_path) and not os.listdir(car_path):
                os.rmdir(car_path)

    print("Cleaned up empty folders.")
    results_text.insert(tk.END, "Cleaned up empty folders.")

def print_summary():
    print("\n--- Summary ---")
    results_text.insert(tk.END, "\n--- Summary ---\n")
    
    if skipped_meta_files:
        print("\nSkipped meta files (non-.meta files in meta folders):")
        results_text.insert(tk.END, "\nSkipped meta files (non-.meta files in meta folders):\n")
        for file in skipped_meta_files:
            folder_name = os.path.basename(os.path.dirname(file))
            file_name = os.path.basename(file)
            print(f"  - {folder_name}/{file_name}")
            results_text.insert(tk.END, f"  - {folder_name}/{file_name}\n")
    else:
        results_text.insert(tk.END, "No meta files were skipped.\n")

    if skipped_stream_folders:
        print("\nSkipped stream folders (empty or non-matching):")
        results_text.insert(tk.END, "\nSkipped stream folders (empty or non-matching):\n")
        for folder in skipped_stream_folders:
            print(f"  - {folder}")
            results_text.insert(tk.END, f"  - {folder}\n")
    else:
        print("No stream folders were skipped.")
        results_text.insert(tk.END, "No stream folders were skipped.\n")

    if dlc_folders:
        print("\n--- ***IMPORTANT: Folders with dlc.rpf (MUST BE FIXED)*** ---")
        results_text.insert(tk.END, "\n--- ***IMPORTANT: Folders with dlc.rpf (MUST BE FIXED)*** ---\n")
        for folder in dlc_folders:
            print(f"  - {folder} contains dlc.rpf and needs to be fixed!")
            results_text.insert(tk.END, f"  - {folder} contains dlc.rpf and needs to be fixed!\n")

        with open(DLC_TXT_FILE, "w") as dlc_file:
            for folder in dlc_folders:
                dlc_rpf_path = os.path.join(DLC_FOLDER, f"{folder}_dlc.rpf")
                dlc_file.write(f"{dlc_rpf_path}\n")
        print(f"Paths of dlc.rpf files have been saved to '{DLC_TXT_FILE}'.")
        results_text.insert(tk.END, f"Paths of dlc.rpf files have been saved to '{DLC_TXT_FILE}'.\n\n")
    else:
        print("No dlc.rpf folders were found.")
        results_text.insert(tk.END, "No dlc.rpf folders were found.\n")

def main():
    if os.path.exists(STREAM_FOLDER):
        if os.path.exists(STREAM_DATA_FOLDER):
            organize_meta_and_stream()
        else:
            print(f"No `data` folder found in `{STREAM_FOLDER}`, skipping meta reorganization.")
        
        handle_old_format()
        clean_empty_folders()
        print_summary()
    else:
        print(f"Stream folder '{STREAM_FOLDER}' does not exist. Nothing to process.")

def choose_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        update_folders(folder_selected)
        label_folder.config(text=f"Selected Folder: {folder_selected}")

def process_folder():
    if not BASE_FOLDER or not os.path.exists(STREAM_FOLDER):
        messagebox.showerror("Error", "Invalid base folder or no 'stream' folder found.")
        return

    organize_meta_and_stream()
    handle_old_format()
    clean_empty_folders()
    messagebox.showinfo("Success", "Processing completed successfully!")
    print_summary()

# Create the main GUI window
root = tk.Tk()
root.title("Vehicle Pack Organizer")
root.geometry("1200x700")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 1200
window_height = 700
x_coordinate = int((screen_width / 2) - (window_width / 2))
y_coordinate = int((screen_height / 2) - (window_height / 2))
root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

# Sun Valley theme
sv_ttk.set_theme("dark")

frame_folder = ttk.Frame(root)
frame_folder.pack(pady=10)

label_folder = tk.Label(frame_folder, text="No folder selected", wraplength=500)
label_folder.pack(side=tk.RIGHT)

button_choose = ttk.Button(frame_folder, text="Choose Folder", command=choose_folder)
button_choose.pack(side=tk.RIGHT, padx=10)

button_process = ttk.Button(root, text="Process Folder", command=process_folder)
button_process.pack(pady=20)

rpf_label = ttk.Label(root, text="RPF Finder:", font=('Arial', 16, 'bold'))
rpf_label.pack(pady=5)

rpf_frame = ttk.Frame(root)
rpf_frame.pack(pady=5)

rpf_text = scrolledtext.ScrolledText(rpf_frame, width=110, height=15, wrap=tk.WORD, font=('Arial', 12), bg='#111111', fg='white')
rpf_text.pack(padx=5, pady=5)

results_label = ttk.Label(root, text="Pack Results:", font=('Arial', 16, 'bold'))
results_label.pack(pady=5)

results_frame = ttk.Frame(root)
results_frame.pack(pady=5)

results_text = scrolledtext.ScrolledText(results_frame, width=110, height=15, wrap=tk.WORD, font=('Arial', 12), bg='#111111', fg='white')
results_text.pack(padx=5, pady=5)

apply_theme_to_titlebar(root)

root.mainloop()