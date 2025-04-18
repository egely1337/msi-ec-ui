#!/usr/bin/python3
# Made by Google Gemini
# Prompted by egely1337


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import subprocess
import threading
import time

def get_cooler_boost_status():
    """Gets the CoolerBoost status."""
    try:
        result = subprocess.run(["cat", "/sys/devices/platform/msi-ec/cooler_boost"], capture_output=True, text=True)
        return result.stdout.strip() == "on"
    except FileNotFoundError:
        print("CoolerBoost status not found.")
        return False

def get_battery_status():
    """Gets the Battery status."""
    try:
        start = subprocess.run(["cat", "/sys/class/power_supply/BAT1/charge_control_start_threshold"], capture_output=True, text=True)
        end = subprocess.run(["cat", "/sys/class/power_supply/BAT1/charge_control_end_threshold"], capture_output=True, text=True)
        
        if 60 == int(end.stdout.strip()) and 50 == int(start.stdout.strip()):
            return 0
        elif 80 == int(end.stdout.strip()) and 70 == int(start.stdout.strip()):
            return 1
        elif 100 == int(end.stdout.strip()) and 90 == int(start.stdout.strip()):
            return 2
    except FileNotFoundError:
        print("Battery status not found.")
        return False

def get_webcam_status():
    """Gets the Webcam status."""
    try:
        result = subprocess.run(["cat", "/sys/devices/platform/msi-ec/webcam"], capture_output=True, text=True)
        return result.stdout.strip() == "on"
    except FileNotFoundError:
        print("Webcam status not found.")
        return False

def toggle_cooler_boost(widget, data=None):
    """Toggles the CoolerBoost status."""
    if widget.get_active():
        subprocess.run(["sudo", "tee", "/sys/devices/platform/msi-ec/cooler_boost"], input="on".encode())
    else:
        subprocess.run(["sudo", "tee", "/sys/devices/platform/msi-ec/cooler_boost"], input="off".encode())

def toggle_webcam(widget, data=None):
    """Toggles the Webcam status."""
    if widget.get_active():
        subprocess.run(["sudo", "tee", "/sys/devices/platform/msi-ec/webcam"], input="on".encode())
    else:
        subprocess.run(["sudo", "tee", "/sys/devices/platform/msi-ec/webcam"], input="off".encode())

def set_battery_limit(widget, data=None):
    """Sets the battery charge limit."""
    selected_limit = widget.get_active_text()
    if selected_limit == "Best for Battery (%60)":
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_start_threshold"], input="50".encode())
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_end_threshold"], input="60".encode())
    elif selected_limit == "Best for Idle (%80)":
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_start_threshold"], input="70".encode())
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_end_threshold"], input="80".encode())
    elif selected_limit == "Best for Mobility (%100)":
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_start_threshold"], input="90".encode())
        subprocess.run(["sudo", "tee", "/sys/class/power_supply/BAT1/charge_control_end_threshold"], input="100".encode())

class MSIECWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="MSI-EC Control")
        self.set_default_size(640, 480)
        self.set_border_width(10)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.add(hbox)

        notebook = Gtk.Notebook()
        hbox.pack_start(notebook, True, True, 0)

        # General page (Fan Settings and Misc combined)
        general_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        general_page.set_border_width(10)
        notebook.append_page(general_page, Gtk.Label(label="General"))

        title_label = Gtk.Label(label="General Settings")
        general_page.pack_start(title_label, False, False, 5)
        title_label.set_halign(Gtk.Align.START)

        self.cooler_boost_checkbutton = Gtk.CheckButton(label="CoolerBoost")
        self.cooler_boost_checkbutton.connect("toggled", toggle_cooler_boost)
        general_page.pack_start(self.cooler_boost_checkbutton, False, False, 5)
        self.cooler_boost_checkbutton.set_halign(Gtk.Align.START)

        # Initialize CoolerBoost status
        self.cooler_boost_checkbutton.set_active(get_cooler_boost_status())

        self.webcam_checkbutton = Gtk.CheckButton(label="Webcam")
        self.webcam_checkbutton.connect("toggled", toggle_webcam)
        general_page.pack_start(self.webcam_checkbutton, False, False, 5)
        self.webcam_checkbutton.set_halign(Gtk.Align.START)

        # Initialize Webcam status
        self.webcam_checkbutton.set_active(get_webcam_status())

        # CPU temperature label
        self.cpu_temp_label = Gtk.Label(label="CPU Temp: %d C")
        general_page.pack_start(self.cpu_temp_label, False, False, 5)
        self.cpu_temp_label.set_halign(Gtk.Align.START)

        # CPU temperature update thread
        self.cpu_temp_thread = threading.Thread(target=self.update_cpu_temp, daemon=True)
        self.cpu_temp_thread.start()

        # Battery page
        battery_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        battery_page.set_border_width(10)
        notebook.append_page(battery_page, Gtk.Label(label="Battery"))

        battery_label = Gtk.Label(label="Battery")
        battery_page.pack_start(battery_label, False, False, 5)
        battery_label.set_halign(Gtk.Align.START)

        hbox_battery = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        battery_page.pack_start(hbox_battery, False, False, 5)

        battery_dropdown = Gtk.ComboBoxText()
        battery_dropdown.insert_text(0, "Best for Battery (%60)")
        battery_dropdown.insert_text(1, "Best for Idle (%80)")
        battery_dropdown.insert_text(2, "Best for Mobility (%100)")
        battery_dropdown.set_active(get_battery_status())
        battery_dropdown.connect("changed", set_battery_limit)
        hbox_battery.pack_start(battery_dropdown, True, True, 0) # Expand the dropdown to fill the available space.

    def update_cpu_temp(self):
        """Updates the CPU temperature."""
        while True:
            try:
                result = subprocess.run(["cat", "/sys/devices/platform/msi-ec/cpu/realtime_temperature"], capture_output=True, text=True)
                cpu_temp = int(result.stdout.strip())
                GLib.idle_add(self.update_cpu_temp_label, cpu_temp)
            except (FileNotFoundError, ValueError):
                pass
            time.sleep(2)

    def update_cpu_temp_label(self, cpu_temp):
        """CPU sıcaklık metnini günceller."""
        self.cpu_temp_label.set_text("CPU Temp: %d C" % cpu_temp)

window = MSIECWindow()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()