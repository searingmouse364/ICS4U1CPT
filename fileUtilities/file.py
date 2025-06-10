"""
Date:
File Description: File wrapper class
Name: Notorious LB
"""
import os, zlib ## Had to replace my own compression and decompression algorithms with zlib because they sucked
from typing import Callable


class File:

    @staticmethod
    def NO_INIT_ACTION():
        """
        Used to nullify the File().__init__ default and alternative actions, does nothing and returns nothing.\n
        Potentially dangerous, use with caution. 
        """
        pass 

    @staticmethod
    def compress(data: bytes) -> bytes: ## Hopefully I will write my own later
        """
        Compression algorithm 
        """
        return zlib.compress(data)

    @staticmethod
    def decompress(data: bytes) -> bytes: ## Hopefully I will write my own later
        """
        Decompression algorithm 
        """
        return zlib.decompress(data)  

    def __init__(self, path, default_content : str = "", alt_action: Callable[[any], any] | None = None, *args, **kwargs):
        """
        File handler

        params:
            - path - path to file
            - def_content - default content to write upon file creation
            - alt_action - alternative action to be done if file is not found, default action creats an empty file with the provided path
            - *args - args for alt_action
            - **kwargs - kwargs for alt_action
        
        To do nothing if no file is found, pass File.NO_INIT_ACTION into alt_action
        
        """
        if not os.path.isfile(path):
            if alt_action:
                alt_action(*args, **kwargs)
            else:
                with open(path, "w") as f:
                    f.write(default_content)

        self._location = path
        self._name = os.path.basename(path)

    def read_bytes(self) -> bytes:
        with open(self._location, "rb") as f:
            return f.read()

    def write_bytes(self, bytes: bytes):
        with open(self._location, "wb") as f:
            return f.write(bytes)
    
    def append_bytes(self, bytes: bytes):
        with open(self._location, "ab") as f:
            return f.write(bytes)

    def read(self):
        with open(self._location, "r") as f:
            return f.read()

    def write(self, string: str):
        with open(self._location, "w") as f:
            f.write(string)

    def append(self, string: str):
        with open(self._location, "a") as f:
            f.write(string)

    def readlines(self):
        with open(self._location, "r") as f:
            return f.readlines()

    def get_name(self):
        return self._name

    def get_location(self):
        return self._location
    