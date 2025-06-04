import sys, subprocess
import tkinter as tk
from importlib.metadata import distributions
from tkinter import messagebox

__all__ = ["safeguard"]

def __show_warning(text, uninstalled):
    if __name__ != "__main__":
        raise Exception("Do not import")
    
    result = messagebox.askyesno("Warning", text)
    if result:
        for package, package_ver in uninstalled:
            subprocess.run(f"pip install {package}=={package_ver}", shell=True)
    else:
        sys.exit(1)
    root = tk.Tk()
    root.withdraw() 

def verify_requirements():
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
        __show_warning("".join(warnings) + "Do you want to install them?", uninstalled)
