from watchdog.observers import Observer
from fileUtils import DownloadHandler
from awsUtils import list_bucket_folder_files, download_file_from_bucket_folder, upload_file_to_bucket_folder
from file_handler import process_file, get_description_to_file_path, process_initial_audio
from faiss_db import VectorDB
from audio_recorder import record_until_silence_bytes
from PIL import Image
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
UUID = str(random.randint(10000, 99999))
# UUID = "1234"
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

    def handle_send_button(self):
        user_description = self.text_input.get()

        if len(user_description) == 0:
            return
        
        # Disable button and show status
        self.send_button.configure(state="disabled")
        
        # Use threading to keep UI responsive
        threading.Thread(target=self._process_send, args=(user_description,), daemon=True).start()
    
    def _process_send(self, user_description):
        recipient_UUID = self.recipient_input_box.get()
        
        # Search in database
        retrieved_description = db.search_with_context(user_description)['document']
        file_path = get_description_to_file_path()[retrieved_description]
        
        # Upload file
        upload_file_to_bucket_folder(file_path, recipient_UUID)
        self.send_button.configure(state="enabled")
            
    
    def handle_tts_button(self):
        # Disable button and show status
        self.speech_button.configure(state="disabled")
        
        # Use threading to keep UI responsive
        threading.Thread(target=self._process_tts, daemon=True).start()

    def _process_tts(self):
        bytes_output = record_until_silence_bytes()
        transcription = process_initial_audio(bytes_output)
        
        # Update input field from main thread
        self.after(0, lambda: self.text_input.delete(0, ctk.END))
        self.after(10, lambda: self.text_input.insert(0, transcription))
        
        # Process search and upload
        recipient_UUID = self.recipient_input_box.get()
        retrieved_description = db.search_with_context(transcription)['document']
        file_path = get_description_to_file_path()[retrieved_description]
        upload_file_to_bucket_folder(file_path, recipient_UUID)
        self.speech_button.configure(state="enabled")


class RecipientAndInput(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(fg_color="#212121")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.queryInputBox = QueryInputBox(self)
        self.queryInputBox.grid(row=1, column=0, padx=10, pady=20, sticky="ew")

def open_settings(self):
    self.settings_popup = SettingsPopup(self)

class SettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__()  # Don't pass parent directly to avoid macOS issues
        
        self.parent = parent
        self.title("Settings")
        self.geometry("450x350")
        self.resizable(False, False)
        
        # Configure behavior - use after() to avoid animation issues
        self.after(100, lambda: self.transient(parent))
        self.after(100, lambda: self.grab_set())
        
        # Center on parent
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 350) // 2
            self.geometry(f"+{x}+{y}")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(self, text="Settings", font=("Arial Bold", 28))
        header_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nw")
        
        # Settings container
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=0)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Username setting
        username_label = ctk.CTkLabel(settings_frame, text="Display Name:", font=("Arial", 16))
        username_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")
        
        # Get current username from parent's greeting label or use default
        current_name = "[User]"
        try:
            if hasattr(parent, 'greet_text'):
                greeting_text = parent.greet_text.cget("text")
                if "Hey there, " in greeting_text:
                    current_name = greeting_text.replace("Hey there, ", "")
        except Exception:
            pass
        
        self.username_entry = ctk.CTkEntry(settings_frame, font=("Arial", 16), width=200)
        self.username_entry.insert(0, current_name)
        self.username_entry.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="w")
        
        # Theme setting
        theme_label = ctk.CTkLabel(settings_frame, text="Theme:", font=("Arial", 16))
        theme_label.grid(row=1, column=0, padx=(20, 10), pady=20, sticky="w")
        
        # Get current theme
        current_theme = ctk.get_appearance_mode().lower()
        
        self.theme_var = ctk.StringVar(value=current_theme)
        self.theme_combobox = ctk.CTkComboBox(
            settings_frame,
            values=["dark", "light", "system"],
            variable=self.theme_var,
            state="readonly",
            font=("Arial", 16),
            width=200
        )
        self.theme_combobox.grid(row=1, column=1, padx=(10, 20), pady=20, sticky="w")
        
        # Buttons container
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=20, pady=(20, 20), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="#e74c3c",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        cancel_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        # Save button
        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save",
            command=self.save_settings,
            fg_color="#2ecc71",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        save_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")
    
    def on_cancel(self):
        """Safely destroy the window"""
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass
    
    def save_settings(self):
        # Update username
        try:
            new_username = self.username_entry.get()
            if new_username.strip():  # Check if the username is not empty
                self.parent.greet_text.configure(text=f"Hey there, {new_username}")
            
            # Update theme
            selected_theme = self.theme_var.get()
            ctk.set_appearance_mode(selected_theme)
        except Exception as e:
            print(f"Error saving settings: {e}")
        
        # Close the popup
        self.on_cancel()

