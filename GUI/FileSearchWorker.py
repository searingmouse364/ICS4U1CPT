from PyQt5.QtCore import QObject, pyqtSignal
from time import time
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
        

    def run(self):
        matches = []
        all_dirs = []
        self.progress.emit(0)
        for dirpath, _, _ in os.walk(self.root_path):
            if self._cancelled:
                return
            all_dirs.append(dirpath)

        self.total_estimated.emit(len(all_dirs))  # Send estimated total steps

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
