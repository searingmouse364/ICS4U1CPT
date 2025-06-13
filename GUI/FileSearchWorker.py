"""
Date:
File Description: Searches file system for user using linear search
Name: Notorious LB
"""

from PyQt5.QtCore import QObject, pyqtSignal
from time import time
from functools import lru_cache
import os

class FileSearchWorker(QObject):
    
    # Used to update PyQt5 GUI without blocking main thread
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    total_estimated = pyqtSignal(int)
    
    @staticmethod
    @lru_cache(maxsize=None) # Cache result because this function takes a while
    def parse_dirs_cached(root_path): # Parse all directories in the system
        all_dirs = []
        for dirpath, _, _ in os.walk(root_path):
            all_dirs.append(dirpath)
        return all_dirs

    def __init__(self, root_path, query, model):
        super().__init__()
        self.root_path = root_path
        self.query = query
        self.model = model
        self._cancelled = False # Used to kill function
        self._last_emit_time = 0 # Keeps track of last emit time to moderate updates

    def cancel(self):
        self._cancelled = True

    def run(self):
        matches = []
        self.progress.emit(0) # Update progress bar to 0%
        all_dirs = FileSearchWorker.parse_dirs_cached(self.root_path)
        self.total_estimated.emit(len(all_dirs))
        for i, dirpath in enumerate(all_dirs): #Linear search
            if self._cancelled:
                return  # Stop the thread
            for fname in os.listdir(dirpath):
                if self._cancelled:
                    return
                if self.query in fname.lower():
                    full_path = os.path.join(dirpath, fname)
                    index = self.model.index(full_path) # Get the index of full_path in the file tree, for the "find next" btn
                    if index.isValid(): # Make sure index exists
                        matches.append(index)
            now = time()
            if now - self._last_emit_time > 0.05:  # Emit only every ~50ms to not overwhelm the CPU
                self.progress.emit(i)
                self._last_emit_time = now # Updat emit time

        self.finished.emit(matches) # Return matches
