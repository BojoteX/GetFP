# Flight Plan Downloader by Bojote
# To create .exe file run:
# pyinstaller --onefile --windowed --version-file=version.txt --icon=fp_small.ico --add-data "fp_small.ico;." GetFP.py

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
    messagebox.showinfo(title, message, parent=root)

def get_user_input(prompt):
    def on_ok():
        nonlocal input_value
        input_value = entry.get()
        dialog.destroy()

    def on_cancel():
        nonlocal input_value
        input_value = None  # Or set to a default value indicating cancellation
        dialog.destroy()

    input_value = None  # Default value to indicate no input or cancellation
    dialog = tk.Toplevel(root)
    dialog.iconbitmap(icon_path)
    dialog.title("GetFP")
    dialog.geometry("240x120")  # Adjust size as needed
    dialog.grab_set()  # Make dialog modal

    tk.Label(dialog, text=prompt).pack(pady=10)
    entry = tk.Entry(dialog)
    entry.pack(pady=5)
    entry.bind("<Return>", lambda event: on_ok())

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=5)
    ok_button = tk.Button(button_frame, text="OK", command=on_ok)
    ok_button.pack(side=tk.LEFT, padx=(0,10))
    cancel_button = tk.Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)  # Handle window close (X) button click

    dialog.wait_window(dialog)  # Wait for the dialog to close before moving on

    return input_value
    
# Paths to check for MSFS
ms_store_path = Path(os.getenv('LOCALAPPDATA')) / "Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe"
steam_path = Path(os.getenv('APPDATA')) / "Microsoft Flight Simulator"

# Check for Microsoft Flight Simulator installation
PlanSaveLocation = None  # Initialize with None to check if set later
if ms_store_path.exists():
    PlanSaveLocation = ms_store_path
elif steam_path.exists():
    PlanSaveLocation = steam_path

if PlanSaveLocation is None:
    show_message("Error", "Microsoft Flight Simulator not found.")
    sys.exit(1)  # Exit the script if not found

def get_settings_from_ini():
    config = configparser.ConfigParser()
    ini_path = 'GetFP.ini'
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
    with open('GetFP.ini', 'w') as configfile:
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
            match = re.search(location, gate_pattern, remark)
            if match:
                letter, number = match.groups()
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

        if normalized_gate:  # Check if normalized_gate is not empty    
            # Find the DepartureName element within FlightPlan.FlightPlan
            departure_name_element = root.find('.//FlightPlan.FlightPlan/DepartureName')
            if departure_name_element is not None:
                # Create the DeparturePosition element
                departure_position_element = etree.Element('DeparturePosition')
                departure_position_element.text = normalized_gate
                departure_position_element.tail = '\n\t'  # Ensure a newline follows the element
            
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
                show_message("Success", f"Flight Plan downloaded. Just load {PlanSaveName} to start your flight at {normalized_gate}.")
            else:
                show_message("Success", f"Flight Plan downloaded. Just load {PlanSaveName} to start your flight.")
    else:
        show_message("Error", f"Failed to download the file. Status code: {response.status_code}")

if __name__ == "__main__":
    pln_url, normalized_gate = fetch_pln_url()
    if pln_url:
        download_file(pln_url, normalized_gate)
    else:
        show_message("Error", "Failed to fetch the PLN file URL.")
