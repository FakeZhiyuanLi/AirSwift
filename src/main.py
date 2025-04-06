from watchdog.observers import Observer
from fileUtils import DownloadHandler
from awsUtils import list_bucket_folder_files, download_file_from_bucket_folder, upload_file_to_bucket_folder
from file_handler import process_file, get_description_to_file_path, process_initial_audio
from faiss_db import VectorDB
from audio_recorder import record_until_silence_bytes
import customtkinter as ctk
import threading
import queue
import time
import random
import os

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

db = VectorDB()

DOWNLOADED_FILES = []
AWS_PULLED_FILES = set()
AWS_POLL_INTERVAL = 5
# UUID = str(random.randint(10000, 99999))
UUID = "1234"
POLL_FROM_AWS = True

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
        self.grid_columnconfigure(0, weight=1)

        self.recipient_input_box = ctk.CTkEntry(self, placeholder_text="UUID (Ex. 12345)", 
                font=("Arial Italic", 16), text_color="#AAAAAA", width=200, height=40, corner_radius=15)
        self.recipient_input_box.grid(row=0, column=0, padx=10, pady=10, sticky="")

        self.text_input = ctk.CTkEntry(self, placeholder_text="File Description (ie. Image of Thomas The Tank Engine)", 
                font=("Arial Italic", 16), text_color="#AAAAAA", height=80, corner_radius=15)
        self.text_input.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.sendAndTTSGroup = ctk.CTkFrame(self)
        self.sendAndTTSGroup.configure(fg_color="#212121")
        self.sendAndTTSGroup.grid(row=2, column=0, padx=0, pady=25, sticky="")

        self.speech_button = ctk.CTkButton(self.sendAndTTSGroup, text="STT 🔊", font=("Arial Bold", 24), height=50, corner_radius=25, command=self.handle_tts_button)
        self.send_button = ctk.CTkButton(self.sendAndTTSGroup, text="Send   →", font=("Arial Bold", 24), width=100, height=50, corner_radius=25, command=self.handle_send_button)

        self.speech_button.grid(row=0, column=0, padx=20, pady=0, sticky="")
        self.send_button.grid(row=0, column=1, padx=20, pady=0, sticky="")

        # self.speech_button.grid(row=1, column=1, padx=0, pady=0, sticky="")
        # self.send_button.grid(row=2, column=0, padx=10, pady=(10, 100), sticky="")

    def handle_send_button(self):
        user_description = self.text_input.get()

        if len(user_description) == 0:
            return

        retrieved_description = db.search_with_context(user_description)['document']
        file_path = get_description_to_file_path()[retrieved_description]
        recipient_UUID = self.recipient_input_box.get()
        upload_file_to_bucket_folder(file_path, recipient_UUID)
        print("successfully uploaded from send button")
    
    def handle_tts_button(self):
        bytes_output = record_until_silence_bytes()
        transcription = process_initial_audio(bytes_output)
        self.text_input.delete(0, ctk.END)
        self.text_input.insert(0, transcription)
        
        retrieved_description = db.search_with_context(transcription)['document']
        file_path = get_description_to_file_path()[retrieved_description]
        recipient_UUID = self.recipient_input_box.get()
        upload_file_to_bucket_folder(file_path, recipient_UUID)
        print("successfully uploaded from tts")


class RecipientAndInput(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color="#212121")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # self.recipient_dropdown = ctk.CTkOptionMenu(self, values=["Select A Recipient", "Friend 1", "Friend 2", "Group Chat"],
        #     width=300, height=40, 
        #     fg_color="#2D2D2D", button_color="#2D2D2D",
        #     text_color="white", dropdown_fg_color="#2D2D2D")
        # self.recipient_dropdown.grid(row=0, column=0, padx=10, pady=10, sticky="")

        self.queryInputBox = QueryInputBox(self)
        self.queryInputBox.grid(row=1, column=0, padx=10, pady=20, sticky="ew")


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

class ConfirmationPopup(ctk.CTkToplevel):
    def __init__(self, parent, file_name):
        super().__init__()

        self.title("File Download Confirmation")
        self.geometry("450x200")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.result = False
        self.file_name = file_name

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Message frame
        message_frame = ctk.CTkFrame(self, fg_color="transparent")
        message_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        file_icon = ctk.CTkLabel(message_frame, text="📄", font=("Arial", 32))
        file_icon.grid(row=0, column=0, padx=(0, 15), pady=10)

        message_label = ctk.CTkLabel(
            message_frame, 
            text=f"New file detected. Download '{self.file_name}'?",
            font=("Arial", 14),
            justify="left"
        )
        message_label.grid(row=0, column=1, padx=0, pady=10, sticky="w")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="sew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        download_button = ctk.CTkButton(
            button_frame, 
            text="Download", 
            command=self.on_confirm,
            fg_color="#2ecc71",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        download_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        skip_button = ctk.CTkButton(
            button_frame, 
            text="Skip", 
            command=self.on_cancel,
            fg_color="#e74c3c",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        skip_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")

    def on_confirm(self):
        """Callback for the confirm button"""
        self.result = True
        self.destroy()
    
    def on_cancel(self):
        """Callback for the cancel button"""
        self.result = False
        self.destroy()


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

        if POLL_FROM_AWS:
            self.thread = threading.Thread(target=self.aws_file_pull_task)
            self.thread.daemon = True
            self.thread.start()

    def aws_file_pull_task(self):
        while True:
            try:
                folder_files = list_bucket_folder_files(UUID)
                print("POLLED AWS")
                for file in folder_files:
                    if file not in AWS_PULLED_FILES:
                        AWS_PULLED_FILES.add(file)
                        self.show_download_confirmation(file)
                        # download_file_from_bucket_folder(os.path.join(get_downloads_folder(), file), UUID, file)
                time.sleep(AWS_POLL_INTERVAL)
            except Exception as e:
                print(e)
                time.sleep(10)

    def show_download_confirmation(self, file):
        self.after(0, lambda: self._show_download_confirmation_dialog(file))

    def _show_download_confirmation_dialog(self, file):
        popup = ConfirmationPopup(self, file)
        
        # Wait for the popup to be closed
        self.wait_window(popup)
        
        # Handle the result
        if popup.result:
            print(f"Downloading file: {file}")
            AWS_PULLED_FILES.add(file)
            download_file_from_bucket_folder(os.path.join(get_downloads_folder(), file), UUID, file)
            print("File was successfully downloaded")
        else:
            print(f"Skipped download for file: {file}")
            # Still add to pulled files to avoid asking again
            AWS_PULLED_FILES.add(file)

    def poll_queue(self):
        try:
            while True:
                file_path = self.file_queue.get_nowait()
                DOWNLOADED_FILES.append(file_path)
                self.display_file(file_path)

                document_description = process_file(file_path)
                db.add_document(document_description)

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
        # print(f"here: {file_path}")

if __name__ == "__main__":
    app = App()
    app.configure(fg_color="#212121")
    app.attributes("-topmost", True)
    app.lift()
    app.attributes("-topmost", False)
    app.mainloop()