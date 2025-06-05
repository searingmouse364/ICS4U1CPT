import subprocess
import tkinter as tk
from importlib.metadata import distributions
from tkinter import messagebox


def verify_requirements():
    def __show_warning(text, uninstalled):
    
        result = messagebox.askyesno("Missing Requirements", text)
        if result:
            for package, package_ver in uninstalled:
                subprocess.run(f"pip install {package}=={package_ver}", shell = True)

        root = tk.Tk()
        root.withdraw() 

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
