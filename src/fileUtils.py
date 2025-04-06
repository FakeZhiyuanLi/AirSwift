import os
from watchdog.events import FileSystemEventHandler

EXISTING_FILES = set()

class DownloadHandler(FileSystemEventHandler):
    # Common file extensions
    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".txt",
    }

    def __init__(self, file_queue):
        super().__init__()
        self.file_queue = file_queue

    def on_created(self, event):
        # Only process files (ignore directories)
        if not event.is_directory:
            _, ext = os.path.splitext(event.src_path)
            if ext.replace(" ", "").lower() in self.SUPPORTED_EXTENSIONS and event.src_path not in EXISTING_FILES:
                self.file_queue.put(event.src_path)
                EXISTING_FILES.add(event.src_path)
                # print(f'file detected: {event.src_path}')