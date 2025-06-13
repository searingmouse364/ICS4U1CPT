"""
Date:
File Description: Adds the vault icon to .vault files in the file tree
Name: Notorious LB
"""

from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class VaultFileSystemModel(QFileSystemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault_icon = QIcon("./GUI/vault_icon.ico")

    def data(self, index, role):
        if role == Qt.DecorationRole and index.column() == 0:
            file_info = self.fileInfo(index) ## Get file
            if file_info.isFile() and file_info.suffix() == "vault":
                return self.vault_icon #Return vault icon if file is a ".vault" file
        return super().data(index, role) 