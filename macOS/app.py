import sys
import requests
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMessageBox
from record import *


# Constant variables
INPUT_DEVICE_NAME = "Breev Input"
OUTPUT_FILENAME = "output.mp3"
TRANSCRIBE_URL = "https://breev.ai/api/transcribe"
DEFAULT_COUNTDOWN_SECONDS = 3600

# Global variables
file_path = None


def upload_meeting(username, password, audio_path):
    with open(audio_path, "rb") as audio_file:
        # Prepare the file for upload (not const name since server needs it named "output.mp3")
        files = {"meetingRecording": ("output.mp3", audio_file, "audio/mp3")}
        # Data
        data = {
            "username": username,
            "password": password
        }
        # Send the POST request
        response = requests.post(TRANSCRIBE_URL, data, files=files)
        return response

# App
class Breev(QWidget):
   
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.is_recording = False # Set to not recording
        self.remaining_time = DEFAULT_COUNTDOWN_SECONDS  # Initialize remaining time
        self.timer = QTimer(self)  # Create a QTimer instance
        self.timer.timeout.connect(self.update_timer)  # Connect timer to update method

    def init_ui(self):
        # Create a label with centered alignment and headline style
        self.label = QLabel("Meeting aufzeichnen", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px;")

        # Create the countdown label
        self.countdown_label = QLabel("", self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 12px; color: gray;")
        self.countdown_label.setText(f"Verbleibende Zeit: 60:00")

        # Create the "Aufzeichnen" button
        self.start_button = QPushButton("Aufzeichnen", self)
        self.start_button.clicked.connect(self.start_recording)

        # Create the "Aufnahme beenden" button
        self.stop_button = QPushButton("Aufnahme beenden", self)
        self.stop_button.clicked.connect(self.show_credentials_popup_and_upload)
        self.stop_button.setEnabled(False)  # Initially disabled

        # Layout to organize widgets
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.countdown_label)  # Add countdown label to layout
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        # Set the layout for the main window
        self.setLayout(layout)

        # Configure the main window
        self.setWindowTitle("Breev")
        self.resize(300, 100)

    def start_recording(self):
        self.label.setText("Aufnahme läuft...")
        self.start_button.setEnabled(False)  # Disable "Aufzeichnen" button
        self.stop_button.setEnabled(True)   # Enable "Aufnahme beenden" button
        self.is_recording = True
        self.remaining_time = DEFAULT_COUNTDOWN_SECONDS  # Reset the countdown
        self.update_countdown_label()  # Update the label immediately
        self.timer.start(1000)  # Start the timer with 1-second intervals
        start_recording()

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1  # Decrease the time left
            self.update_countdown_label()  # Update the displayed time
        else:
            self.auto_submit_meeting()  # Submit the meeting when time runs out

    def update_countdown_label(self):
        minutes, seconds = divmod(self.remaining_time, 60)
        self.countdown_label.setText(f"Verbleibende Zeit: {minutes:02d}:{seconds:02d}")

    def auto_submit_meeting(self):
        self.timer.stop()  # Stop the timer
        if self.is_recording:
            self.show_credentials_popup_and_upload()  # Trigger the credentials popup
        self.label.setText("Automatische Einreichung")

    def show_credentials_popup_and_upload(self):
        if self.is_recording:
            stop_recording(OUTPUT_FILENAME)
        self.is_recording = False

        self.timer.stop()  # Stop the timer if it's running
        self.label.setText(f"Meeting aufzeichnen")

        dialog = CredentialsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            username = dialog.email_input.text()
            password = dialog.password_input.text()
            
            # Upload Meeting
            response = upload_meeting(username, password, file_path)

            if response.status_code == 401:
                self.show_credentials_popup_and_upload()
                
            elif response.status_code == 201:
                self.label.setText("Meeting erfolgreich hochgeladen!")

            elif response.status_code == 429:
                self.show_error_message("Limit überschritten", f"Sie haben bereits Ihr monatliches Limit überschritten.")

            elif response.status_code == 413:
                self.show_error_message("Länge überschritten", f"Das aufgezeichnete Meeting überschreitet 60 Minuten.")

            else:
                self.show_error_message("Fehler", f"Ein unerwarteter Fehler ist aufgetreten. Statuscode: {response.status_code}")

        else:
            pass
        
        self.stop_button.setEnabled(False)  # Disable "Aufnahme beenden" button
        self.start_button.setEnabled(True)  # Enable "Aufzeichnen" button

    def show_error_message(self, title, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

class CredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anmeldung")
        self.resize(300, 100)

        # Create input fields
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("E-Mail")
        self.email_input.setStyleSheet("font-size: 14px; padding: 2px;")  # Set font size and padding for the input

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Passwort")
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide password input
        self.password_input.setStyleSheet("font-size: 14px; padding: 2px;")  # Set font size and padding for the input

        # Create the form layout
        form_layout = QFormLayout()
        form_layout.addRow(self.email_input)
        form_layout.addRow(self.password_input)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Create the main layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

# Main execution
if __name__ == "__main__":
    # Initialize app
    app = QApplication(sys.argv) 

    # Set your virtual audio device name
    try:
        initialize_device(INPUT_DEVICE_NAME)

    except Exception as e:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Fehler")
        error_box.setText("Ein Fehler ist aufgetreten.")
        error_box.setInformativeText(str(e))
        error_box.exec_()
        sys.exit(1)


    # Get default file path
    file_path = create_file_path(OUTPUT_FILENAME)
    
    # Setup app
    window = Breev()
    window.show()
    sys.exit(app.exec_())