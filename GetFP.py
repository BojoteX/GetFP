# Flight Plan Downloader by Bojote
# To create .exe file run:
# pyinstaller --onefile --windowed --version-file=version.txt --icon=fp_small.ico --add-data "fp_small.ico;." --distpath C:\Tools\GetFP GetFP.py

import sys
import os
import configparser
import tkinter as tk
import requests
import json
import shutil
import re
from lxml import etree
from pathlib import Path
from tkinter import simpledialog, messagebox

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Initialize the root window
root = tk.Tk()
root.withdraw()  # Hide the root window, if you don't want it to be visible

icon_path = resource_path('fp_small.ico')
root.iconbitmap(icon_path)

def show_message(title, message):
    msg_window = tk.Toplevel(root)
    msg_window.title(title)

    # Set the icon using the resource_path
    icon_path = resource_path('fp_small.ico')
    msg_window.iconbitmap(icon_path)

    # Set the window to be always on top
    msg_window.attributes('-topmost', 1)

    # Setup the message and button within the window
    message_label = tk.Message(msg_window, text=message, padx=20, pady=20, width=300)  # Adjust width as needed
    message_label.pack()
    button = tk.Button(msg_window, text="OK", command=msg_window.destroy)
    button.pack(pady=10)

    # Set the size of the window and center it
    window_width = 400  # Adjust size as needed
    window_height = 150  # Adjust size as needed
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coordinate = int((screen_width/2) - (window_width/2))
    y_coordinate = int((screen_height/2) - (window_height/2))
    msg_window.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

    # Make dialog modal and force focus
    msg_window.grab_set()
    msg_window.focus_force()
    msg_window.wait_window()

def validate_username(username):
    # Validates username by checking if a network fetch succeeds.
    json_url = f"https://www.simbrief.com/api/xml.fetcher.php?username={username}&json=v2"
    response = requests.get(json_url)
    if response.status_code == 200:
        return username
    else:
        return None

def get_user_input(prompt, custom_width=400, custom_height=150, entry_width=30):
    def on_ok():
        nonlocal input_value
        validated_username = validate_username(entry.get())
        if validated_username:
            input_value = validated_username
            dialog.destroy()
        else:
            show_message("Invalid Username", "The username entered is not valid. Please try again.")
            # messagebox.showerror("Invalid Username", "The username entered is not valid. Please try again.")
            entry.delete(0, tk.END)  # Clear the entry widget for new input

    def on_cancel():
        nonlocal input_value
        input_value = None  # Or set to a default value indicating cancellation
        dialog.destroy()

    input_value = None  # Default value to indicate no input or cancellation
    
    dialog = tk.Toplevel(root)
    icon_path = resource_path('fp_small.ico')
    dialog.iconbitmap(icon_path)
    dialog.title("GetFP")

    # Apply initial dimensions and center the window initially
    dialog.geometry("+0+0")

    # Create dialog content
    label = tk.Label(dialog, text=prompt, wraplength=custom_width - 20)
    label.pack(pady=(10, 0))  # Padding at the top only

    # Determine the width of the entry based on the optional parameter or default to 50
    if entry_width is None:
        entry_width = int(custom_width / 8)  # Default based on custom_width

    entry = tk.Entry(dialog, width=entry_width)
    entry.pack(pady=(10, 20))  # Padding above and below

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=(0, 10))  # Padding at the bottom only
    ok_button = tk.Button(button_frame, text="OK", command=on_ok)
    ok_button.pack(side=tk.LEFT, padx=(10, 20), expand=True)
    cancel_button = tk.Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, expand=True)

    dialog.attributes('-topmost', 1)  # Ensure the dialog stays on top
    dialog.grab_set()  # Make the dialog modal
    dialog.focus_force()  # Force the dialog to take focus

    dialog.update_idletasks()  # Update the dialog to calculate its size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate window size dynamically or use custom values
    window_width = custom_width
    window_height = dialog.winfo_reqheight() if custom_height is None else custom_height

    x_coordinate = int((screen_width/2) - (window_width/2))
    y_coordinate = int((screen_height/2) - (window_height/2))
    dialog.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)  # Handle window close (X) button click
    dialog.wait_window(dialog)  # Wait for the dialog to close before moving on

    return input_value
    
# Function to safely check path existence including symlinks
def safe_path_exists(path):
    try:
        # Directly check for existence without resolving the path
        return path.exists()
    except OSError as e:
	# Log or handle the error here if needed
        show_message("Error", f"{path} is not accesible. Delete directory or reinstall MSFS. This could also be due to permissions or a Symbolic link. Will exit now.") 
        sys.exit(1)  # Exit the script if not found

# Paths to check for MSFS
ms_store_path = Path(os.getenv('LOCALAPPDATA')) / "Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalState"
steam_path = Path(os.getenv('APPDATA')) / "Microsoft Flight Simulator"

# Check for Microsoft Flight Simulator installation
PlanSaveLocation = None  # Initialize with None to check if set later

if safe_path_exists(steam_path) and safe_path_exists(ms_store_path):
    PlanSaveLocation = None
    show_message("Error", "Both Steam and MS Store versions are installed. This program requires only one version installed.")  
    sys.exit(1)  # Exit the script if not found  
elif safe_path_exists(steam_path):
    PlanSaveLocation = steam_path
elif safe_path_exists(ms_store_path):
    PlanSaveLocation = ms_store_path

if PlanSaveLocation is None:
    show_message("Error", "Microsoft Flight Simulator not found.")
    sys.exit(1)  # Exit the script if not found

