"""
Date:
File Description:
Name: Notorious LB
"""
import os, pickle, struct
from typing import Callable


class File:

    @staticmethod
    def NO_INIT_ACTION():
        """
        Used to nullify the File().__init__ default and alternative actions, does nothing and returns nothing.\n
        Potentially dangerous, use with caution. 
        """
        pass    

    def __init__(self, path, def_content : str = "", alt_action: Callable[[any], any] | None = None, *args, **kwargs):
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
                    f.write(def_content)

        self._location = path
        self._name = os.path.basename(path)

    def read_bytes(self):
        with open(self._location, "rb") as f:
            return f.read()

    def write_bytes(self, bytes: bytes):
        with open(self._location, "wb") as f:
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

    def get_name(self):
        return self._name

    def get_location(self):
        return self._location
    
    ###def __del__(self):
    ###    os.remove(self._location)

class Vault(File):
    def __init__(self, name: str):
        """
        Initializer for vaults

        params:
            - name - Name of the vault, file extension ".vault" added automatically
            - create - specifies whether or not to create a new vault, or to find an existing one. It is true by default.

        
        Each vault contains an 20 byte footer which includes:
            - A 4 byte magic number that identifies it as a vault
            - An 8 byte big-endian unsigned integer which offsets to the pointer table
            - An 8 byte number which describes the length of the pointer table
        
        Upon creating a new vault, the initializer will:
            - write the 20 byte footer with the magic number with 20 as the offset to the pointer table

        """
        super().__init__(f"{name}.vault", alt_action = File.NO_INIT_ACTION)
        ## Magic is used to sign the file as a .vault file
        ## It is 4 bytes long
        self.__magic = 'VULT'
        if not os.path.isfile(f"{name}.vault"):
            self.__pointer_table = []
            ## The param ">I" specifies that it is an unsigned integer in the big-endian format
            ## Setting up the footer in the order mentioned above, length of the pointer table is determined
            ## After serialization of the list. Also, the offset is counted from the end of the file
            ## Because this makes computation easier
            length_of_table = len(pickle.dumps(self.__pointer_table))
            self.__footer = self.__magic, 20 + length_of_table, length_of_table
            self.__length = 20 + length_of_table

        else:
            self.__footer = self.get_footer()
            ## Validate that the file is in fact a vault file
            if self.__footer[0] != self.__magic:
                raise ValueError("File is not a vault file")
            ## Get length of the vault
            self.__pointer_table = self.get_pointer_table_from_file()
            print(self.__pointer_table)

            ## Clears the pointer table and header from file
            with open(self._location, "r+b") as f:
                f.seek(-self.__footer[1], 2)
                f.truncate() 

            self.__length = len(self.read_bytes())
            print(self.__length)

    def append_footer(self):
        with open(self._location, "ab") as f:
            f.write(self.__footer[0].encode("utf-8"))
            f.write(struct.pack(">Q", self.__footer[1]))
            f.write(struct.pack(">Q", self.__footer[2]))

    def append_bytes(self, content) -> int:
        """
        Appends content in byte-form to the vault

        Returns total length of bytes appended
        """
        new_content = pickle.dumps(content)
        with open(self._location, "ab") as f:
            f.write(new_content)
        return len(new_content)

    def get_footer(self) -> tuple[str, int, int]:
        """
        Returns the footer in the form of a tuple.

        - First index describes the magic number
        - Second index describes the offset to the pointer table
        - Third index describes the length of the pointer table
        """
        with open(self._location, "rb") as f:
            f.seek(-20, 2) # Move to the start of the footer
            magic, offset, length = f.read(4), f.read(8), f.read(8) 
            offset = struct.unpack('>Q', offset)[0]
            length = struct.unpack('>Q', length)[0]            
        return magic.decode("utf-8"), offset, length
    
    def __update_footer(self):
        length_of_table =len(pickle.dumps(self.__pointer_table))
        self.__footer = self.__magic, length_of_table + 20, length_of_table

    def get_pointer_table_from_file(self) -> list[tuple[str, int, int]]:
        offset = -self.__footer[1] ## Negative offset because calculating offset from the end of the file is easier
        length = self.__footer[2] ## Length remains positive
        with open(self._location, "rb") as f:
            f.seek(offset, 2)
            pickled_pointer_table = f.read(length)
        return pickle.loads(pickled_pointer_table)
    
    def get_pointer_table(self) -> list[tuple[str, int, int]]:
        return self.__pointer_table

    def __add_new_pointer(self, name: str, offset: int, length: int):
        self.__pointer_table.append((name, offset, length))


    def capture(self, file: File):
        #Makes sure the specified file is not the vault file itself
        if file.get_name() == self._name:
            raise Exception("Vault cannot capture itself")
        contents = file.read_bytes() #Gets the byte data of given file
        len_contents = self.append_bytes(contents) #Appends data to the vault, returning length of total appended data
        self.__add_new_pointer(file.get_name(), self.__length, len_contents)
        len_pointer_table = len(pickle.dumps(self.__pointer_table)) #New length of the pointer table
        self.__update_footer() #Updating the footer
        self.__length += len_contents + len_pointer_table + 20 #Updating the length of the vault
        os.remove(file.get_location())
    
    def file_exists(self, file_name : str) -> tuple[bool, int | None, int | None]:
        """
        Linear search
        Checks if a file exists through the pointer table

        params:
            - file_name - name of the file with the extension

        - If it does, it returns True, the offset and the length
        - Otherwise, it returns False, None and None


        """

        for pointer in self.__pointer_table:
            name, offset, length = pointer[0], pointer[1], pointer[2]
            if name != file_name:
                continue
            return True, offset, length
        return False, None, None

    def release(self, file_name: str) -> bool:
        does_file_exist = self.file_exists(file_name)
        if does_file_exist[0]:
            with open(self._location, "rb") as f:
                f.seek(does_file_exist[1], 0)
                data = pickle.loads(f.read(does_file_exist[2]))
            released_file = File(file_name)
            released_file.write_bytes(data)

            for index, pointer in enumerate(self.__pointer_table):
                if pointer[0] == file_name:
                    self.__pointer_table.pop(index)
                    break
            return True
        return False
    
    def __del__(self): ## Writes updated pointer table to vault when self is cleared from RAM
        print(self.__length)
        self.append_bytes(self.__pointer_table)
        self.__update_footer()
        self.append_footer()