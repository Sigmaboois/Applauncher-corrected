import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import winreg
import subprocess
import sys
import threading
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "startup_apps.json"
REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REGISTRY_PREFIX = "MyStartupApp_"

class StartupAppManager:
    def __init__(self, master, autorun=False):
        self.master = master
        self.apps = []
        self.autorun = autorun
        self.tray_icon = None
        self.load_config()

        if self.autorun:
            self.launch_all_apps()
            self.show_tray_icon()
            return

        master.title("Startup App Selector")
        master.geometry("500x300")

        self.listbox = tk.Listbox(master, selectmode=tk.SINGLE, width=70)
        self.listbox.pack(pady=10)

        self.browse_button = tk.Button(master, text="Add App", command=self.add_app)
        self.browse_button.pack()

        self.remove_button = tk.Button(master, text="Remove Selected", command=self.remove_selected)
        self.remove_button.pack(pady=5)

        self.save_button = tk.Button(master, text="Save & Enable on Startup", command=self.save_and_register)
        self.save_button.pack(pady=10)

        self.refresh_listbox()

    def browse_file(self):
        return filedialog.askopenfilename(
            title="Select an Application",
            filetypes=[("Executables", "*.exe")]
        )

    def add_app(self):
        file_path = self.browse_file()
        if file_path and file_path not in self.apps:
            self.apps.append(file_path)
            self.refresh_listbox()

    def remove_selected(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            del self.apps[index]
            self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for app in self.apps:
            self.listbox.insert(tk.END, app)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.apps = json.load(f)

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.apps, f)

    def clean_registry_entries(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS)
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    if name.startswith(REGISTRY_PREFIX):
                        winreg.DeleteValue(key, name)
                    else:
                        i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to clean registry entries: {e}")

    def register_apps_in_registry(self):
        self.clean_registry_entries()
        for i, app in enumerate(self.apps):
            name = f"{REGISTRY_PREFIX}{i}"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE)
                command = f'"{sys.executable}" "{os.path.abspath(__file__)}" --autorun'
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
            except Exception as e:
                messagebox.showerror("Error", f"Registry error: {e}")

    def launch_all_apps(self):
        for app in self.apps:
            try:
                subprocess.Popen(app)
            except Exception as e:
                print(f"Failed to launch {app}: {e}")

    from PIL import Image

def show_tray_icon(self):
    image = Image.open("icon.ico")
    menu = pystray.Menu(pystray.MenuItem("Exit", self.exit_tray))
    self.tray_icon = pystray.Icon("StartupApp", image, "Startup App Auto-Run", menu)

    def run_icon():
        self.tray_icon.run()

    threading.Thread(target=run_icon, daemon=True).start()


    def exit_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        sys.exit()

    def create_icon(self):
        image = Image.new("RGB", (64, 64), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="white")
        return image

    def save_and_register(self):
        self.save_config()
        self.register_apps_in_registry()
        self.launch_all_apps()
        messagebox.showinfo("Success", "Apps saved and launched!")

if __name__ == "__main__":
    autorun_flag = "--autorun" in sys.argv
    root = tk.Tk()
    app = StartupAppManager(root, autorun=autorun_flag)
    if not autorun_flag:
        root.mainloop()
