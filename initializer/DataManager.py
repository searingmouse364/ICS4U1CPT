"""
Date:
File Description: Model for managing app data
Name: Notorious LB
"""

import sys
import os

sys.path.insert(1, os.getcwd()) # Allows importation of File
from fileUtilities.file import File
from fileUtilities.exceptions import DataError

class DataManager(File):

    """
    class used to manage stored data / settings regarding the app
    
    """
    data_path = os.getcwd() + r"\.dat"
    location = data_path +  r"\dat.dat"

    def __init__(self):
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path) ## Creates data_path directory on first launch or if it was deleted by the user
        super().__init__(self.location)
        vars = [var.strip().split("==") for var in super().readlines()] # Get vars from self, vars are in tuples of (key, value)
        self.VARS = {}
        if len(vars) > 0:
            for KEY, VALUE in vars:
                self.VARS[KEY] = VALUE

    def add_var(self, key, value):
        if key in self.VARS.keys():
            raise DataError("Can't add a variable that already exists. Try using self.edit_var(key, value) instead")
        
        FORMAT = f"{key}=={value}\n"
        super().append(FORMAT)
        self.VARS[key] = value

    def edit_var(self, key, value):
        if not self.VARS.get(key):
            raise DataError(f"Variable {key} cannot be changed because it does not exist. Try using self.add_var(key, value) instead")

        self.VARS[key] = value
        super().write_bytes(b"") # Hack to clear the file
        for key in self.VARS.keys():
            FORMAT = f"{key}=={self.VARS[key]}\n"
            super().append(FORMAT)
                
    def read_var(self, key) -> str:
        return self.VARS.get(key)
