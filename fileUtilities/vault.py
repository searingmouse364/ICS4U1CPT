"""
Date:
File Description: Vault class
Name: Notorious LB
"""
import os, pickle, struct
from fileUtilities.file import File
from fileUtilities.exceptions import VaultError

class Vault(File):
    def __init__(self, path: str):
        """
        Initializer for vaults

        params:
            - name - Name of the vault, file extension ".vault" added automatically
            - create - specifies whether or not to create a new vault, or to find an existing one. It is true by default.

        
        Each vault contains an 28 byte footer which includes:
            - A 4 byte magic number that identifies it as a vault
            - An 8 byte big-endian unsigned integer which offsets to the pointer table
            - An 8 byte number which describes the length of the pointer table
            - An 8 byte number storing the size of the vault (excluding the footer)
        
        Upon creating a new vault, the initializer will:
            - write the 28 byte footer

        """
        super().__init__(path, alt_action = File.NO_INIT_ACTION)
        ## Magic is used to sign the file as a .vault file
        ## It is 4 bytes long
        self.__magic = 'VULT'
        if not os.path.isfile(path):
            self.__pointer_table : dict[str, list[tuple[int, int]]] = {"?empty": []} # Key is called ?empty, because file names in windows cannot contain "?".
            # Therefore, this avoids potential conflicts. Better solution to come.
            self.__length = 0
            # Setting up the footer in the order mentioned above, length of the pointer table is determined
            # After serialization of the list. Also, the offset is counted from the end of the file
            # Because this makes computation easier
            length_of_table = len(pickle.dumps(self.__pointer_table))
            self.__footer = self.__magic, 28 + length_of_table, length_of_table, self.__length
            
        else:
            self.__footer = self.get_footer()
            ## Validate that the file is in fact a vault file
            if self.__footer[0] != self.__magic:
                raise ValueError("File is not a vault file")

            self.__pointer_table = self.get_pointer_table_from_file()

            ## Clears the pointer table and header from file
            with open(self._location, "r+b") as f:
                f.seek(-self.__footer[1], 2)
                f.truncate() 

            ## Get length of the vault
            self.__length = self.__footer[3]

    def append_footer(self):
        with open(self._location, "ab") as f:
            f.write(self.__footer[0].encode("utf-8"))
            f.write(struct.pack(">Q", self.__footer[1]))
            f.write(struct.pack(">Q", self.__footer[2]))
            f.write(struct.pack(">Q", self.__footer[3]))

    def get_footer(self) -> tuple[str, int, int]:
        """
        Returns the footer in the form of a tuple.

        - First index describes the magic number
        - Second index describes the offset to the pointer table
        - Third index describes the length of the pointer table
        - Fourth index describes the length of the vault (excluding footer)
        """
        with open(self._location, "rb") as f:
            f.seek(-28, 2) # Move to the start of the footer
            magic, offset, length_pointer, length = f.read(4), f.read(8), f.read(8), f.read(8) 
            offset = struct.unpack('>Q', offset)[0]
            length_pointer = struct.unpack('>Q', length_pointer)[0]
            length = struct.unpack('>Q', length)[0]            
        return magic.decode("utf-8"), offset, length_pointer, length
    
    def __update_footer(self):
        length_of_table = len(pickle.dumps(self.__pointer_table))
        self.__footer = self.__magic, length_of_table + 28, length_of_table, self.__length

    def get_pointer_table_from_file(self) -> dict[str , list[tuple[int, int]]]:
        offset = -self.__footer[1] ## Negative offset because calculating offset from the end of the file is easier
        length_pointer = self.__footer[2] ## Length remains positive
        with open(self._location, "rb") as f:
            f.seek(offset, 2)
            pickled_pointer_table = f.read(length_pointer)
        return pickle.loads(pickled_pointer_table)
    
    def get_pointer_table(self) -> dict[str , list[tuple[int, int]]]:
        return self.__pointer_table

    def __add_new_pointer(self, name: str, pointer_data: list[tuple[int, int]]):
        entry = self.__pointer_table.get(name) # Checks if the entry already exists
        if entry: # If yes, then add more (offset, length) pairs to the pointer
            entry.extend(pointer_data)
        else: # Otherwise create a new pointer
            self.__pointer_table[name] = pointer_data
    

    def capture(self, file: File):
        file_name = file.get_name()
        #Makes sure the specified file is not the vault file itself
        if file_name == self._name:
            raise VaultError("Vault cannot capture itself")
        #Makes sure a file by the same name does not yet exist
        if self.file_exists(file_name)[0]:
            raise VaultError("A file by the same name already exists. Consider renaming it first?")
        
        free_space =  self.__pointer_table["?empty"].copy()
        contents = file.read_bytes() #Gets the byte data of given file
        contents = File.compress(contents)
        len_contents = len(contents)
        written = 0
        for slot in free_space:
            offset, length = slot
            if length >= len_contents - written: # A slot large enough to fit the remaining/whole file was found
                with open(self._location, "r+b") as f:
                    f.seek(offset)
                    f.write(contents[written:])
                self.__add_new_pointer(file_name, [(offset, len_contents - written)])
                if length > len_contents - written: # If the length of the empty slot was larger than the (remaining) file length, not all the space was used
                    leftover = (offset + len_contents - written, length - len_contents + written) # This accounts for leftover space and appends it to the empty pointers
                    self.__pointer_table["?empty"].append(leftover)
                self.__pointer_table["?empty"].remove(slot) # Because the slot is no longer empty, remove it from the empty pointers
                break

            elif length < len_contents: # A slot smaller than the file was found
                with open(self._location, "r+b") as f:
                    f.seek(offset) # Move to the offset of the free space
                    f.write(contents[written: written + length]) # Write only the part of the data that will fit in this space
                written += length # Add the length of the space to how much was written
                self.__add_new_pointer(file_name, [slot]) # Add this slot to the pointers
                self.__pointer_table["?empty"].remove(slot) # Because the slot is no longer empty, remove it from the empty pointers
                if written == len_contents:
                    break # Stop when all data was written

        else: # The file was unable to be completely written with the available space
            self.append_bytes(contents[written:]) #Appends all remaining data to the vault
            self.__add_new_pointer(file_name, [(self.__length, len_contents - written)])
            self.__length += len_contents  #Updating the length of the vault

        self.__update_footer() #Updating the footer
        os.remove(file.get_location())
    
    def file_exists(self, file_name : str) -> tuple[bool, list[tuple[int, int]]]:
        """
        Checks if a file exists through the pointer table

        params:
            - file_name - name of the file with the extension

        - If it does, it returns True, and a list with entries in the format of: [(offset: int, length: int), ...]
        - Otherwise, it returns False, and an empty list
        """
        file_data = self.__pointer_table.get(file_name)
        if file_data:
            return True, file_data
        return False, []

    def release(self, file_name: str, path: str = "./") -> bool:
        if file_name == "?empty": # Checks that the user is not trying to extract the empty pointers
            raise VaultError('Invalid file name: "?empty"')
        does_file_exist = self.file_exists(file_name) # Retrieve file information and check that it exists
        if does_file_exist[0]:
            file_locations = does_file_exist[1] # List of offsets and lengths 
            released_file = File(rf"{path}/{file_name}") # Create file
            data = b""
            with open(self._location, "rb") as f:
                for location in file_locations: # Looping over every (offset, length) pair in the file_locations
                    offset, length = location
                    f.seek(offset, 0) # Go to the offset
                    data += f.read(length) # Read all the bytes associated in that block with the file
            data = File.decompress(data)
            released_file.write_bytes(data) # Append data to a file 

            self.__pointer_table["?empty"].extend(file_locations) # Release the newly freed space to the empty pointer table
            del self.__pointer_table[file_name] # Clear the pointer for the released file from memory
            return True
        return False
    
    def get_size_of(self, file_name: str) -> int | None:
        does_file_exist, file_data = self.file_exists(file_name)
        if does_file_exist:
            length = 0
            for pointer in file_data:
                length += pointer[1]
            return length
        return None

    def __del__(self): # Writes updated pointer table to vault when self is cleared from RAM
        if len(self.__pointer_table.keys()) == 1:
            os.remove(self._location)
        else:
            self.append_bytes(pickle.dumps(self.__pointer_table))
            self.__update_footer()
            self.append_footer()