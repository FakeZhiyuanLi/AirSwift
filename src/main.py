import os
import queue
import customtkinter
# import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from watchdog.observers import Observer
from fileUtils import DownloadHandler

def apply_ctk_configs():
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("blue")

# Determine the default Downloads folder based on the OS
def get_downloads_folder():
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads")
    if os.path.isdir(downloads):
        return downloads
    else:
        # return home
        raise IOError("couldn't access downloads folder")

# The main GUI application
class DownloadMonitorApp(customtkinter.CTk):
    def __init__(self, root, monitor_path):
        self.root = root
        self.monitor_path = monitor_path
        self.file_queue = queue.Queue()

        self.root.title("Download Monitor")
        self.root.geometry("1200x1000")

        # Create a ScrolledText widget to display file paths
        self.text_area = ScrolledText(self.root, wrap=customtkinter.WORD, state="disabled")
        self.text_area.pack(expand=True, fill=customtkinter.BOTH, padx=10, pady=10)

        # Set up watchdog observer
        self.event_handler = DownloadHandler(self.file_queue)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.monitor_path, recursive=False)
        self.observer.start()

        # Start polling the file queue
        self.poll_queue()

        # Bind the close event to properly shut down the observer
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def poll_queue(self):
        try:
            while True:
                file_path = self.file_queue.get_nowait()
                self.display_file(file_path)
        except queue.Empty:
            pass
        # Check again after 100 ms
        self.root.after(100, self.poll_queue)

    def display_file(self, file_path):
        self.text_area.configure(state="normal")
        self.text_area.insert(customtkinter.END, f"New file detected: {file_path}\n")
        self.text_area.configure(state="disabled")
        self.text_area.see(customtkinter.END)

    def on_close(self):
        # Stop the observer thread before closing the app
        self.observer.stop()
        self.observer.join()
        self.root.destroy()

def main():
    downloads_folder = get_downloads_folder()
    apply_ctk_configs()

    root = customtkinter.CTk()
    app = DownloadMonitorApp(root, downloads_folder)
    root.mainloop()

if __name__ == "__main__":
    main()
