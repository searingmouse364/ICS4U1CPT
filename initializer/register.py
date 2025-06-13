"""
Date:
File Description: Registers .vault files on the host Windows machine
Name: Notorious LB
"""

import winreg, os

def register_file_type(ext, filetype_name, icon_path):

    USER_ROOT = winreg.HKEY_CURRENT_USER
    try:
        ## Registering icon with windows
        ext_key = winreg.CreateKey(USER_ROOT, fr"Software\Classes\{ext}") ## Creating extension key at the user level
        winreg.SetValue(ext_key, '', winreg.REG_SZ, filetype_name)
        winreg.CloseKey(ext_key)
        
        type_key = winreg.CreateKey(USER_ROOT, fr"Software\Classes\{filetype_name}") ## Associating the name "Vault" with extension ".vault"
        winreg.SetValue(type_key, '', winreg.REG_SZ, f"{filetype_name} File")
        icon_key = winreg.CreateKey(type_key, "DefaultIcon") ## Associating proper icon with file type
        icon_abs = os.path.abspath(icon_path)
        winreg.SetValue(icon_key, '', winreg.REG_SZ, f'"{icon_abs}"')
        
        winreg.CloseKey(icon_key)
        winreg.CloseKey(type_key)

        print(f"Registered {ext} with icon {os.path.abspath(icon_path)} at user level.")

    except Exception as e:
        print(f"Failed to register file type: {e}")