class UserControls(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=10)

        self.settings_image = ctk.CTkImage(Image.open("assets/settings.png"), size=(20, 20))
        self.settings_button = ctk.CTkButton(self, text="", image=self.settings_image, command=self.open_settings, width=40, height=40)
        self.settings_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.greet_text = ctk.CTkLabel(self, text=f"Hey there, [User]", font=("Arial Bold", 42), text_color="white", anchor="center")
        self.greet_text.grid(row=1, column=0, padx=10, pady=(100, 0), sticky="")

        self.recipientAndInput = RecipientAndInput(self)
        self.recipientAndInput.grid(row=2, column=0, padx=10, pady=(0, 50), sticky="ew")

    def open_settings(self):
        self.settings_popup = SettingsPopup(self)

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

        self.download_button = ctk.CTkButton(
            button_frame, 
            text="Download", 
            command=self.on_confirm,
            fg_color="#2ecc71",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        self.download_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")
        
        self.skip_button = ctk.CTkButton(
            button_frame, 
            text="Skip", 
            command=self.on_cancel,
            fg_color="#e74c3c",
            font=("Arial Bold", 14),
            height=40,
            corner_radius=15
        )
        self.skip_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="w")

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

        # Set up queues for thread-safe communication
        self.file_queue = queue.Queue()
        self.ui_update_queue = queue.Queue()
        self.file_processing_queue = queue.Queue()
        
        # Event handler for file downloads
        self.event_handler = DownloadHandler(self.file_queue)

        # Set up and start the watchdog observer
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=get_downloads_folder(), recursive=False)
        self.observer.start()

        # Set up UI layout
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.userControls = UserControls(self)
        self.userControls.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.indexedFiles = IndexedFiles(self)
        self.indexedFiles.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Status bar for background operations
        self.status_bar = ctk.CTkLabel(self, text="", font=("Arial", 12), anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Start polling threads
        self.poll_queue()
        self.poll_ui_updates()
        
        # Start file processing thread
        self.file_processor_thread = threading.Thread(target=self.process_files_thread, daemon=True)
        self.file_processor_thread.start()
        
        # Start AWS polling if enabled
        if POLL_FROM_AWS:
            self.aws_thread = threading.Thread(target=self.aws_file_pull_task, daemon=True)
            self.aws_thread.start()

        # Set up close handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def process_files_thread(self):
        """Thread that processes files in the background"""
        while True:
            try:
                file_path = self.file_processing_queue.get()
                # Update status
                self.ui_update_queue.put(("status", "Processing file..."))
                
                # Process the file
                document_description = process_file(file_path)
                db.add_document(document_description)
                
                # Clear status
                self.ui_update_queue.put(("status", ""))
                
                self.file_processing_queue.task_done()
            except Exception as e:
                print(f"Error processing file: {e}")
                self.ui_update_queue.put(("status", f"Error processing file: {str(e)}"))
                time.sleep(2)
                self.ui_update_queue.put(("status", ""))

    def poll_ui_updates(self):
        """Check for UI updates from worker threads"""
        try:
            while True:
                update_type, data = self.ui_update_queue.get_nowait()
                
                if update_type == "status":
                    self.status_bar.configure(text=data)
                elif update_type == "add_file":
                    self.indexedFiles.text_area.insert("end", f"{data}\n")
                
                self.ui_update_queue.task_done()
        except queue.Empty:
            pass
        
        # Check again after 50 ms
        self.after(50, self.poll_ui_updates)

    def poll_queue(self):
        """Check for new downloaded files"""
        try:
            while True:
                file_path = self.file_queue.get_nowait()
                DOWNLOADED_FILES.append(file_path)
                
                # Add to UI
                self.ui_update_queue.put(("add_file", file_path))
                
                # Queue for processing
                self.file_processing_queue.put(file_path)
                
                self.file_queue.task_done()
        except queue.Empty:
            pass
        
        # Check again after 100 ms
        self.after(100, self.poll_queue)

    def aws_file_pull_task(self):
        """Thread that polls AWS for new files"""
        while True:
            try:
                # Update status via queue
                self.ui_update_queue.put(("status", "Checking for new files..."))
                
                folder_files = list_bucket_folder_files(UUID)
                print("POLLED AWS")
                
                # Clear status after successful poll
                self.ui_update_queue.put(("status", ""))
                
                for file in folder_files:
                    if file not in AWS_PULLED_FILES:
                        AWS_PULLED_FILES.add(file)
                        self.show_download_confirmation(file)
                
                time.sleep(AWS_POLL_INTERVAL)
            except Exception as e:
                print(f"AWS polling error: {e}")
                self.ui_update_queue.put(("status", f"AWS connection error: {str(e)}"))
                time.sleep(10)
                self.ui_update_queue.put(("status", ""))

    def show_download_confirmation(self, file):
        self.after(0, lambda: self._show_download_confirmation_dialog(file))

    def _show_download_confirmation_dialog(self, file):
        popup = ConfirmationPopup(self, file)
        
        # Wait for the popup to be closed
        self.wait_window(popup)
        
        # Handle the result (download happens in popup thread)
        if popup.result:
            print(f"File was successfully downloaded: {file}")
        else:
            print(f"Skipped download for file: {file}")

    def on_close(self):
        # Stop the observer thread before closing the app
        self.observer.stop()
        self.observer.join()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.configure(fg_color="#212121")
    app.attributes("-topmost", True)
    app.lift()
    app.attributes("-topmost", False)
    app.mainloop()