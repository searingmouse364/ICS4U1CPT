"""
Date:
File Description: 7Zip clone
Name: Notorious LB
"""

from fileUtilities.file import File
from fileUtilities.vault import Vault


new_vault = Vault("new_vault")
print("Vault initialized!")
while True:
    print(new_vault.get_pointer_table())
    command = input("Select a command, exit, capture, release: ").lower().strip()
    if command == "capture":
        file_name = input("Input the name of the file you'd like to capture: ").strip()
        new_vault.capture(File(file_name, create=False))
        print(f"Successfully captured {file_name}")
    elif command == "release":
        if len(new_vault.get_pointer_table()): 
            print(' '.join(i for i in new_vault.get_pointer_table().keys()))
        else:
            print("No captured files")
            continue
        file_name = input("Input the name of the file you'd like to release: ").strip().strip('"')
        success = new_vault.release(file_name)
        if success:
            print(f"Successfully released {file_name}")
        else:
            print("Uh Oh")
    else:
        print("Goodbye!")
        break