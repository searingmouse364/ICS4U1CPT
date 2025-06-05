"""
Date:
File Description: GUI for user experience
Name: Notorious LB
"""
import sys
import os

sys.path.insert(1, os.getcwd()) # Allows importation of Vault and File
from fileUtilities.vault import Vault
from fileUtilities.file import File
from .models import VaultFileSystemModel
from .FileSearchWorker import FileSearchWorker


# Importing required PyQt5 modules
from PyQt5.QtWidgets import (    
    QMainWindow,        
    QAction,              
    QToolBar,             
    QStatusBar,           
    QTreeView,           
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,             
    QSplitter,           
    QHeaderView ,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QAbstractItemView,
    QDialog,
    QListWidget,
    QPushButton,
    QLineEdit,
    QProgressBar,
    QApplication
    
)

from PyQt5.QtCore import Qt, QDir, pyqtSignal, QThread



class GUI(QMainWindow):  # Main window class inheriting from QMainWindow
    search_finished = pyqtSignal(list)  # Signal that sends list of QModelIndex matches

    def __init__(self):
        super().__init__()  # Call parent constructor
        self.setWindowTitle("Vault - Archive Manager")  # Window title
        self.setGeometry(100, 100, 900, 600)  # Set window position (x=100, y=100) and size (900x600)
        self.initUI()  # Call custom method to build UI
        self.selected_file_path = None  # Store current file path
        

    def initUI(self):
        # ===== Menu Bar =====
        menubar = self.menuBar()              # Create the menu bar
        self.file_menu = menubar.addMenu("File")   # Add "File" menu
        self.file_menu.addAction("Exit", self.close)  # Add "Exit" item that calls the window's close method

        # ===== Toolbar =====
        toolbar = QToolBar("Main Toolbar")  # Create a toolbar
        self.addToolBar(toolbar)            # Add toolbar to main window
        add_action = QAction("Add", self)    # Add "Add" action button
        add_action.triggered.connect(self.add_file)
        toolbar.addAction(add_action)
        extract_action = QAction("Extract", self)  # Add "Extract" action button
        extract_action.triggered.connect(self.extract_file)
        toolbar.addAction(extract_action)
        compress_action = QAction("Compress", self)
        compress_action.triggered.connect(self.compress_files)
        toolbar.addAction(compress_action)

        # ===== Search bar =====
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files or folders...")
        self.search_button = QPushButton("Find Next")
        self.search_button.clicked.connect(self.find_next_match)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)

        self.search_bar.returnPressed.connect(self.start_search)

        self.searching = False
        self.match_results = []
        self.current_match_index = -1
        self.search_finished.connect(self.handle_search_results)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setVisible(False)

        self.cancel_button = QPushButton("Cancel Search")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_search)

        # Add to layout
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.progress_bar)
        search_layout.addWidget(self.cancel_button)


        # ===== Central Widget and Layout =====
        central_widget = QWidget()           # Create a central widget (container)
        self.setCentralWidget(central_widget)  # Set it as the main area of the window
        splitter = QSplitter(Qt.Horizontal)  # Create a horizontal splitter (left/right resizable panels)

        # ===== File System Tree View (Left Pane) =====

        # File system model (all files/folders)
        self.model = VaultFileSystemModel()
        self.model.setRootPath("")  # or your desired root path


        # Tree view setup
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Index for the current directory in the source model
        cwd_path = os.getcwd()
        cwd_index = self.model.index(cwd_path)

        self.tree.setRootIndex(self.model.index(QDir.rootPath()))  # Use actual rootPath
        self.tree.setCurrentIndex(cwd_index)  # Scroll to the current working directory
        self.tree.expand(cwd_index)

        # Layout and signals
        self.tree.setColumnWidth(0, 250)
        self.tree.clicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree)

        # ===== File Info Table (Right Pane) =====
        self.table = QTableWidget(0, 3)       # Create table with 1 row and 4 columns
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Type"])  # Set column headers
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        splitter.addWidget(self.table)        # Add table to right side of splitter

        # ===== Layout Management =====
        layout = QVBoxLayout()               # Create a vertical layout
        layout.addLayout(search_layout)
        layout.addWidget(splitter)           # Add the splitter (tree + table)
        central_widget.setLayout(layout)     # Apply layout to the central widget

        # ===== Status Bar =====
        self.setStatusBar(QStatusBar(self))  # Create and set a status bar at the bottom
    
    def start_search(self):

        self.match_results = []
        self.current_match_index = -1
        query = self.search_bar.text().lower()
        if not query or self.searching:
            return
        
        self.searching = True
        QMessageBox.information(self, "Search Started", "Searching for your file(s) now")
        

        root_path = self.model.filePath(self.tree.rootIndex())

        self.search_thread = QThread()
        self.worker = FileSearchWorker(root_path, query, self.model)
        self.worker.moveToThread(self.search_thread)

        self.search_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_search_results)
        self.worker.finished.connect(self.cleanup_search)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.total_estimated.connect(self.setup_progress_bar)
        self.worker.progress.connect(self.update_progress)

        self.search_thread.finished.connect(self.search_thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)

        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)

        self.search_thread.start()

    def cancel_search(self):
        if hasattr(self, "worker"):
            self.worker.cancel()
        self.cleanup_search([])
        self.searching = False

    def cleanup_search(self, results):
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        if self.search_thread.isRunning():
            self.search_thread.quit()
            self.search_thread.wait()


    def handle_search_results(self, results):
        self.searching = False
        self.match_results = results
        if self.match_results:
            QMessageBox.information(self, "Search", f"Found {len(self.match_results)} item(s).")
            self.current_match_index = 0
            self.highlight_match(self.match_results[0])
        else:
            QMessageBox.information(self, "Search", "No match found.")

    def find_next_match(self):
        if not self.match_results:
            return
        self.current_match_index = (self.current_match_index + 1) % len(self.match_results)
        self.highlight_match(self.match_results[self.current_match_index])

    def highlight_match(self, index):
        self.tree.expand(index.parent())
        self.tree.setCurrentIndex(index)
        self.tree.scrollTo(index)

    def setup_progress_bar(self, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        QApplication.processEvents()  # Force immediate UI update

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()


    def on_tree_item_clicked(self, index):
        try: 
            # Map from proxy model to source model
            file_info = self.model.fileInfo(index)
            file_path = self.model.filePath(index)
            file_info = self.model.fileInfo(index)
            self.table.setRowCount(0)
            self.selected_file_path = None
            self.file_menu.setTitle(file_info.fileName())

            if file_info.isFile() and file_info.fileName().endswith(".vault"):
                self.selected_file_path = file_info.absoluteFilePath()
                vault = Vault(file_path)
                items = [item for item in vault.get_pointer_table().keys() if item != "?empty"]
                
                for item in items:
                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)
                    file_name, file_ext = os.path.splitext(item)
                    file_name = item
                    size = f"{vault.get_size_of(item)} bytes"
                    file_type = f"{file_ext.upper()} File"


                    self.table.setItem(row_position, 0, QTableWidgetItem(file_name))
                    self.table.setItem(row_position, 1, QTableWidgetItem(size))
                    self.table.setItem(row_position, 2, QTableWidgetItem(file_type))
        except Exception as e:
            QMessageBox.warning(self, "Error!", str(e))
    def extract_file(self):
        try:
            if self.selected_file_path and self.selected_file_path.endswith(".vault"):
                QMessageBox.information(self, "Extracting", f"Extracting from:\n{self.selected_file_path}")
                vault = Vault(self.selected_file_path)
                dir = directory = os.path.dirname(self.selected_file_path)
                items = [item for item in vault.get_pointer_table().keys() if item != "?empty"]

                dialog = QDialog(self)
                dialog.setWindowTitle("Select files to extract")
                layout = QVBoxLayout()

                list_widget = QListWidget()
                list_widget.setSelectionMode(QListWidget.MultiSelection)
                list_widget.addItems(items)

                extract_selected_btn = QPushButton("Extract Selected")
                extract_all_btn = QPushButton("Extract All")
                cancel_btn = QPushButton("Cancel")

                layout.addWidget(list_widget)
                layout.addWidget(extract_selected_btn)
                layout.addWidget(extract_all_btn)
                layout.addWidget(cancel_btn)
                dialog.setLayout(layout)


                def extract_selected():
                    selected = list_widget.selectedItems()
                    if not selected:
                        QMessageBox.warning(dialog, "No Selection", "No files selected.")
                        return
                    items = [item.text() for item in selected]
                    for item in items:
                        vault.release(item, dir)
                    dialog.accept()
                def extract_all():
                    for item in items:
                        vault.release(item, dir)
                    dialog.accept()

                extract_selected_btn.clicked.connect(extract_selected)
                extract_all_btn.clicked.connect(extract_all)
                cancel_btn.clicked.connect(dialog.reject)
                dialog.exec_()
                del vault # Something prevents the vault from being removed from RAM automatically, so write it explicitly 
            else:
                QMessageBox.warning(self, "No Valid File", "Please select a .vault file to extract.")

        except Exception as e:
            QMessageBox.warning(self, "Error!", str(e))

    def add_file(self):
        try:
            if not self.selected_file_path or not self.selected_file_path.endswith(".vault"):
                    QMessageBox.warning(self, "No Vault Selected", "Please select a .vault file to add files.")
                    return


            vault = Vault(self.selected_file_path)
            # Choose files to add
            files_to_add, _ = QFileDialog.getOpenFileNames(self, "Select files to add")
            if not files_to_add:
                return  # Cancelled
            else:
                for file in files_to_add:
                    vault.capture(File(file))
        except Exception as e:
            QMessageBox.warning(self, "Error!", str(e))
    
    def compress_files(self):
        try:
            selected_indexes = self.tree.selectionModel().selectedIndexes()

            # Get absolute file paths (filter only files, not folders or duplicates from other columns)
            files_to_add = []
            for index in selected_indexes:
                if index.column() != 0:  # Avoid getting the same item multiple times (one per column)
                    continue
                file_info = self.model.fileInfo(index)
                if file_info.isFile():
                    files_to_add.append(file_info.absoluteFilePath())

            if not files_to_add:
                QMessageBox.warning(self, "No files selected", "Please select one or more files in the tree.")
                return

            # Ask for vault name
            text, ok = QInputDialog.getText(self, "Name your vault", "Enter vault name:")
            vault_path = os.path.dirname(files_to_add[0])
            path = rf"{vault_path}\{text}.vault"
            while os.path.isfile(path) and ok: # Makes sure the vault name entered does not already exist
                QMessageBox.warning(self, "Vault already exists!", "Please choose a different name for your vault")
                text, ok = QInputDialog.getText(self, "Name your vault", "Enter vault name:")
                path = rf"{vault_path}\{text}.vault"
            if ok:
                vault = Vault(path)
                for file in files_to_add:
                    vault.capture(File(file))
                QMessageBox.information(self, "Done", f"{len(files_to_add)} files added to {text}.vault")
        except Exception as e:
            QMessageBox.warning(self, "Error!", str(e))
            

