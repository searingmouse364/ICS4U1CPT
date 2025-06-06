from PyQt5.QtCore import QObject, pyqtSignal
from time import time
from functools import lru_cache
import os

class FileSearchWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)
    total_estimated = pyqtSignal(int)

    def __init__(self, root_path, query, model):
        super().__init__()
        self.root_path = root_path
        self.query = query
        self.model = model
        self._cancelled = False
        self._last_emit_time = 0

    def cancel(self):
        self._cancelled = True

    @staticmethod
    @lru_cache(maxsize=None) # Cache result because this function takes a while
    def parse_dirs_cached(root_path): # Parse all directories in the system
        all_dirs = []
        for dirpath, _, _ in os.walk(root_path):
            all_dirs.append(dirpath)
        return all_dirs
        

    def run(self):
        matches = []
        self.progress.emit(0)
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
                    index = self.model.index(full_path)
                    if index.isValid():
                        matches.append(index)
            now = time()
            if now - self._last_emit_time > 0.05:  # Emit only every ~50ms
                self.progress.emit(i)
                self._last_emit_time = now

        self.finished.emit(matches)
