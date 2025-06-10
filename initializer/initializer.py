"""
Date:
File Description: Pre-launch checklist
Name: Notorious LB
"""


import subprocess, sys, os


try: ## Make sure that tkinter is available 
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from importlib.metadata import distributions
from .register import register_file_type
from .DataManager import DataManager



def init():
    def verify_requirements():
        def __show_warning(text, uninstalled):
            if TKINTER_AVAILABLE:
                result = messagebox.askyesno("Missing Requirements", text)
                if result:
                    for package, package_ver in uninstalled:
                        subprocess.run([sys.executable, "-m", "pip", "install", f"{package}=={package_ver}"])

                root = tk.Tk()
                root.withdraw()
            else:
                result = input(text + " (Y/n) ").lower()
                while result != "y" and result != "n":
                    print(f'Your response "{result}" was not one of the expected responses "(Y/n)"')
                    result = input(text + " (Y/n) ").lower()
                if result == "y":
                    for package, package_ver in uninstalled:
                        subprocess.run([sys.executable, "-m", "pip", "install", f"{package}=={package_ver}"])


        with open("requirements.txt", "r") as f:
            packages = [(parts[0], parts[1].strip()) 
                        for line in f if (parts := line.split("==")) and len(parts) == 2]

        installed = {dist.metadata["Name"].lower(): dist.version for dist in distributions()}
        warnings = []
        uninstalled = []
        for name, version in packages:
            key = name.lower()
            if key not in installed:
                warnings.append(f"{name} is not installed\n")
                uninstalled.append((name, version))
            elif installed[key] != version:
                warnings.append(f"{name} has version {installed[key]} instead of {version}\n")
                uninstalled.append((name, version))

        if len(warnings) > 0:
            msg = "".join(warnings) + "Do you want to install them?" if len(warnings) > 1 else "".join(warnings) + "Do you want to install it?"
            __show_warning(msg, uninstalled)

    data_manager = DataManager()
    registered = data_manager.read_var("REGISTERED")
    if not registered or registered == "False": ## Checks if REGISTERED exists or if it's false
        register_file_type('.vault', 'Vault', os.getcwd() + r'\GUI\vault_icon.ico')
        try:
            data_manager.add_var("REGISTERED", "True")
        except Exception:
            data_manager.edit_var("REGISTERED", "True")

    verify_requirements()