def get_settings_from_ini():
    config = configparser.ConfigParser()
    # Construct the full path to the INI file
    ini_path = os.path.join(os.getenv('APPDATA'), 'GetFP', 'GetFP.ini')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(ini_path), exist_ok=True)
    # Define default settings
    defaults = {
        'SimBriefUser': None,  # This will be prompted for if not found
        'FileName': 'LAST.PLN',  # Default flight plan name
        'Include_SID_STAR': '1',  # Default setting for SID/STAR inclusion
        'Delete_CustomFlight': '0'  # Default setting for Deleting the CustomFlight.FLT and PLN files
    }

    if config.read(ini_path) and 'Settings' in config:
        settings = {key: config['Settings'].get(key, defaults[key]) for key in defaults}
    else:
        settings = defaults
        # Use get_user_input to prompt for SimBrief username if not found in ini
        user_input = get_user_input("Enter your SimBrief username:")
        if user_input:
            settings['SimBriefUser'] = user_input
        else:
            show_message("Error", "No SimBrief username provided.")
            sys.exit(1)
    return settings

def save_settings_to_ini(settings):
    config = configparser.ConfigParser()
    config['Settings'] = settings
    ini_path = os.path.join(os.getenv('APPDATA'), 'GetFP', 'GetFP.ini')
    # Ensure the directory exists
    os.makedirs(os.path.dirname(ini_path), exist_ok=True)
    # Write settings to the specified INI file path
    with open(ini_path, 'w') as configfile:
        config.write(configfile)

settings = get_settings_from_ini()

# Get the SimBrief username from the ini file
SimBriefUser = settings['SimBriefUser']

if settings['Include_SID_STAR'] == '1':
    FlightPlanName = "FS2020"
else: 
    FlightPlanName = "FS2020 (No SID/STAR)"

# Basic Data
PlanSaveName = settings['FileName']
CustomFlightLocation = f"{PlanSaveLocation}\\MISSIONS\\Custom"
json_url = f"https://www.simbrief.com/api/xml.fetcher.php?username={SimBriefUser}&json=v2"

# Use correct headers to be able to fetch data
headers = {
    'User-Agent': 'GetFP v1.0',
}
     
def fetch_pln_url():

    if settings['Delete_CustomFlight'] == '1':
        try:
            shutil.rmtree(CustomFlightLocation)
        except FileNotFoundError:
            pass  # Directory does not exist, or has already been deleted, do nothing.
        except Exception as e:
            show_message("Error", f"Error occurred while trying to delete directory: {CustomFlightLocation}")
        
    # Fetch the JSON data
    response = requests.get(json_url, headers=headers)
    if response.status_code == 200:
        data = response.json()

        # Save the provided username to INI for future use
        save_settings_to_ini(settings)

        # Search for GATE in the remarks
        remarks_list = data['general']['dx_rmk']  # This is now understood to be a list.

        # Adjusted regex pattern to capture letter and number separately
        gate_pattern = r"(GATE|PARKING)\s*([A-Z]?)(\s?\d+)"

        normalized_gate = ""
        for remark in remarks_list:
            match = re.search(gate_pattern, remark)
            if match:
                location, letter, number = match.groups()
                # Normalize to ensure a space between letter and number, if letter is present
                if letter:
                    normalized_gate = f"{location} {letter} {number.strip()}"
                else:
                    normalized_gate = f"{location} {number.strip()}"
                break  # Exit the loop after finding the first match
        
        if not normalized_gate:
            show_message("Success", "Gate information not found.")
            
        directory_url = data['files']['directory']
        for file in data['files']['file']:
            if file['name'] == FlightPlanName:
                pln_relative_url = file['link']
                return directory_url + pln_relative_url, normalized_gate
    else:
        show_message("Error", "Invalid Username.")
        sys.exit(1)  # Exit the script if not found    
    return None

def download_file(pln_url, normalized_gate):
    response = requests.get(pln_url, headers=headers)
    if response.status_code == 200:
        # Parse the XML content using lxml
        root = etree.fromstring(response.content)

        # Use lxml to remove specific elements as needed
        for elem in root.xpath('.//RunwayNumberFP | .//RunwayDesignatorFP | .//DepartureFP | .//ArrivalFP'):
            elem.getparent().remove(elem)

        # Retrieve DepartureName for display
        departure_name_element = root.find('.//FlightPlan.FlightPlan/DepartureName')
        departure_name = departure_name_element.text if departure_name_element is not None else "Unknown Departure"

        if normalized_gate:  # Check if normalized_gate is not empty    
            # Create the DeparturePosition element
            departure_position_element = etree.Element('DeparturePosition')
            departure_position_element.text = normalized_gate
            departure_position_element.tail = '\n\t'  # Ensure a newline follows the element

            if departure_name_element is not None:
                # Find the index of DepartureName in its parent's children
                parent = departure_name_element.getparent()
                index = parent.index(departure_name_element)

                # Insert DeparturePosition right after DepartureName
                parent.insert(index, departure_position_element)

        # Define the path and file where to save the modified .pln file
        file_path = f"{PlanSaveLocation}\\{PlanSaveName}"

        # Write the modified contents back to the file, pretty-printed
        with open(file_path, 'wb') as file:
            file.write(etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
            if normalized_gate:
                show_message("Success", f"Flight Plan downloaded. Just load {PlanSaveName} to start your flight at {normalized_gate} from {departure_name}. If resuming a Flight (with FSAutoSave) load LAST.FLT instead")
            else:
                show_message("Success", f"Flight Plan downloaded. Just load {PlanSaveName} to start your flight in {departure_name}. If resuming a Flight (with FSAutoSave) load LAST.FLT instead")
    else:
        show_message("Error", f"Failed to download the file. Status code: {response.status_code}")

if __name__ == "__main__":
    pln_url, normalized_gate = fetch_pln_url()
    if pln_url:
        download_file(pln_url, normalized_gate)
    else:
        show_message("Error", "Failed to fetch the PLN file URL.")
