from tkinter.scrolledtext import ScrolledText
from watchdog.observers import Observer
from fileUtils import DownloadHandler
import customtkinter as ctk
import queue
import os

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

DOWNLOADED_FILES = []

UUID = "1234"

# Determine the default Downloads folder based on the OS
def get_downloads_folder():
    home = os.path.expanduser("~")
    downloads = os.path.join(home, "Downloads")
    if os.path.isdir(downloads):
        return downloads
    else:
        # return home
        raise IOError("couldn't access downloads folder")

class QueryInputBox(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=1)

        self.text_input = ctk.CTkEntry(self, placeholder_text="File Description (ie. Image of Thomas The Tank Engine)", 
                font=("Arial Italic", 16), text_color="#AAAAAA", height=80, corner_radius=15)
        self.text_input.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.speech_button = ctk.CTkButton(self, text="tts", width=60, height=60, corner_radius=30)
        self.speech_button.grid(row=0, column=1, padx=0, pady=0, sticky="")

class RecipientAndInput(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color="#212121")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.recipient_dropdown = ctk.CTkOptionMenu(self, values=["Select A Recipient", "Friend 1", "Friend 2", "Group Chat"],
            width=300, height=40, 
            fg_color="#2D2D2D", button_color="#2D2D2D",
            text_color="white", dropdown_fg_color="#2D2D2D")
        self.recipient_dropdown.grid(row=0, column=0, padx=10, pady=10, sticky="")

        self.queryInputBox = QueryInputBox(self)
        self.queryInputBox.grid(row=1, column=0, padx=10, pady=20, sticky="ew")

        self.send_button = ctk.CTkButton(self, text="Send   →", font=("Arial Bold", 24), width=100, height=50, corner_radius=25)
        self.send_button.grid(row=2, column=0, padx=10, pady=(10, 100), sticky="")

class UserControls(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.greet_text = ctk.CTkLabel(self, text=f"Hey there, [User]", font=("Arial Bold", 42), text_color="white", anchor="center")
        self.greet_text.grid(row=0, column=0, padx=10, pady=(100, 0), sticky="")

        self.recipientAndInput = RecipientAndInput(self)
        self.recipientAndInput.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

class IndexedFiles(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=3)
        
        self.UUID_text = ctk.CTkLabel(self, text=f'UUID: {UUID}', font=("Arial Bold", 16), text_color="white", anchor="center")
        self.UUID_text.grid(row=0, column=0, padx=10, pady=10, sticky="ne")

        self.indexed_files_text = ctk.CTkLabel(self, text="Indexed Files", font=("Arial Bold", 28), text_color="white", anchor="center")
        self.indexed_files_text.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        self.text_area = ctk.CTkTextbox(self, wrap=ctk.NONE, font=("Arial", 14))
        self.text_area.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{1100}x{800}")
        self.title("AirSwift")

        self.file_queue = queue.Queue()
        self.event_handler = DownloadHandler(self.file_queue)

        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=get_downloads_folder(), recursive=False)
        self.observer.start()

        self.poll_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_close)


        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.userControls = UserControls(self)
        self.userControls.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.indexedFiles = IndexedFiles(self)
        self.indexedFiles.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")


    def poll_queue(self):
        try:
            while True:
                file_path = self.file_queue.get_nowait()
                DOWNLOADED_FILES.append(file_path)
                self.display_file(file_path)
                # print(f"file downloaded: {file_path}")
        except queue.Empty:
            pass
        # Check again after 100 ms
        self.after(100, self.poll_queue)

    def on_close(self):
        # Stop the observer thread before closing the app
        self.observer.stop()
        self.observer.join()
        self.destroy()

    def display_file(self, file_path):
        # TODO: show the file path
        self.indexedFiles.text_area.insert("end", f"{file_path}\n")
        print(f"here: {file_path}")

if __name__ == "__main__":
    app = App()
    app.configure(fg_color="#212121")
    app.attributes("-topmost", True)
    app.lift()
    app.attributes("-topmost", False)
    app.mainloop()