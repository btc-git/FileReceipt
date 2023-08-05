# FileReceipt is licensed under the GNU General Public License v3.0.
# See the LICENSE.txt file in the project root for the full license text.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

# Copyright (c) 2023 Brian Cummings
# brian@crimlawtech.com

import hashlib
import io
import os
import os.path
import platform
import csv
import subprocess
import sys
import zipfile
from datetime import datetime
from tzlocal import get_localzone
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QTextEdit, QScrollArea, QDialog, QComboBox, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QListWidget, QMessageBox, QLabel, QDesktopWidget, QAbstractItemView, QProgressBar, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QUrl, QThread, QSize
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QDesktopServices, QIcon, QScreen


# Dictionary of hash algorithms and their corresponding hashlib functions
HASH_ALGORITHMS = {
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512,
    'sha1': hashlib.sha1,
    'md5': hashlib.md5,
    'sha3_224': hashlib.sha3_224,
    'sha3_256': hashlib.sha3_256,
    'sha3_384': hashlib.sha3_384,
    'sha3_512': hashlib.sha3_512,
    'blake2s': hashlib.blake2s,
    'blake2b': hashlib.blake2b
}


# This function is used to get the correct path for a resource file, regardless of whether the script is running 
# as a standalone script or packed into a standalone executable (using tools like PyInstaller)
def resource_path(relative_path):
    # The '_MEIPASS' attribute is set by PyInstaller, and it contains the path to the temporary folder 
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # If the script is not running as a standalone executable, then the base path is the current directory
        base_path = os.path.abspath("")
    # Join the base path and the relative path to get the absolute path to the resource
    return os.path.join(base_path, relative_path)


# Message box that displays info about long file paths
class LongPathsMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Long File Paths in Windows')
        # remove context help button in title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package icon in pyinstaller onefile build
        icon_path = resource_path("fricon.png")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QLabel instance for the main paragraph
        text_label = QLabel('By default, Windows imposes a limit on the length of file paths and names, restricting them to approximately 260 characters. If a file path exceeds this limit due to long folder names or file names, some programs might be unable to open the file, even if it appears visible in Windows File Explorer. \n\n| ---------------- File Path ----------------- || ----- File Name ----- |\n\n C:\DocumentsFolder\WorkProjectsFolder\SampleDocument.PDF\n\n| -------- Example File Path Length: 56 Characters Long -------- |\n\nTo overcome this limitation, the "Long File Paths" option must be manually enabled in Windows. Without enabling this setting, FileReceipt, and other programs, may encounter difficulties consistently opening files within long file paths. Consequently, when creating a FileReceipt for files and folders with long paths, failure to enable the "Long File Paths" setting may lead to errors or omission of these files from the catalog.\n\nWARNING: Modifying the Windows Registry can be dangerous and may render your computer unusable. Seek assistance from your IT department or proceed with caution and create a backup before making changes.')
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create a QLabel instance for the sentence with hyperlinks
        link_label = QLabel('Visit the following pages for information and instructions on enabling Long File Paths: <a href="https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry">Long File Paths in Windows</a> and <a href="https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html">Enabling Long File Paths</a>.')
        link_label.setWordWrap(True)
        # Set the interaction flags on the QLabel to allow for text browser interactions - allows for clickable links
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # Enable opening of external links within the QLabel
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(link_label)

        # Create close button for window
        ok_button = QPushButton('Close')
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QHBoxLayout()
        # add stretchable space on right and left of OK button
        ok_button_layout.addStretch(1)
        ok_button_layout.addWidget(ok_button)
        ok_button_layout.addStretch(1)
        layout.addLayout(ok_button_layout)

# Message box that displays info about hash algorithm selection
class HashInfoMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hash Algorithm Selection')
        # remove context help button in title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package icon in pyinstaller onefile build
        icon_path = resource_path("fricon.png")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QLabel instance for the main paragraph
        text_label = QLabel('FileReceipt records a hash value for each file, which serves as a unique identifier for the file. This hash value is generated using a specific hash algorithm.\n\nBy default, FileReceipt utilizes the SHA-256 hash algorithm to calculate the corresponding SHA-256 hash values for each file. However, other commonly used hash algorithms can be selected from the dropdown menu. Changing the hash algorithm may be useful to coordinate with external programs, processes, or individuals. In order for hash values of identical files to match, the files must be processed using the same hash algorithm. This allows for direct comparisons and matching of hash values between different systems.')
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create a QLabel instance for the sentence with hyperlinks
        link_label = QLabel('For more information, see these pages on <a href="https://en.wikipedia.org/wiki/File_verification">File Verification</a> and <a href="https://en.wikipedia.org/wiki/Cryptographic_hash_function">Cryptographic Hash Functions</a>.')
        link_label.setWordWrap(True)
        # Set the interaction flags on the QLabel to allow for text browser interactions - allows for clickable links
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # Enable opening of external links within the QLabel
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(link_label)


        # Create close button for window
        ok_button = QPushButton('Close')
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QHBoxLayout()
        # add stretchable space on right and left of OK button
        ok_button_layout.addStretch(1)
        ok_button_layout.addWidget(ok_button)
        ok_button_layout.addStretch(1)
        layout.addLayout(ok_button_layout)

# Message box that displays FileReceipt license
class LicenseMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FileReceipt License: GNU GPLv3')
        # remove context help button in title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package icon in pyinstaller onefile build
        icon_path = resource_path("fricon.png")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QScrollArea, make its content resizable, and add it to the layout
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Create a QWidget for the scroll content, and set it as the widget for the scroll area
        scroll_content = QWidget(scroll_area)
        scroll_area.setWidget(scroll_content)

        # Create a QVBoxLayout for the scroll content, and set it as the layout for the scroll content
        content_layout = QVBoxLayout(scroll_content)
        scroll_content.setLayout(content_layout)

        # Create a QTextEdit and set it to read-only mode
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Get the license file path, read its content, and set it as the plain text for the QTextEdit - also used to package icon in pyinstaller onefile build
        file_path = resource_path("LICENSE.txt")
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
            text_edit.setPlainText(file_content)

        # Set the stylesheet for the QTextEdit to define the font size
        text_edit.setStyleSheet("font-size: 11pt;")
        # Add the QTextEdit to the content layout
        content_layout.addWidget(text_edit)

        # Create a QPushButton labeled 'Close', connect its clicked signal to the accept slot, and add it to a layout
        ok_button = QPushButton('Close')
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QHBoxLayout()
        ok_button_layout.addStretch(1)
        ok_button_layout.addWidget(ok_button)
        ok_button_layout.addStretch(1)

        # Add the button layout to the main layout
        layout.addLayout(ok_button_layout)

        # Get the available screen geometry from the primary screen
        screen = QApplication.instance().primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Calculate the window size based on 70% of the screen size, and resize the window accordingly
        window_width = int(screen_geometry.width() * 0.4)
        window_height = int(screen_geometry.height() * 0.6)
        self.resize(QSize(window_width, window_height))


# Message box that appears when file processing is complete
class FinishedMessageBox(QDialog):
    # Define the initialization function for the class, taking a folder path as an argument
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FileReceipt Complete!')
        # remove context help button in title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Create a QVBoxLayout, set its alignment to center, and set it as the layout for this dialog
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # set the path to the icon image - also used to package icon in pyinstaller onefile build
        icon_path = resource_path("fricon.png")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a spacer item and add it to the layout
        spacer_top = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addItem(spacer_top)

        # Create a QLabel with a message about where the file receipt was saved, set its word wrap to false, set its stylesheet, and add it to the layout
        text_label = QLabel(f'FileReceipt saved to {os.path.normpath(folder_path)}')
        text_label.setWordWrap(False)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create another spacer item with expanding vertical size policy and add it to the layout
        spacer_bottom = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)
        layout.addItem(spacer_bottom)

        # Create a QHBoxLayout for the button
        button_layout = QHBoxLayout()

        # Create a QPushButton labeled 'Ok', set its size to its recommended size, connect its clicked signal to the accept slot, and add it to the button layout
        ok_button = QPushButton('Ok')
        ok_button.setFixedSize(ok_button.sizeHint())
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)


# Define a new class DropZone, which inherits from QLabel. This class creates a drag and drop zone for files and folders.
class DropZone(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set this QLabel to accept drops
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(60)
        # Set the stylesheet for this QLabel to style the border and background
        self.setStyleSheet('''
            QLabel {
                border: 6px dashed #aaa;
                border-radius: 5px;
                background: #f0f0f0;
            }
        ''')
        # Set the text for this QLabel to guide users to drag and drop files and folders - split onto multiple lines
        self.setText("\nDrag and Drop Files\nand Folders Here\n")
    
    # Define the event handler for when a drag enters this QLabel
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    # Define the event handler for when a drag moves within this QLabel
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    # Define the event handler for when a drop happens in this QLabel
    def dropEvent(self, event: QDropEvent) -> None:
        self.parent().drop_list.addItemsFromUrls(event.mimeData().urls())


# Define a new class FileList, which inherits from QListWidget. This class creates a file list box for files to be processed.
class FileList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set this QListWidget to accept drops
        self.setAcceptDrops(True)
        # Initialize the file_paths as an empty set
        self.file_paths = set()
        # Set the selection mode for this QListWidget to allow multiple items to be selected
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    # Define the event handler for when a drag enters this QListWidget
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        
    # Define the event handler for when a drag moves within this QListWidget
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    # Define the event handler for when a drop happens in this QListWidget
    def dropEvent(self, event: QDropEvent) -> None:
        self.addItemsFromUrls(event.mimeData().urls())

    # Define a method to add items from URLs
    def addItemsFromUrls(self, urls):
        # Get the local file paths from the URLs
        file_paths = [url.toLocalFile() for url in urls]
        # Normalize the file paths
        normalized_paths = [os.path.normpath(file_path) for file_path in file_paths]
        # Get the new paths that are not already in self.file_paths
        new_paths = set(normalized_paths) - self.file_paths
        # Update self.file_paths with the new paths
        self.file_paths.update(new_paths)
        # Clear the items in this QListWidget
        self.clear()
        # Add the file paths to this QListWidget
        self.addItems(list(self.file_paths))

# Initialize the thread where file processing takes place
class HashingThread(QThread):
    progress = QtCore.pyqtSignal(int)
    processing_file = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(list, list, list, list)

    def __init__(self, file_paths, hash_algorithm):
        super().__init__()
        self.file_paths = file_paths  # File paths to process
        self.file_hashes = []  # Store file hashes
        self.error_logs = []  # Store any errors during the process
        self.empty_files = []  # Store info of empty files
        self.empty_directories = []  # Store info of empty directories
        self.cancelled = False  # Flag to cancel the process
        self.hash_algorithm = hash_algorithm  # Hash algorithm to use

    def run(self):
        total_files = len(self.file_paths)  # Total number of files
        current_file = 0  # Current file index

        # Loop over all file paths
        for file_path in self.file_paths:
            # Break the loop if the process has been cancelled
            if self.cancelled:
                break
            current_file += 1  # Increment the current file index

            # Check if the file path is a file
            if os.path.isfile(file_path):
                # Handle zip files separately
                if file_path.lower().endswith('.zip'):
                    # Calculate the hash of the zip file
                    hash_value, file_size, error_message = self.calculate_file_hash(file_path)
                    # Handle errors during hash calculation
                    if error_message:
                        # Append error to error logs
                        self.error_logs.append((os.path.normpath(file_path), error_message))
                    else:
                        # Calculate hashes for files inside the zip file
                        hashes, errors, empty_files_zip, empty_dirs_zip = self.calculate_zip_hashes_from_path(file_path)
                        # Append hashes and errors to respective lists
                        self.file_hashes.extend(hashes)
                        self.error_logs.extend(errors)
                        self.empty_files.extend(empty_files_zip)
                        self.empty_directories.extend(empty_dirs_zip)
                else:
                    # Calculate the hash of the file
                    hash_value, file_size, error_message = self.calculate_file_hash(file_path)
                    # Check if file is empty
                    if file_size == 0:
                        # Create a file info list
                        file_info = [os.path.normpath(file_path), hash_value, file_size]
                        # Append the file info to empty_files and file_hashes lists
                        self.empty_files.append(file_info)
                        self.file_hashes.append(file_info)
                    # Handle errors during hash calculation
                    elif error_message:
                        # Append error to error logs
                        self.error_logs.append((os.path.normpath(file_path), error_message))
                    else:
                        # Append file info to file_hashes list
                        self.file_hashes.append([os.path.normpath(file_path), hash_value, file_size])
            
            # Check if the file path is a directory     
            elif os.path.isdir(file_path):
                # Calculate hashes for files inside the directory
                hashes, errors, empty_files_folder, empty_dirs_folder = self.calculate_folder_hashes(file_path)
                # Append hashes and errors to respective lists
                self.file_hashes.extend(hashes)
                self.error_logs.extend(errors)
                self.empty_files.extend(empty_files_folder)
                self.empty_directories.extend(empty_dirs_folder)

            # If the process hasn't been cancelled, calculate and emit the progress
            if not self.cancelled:
                progress_value = int((current_file / total_files) * 100)
                self.progress.emit(progress_value)
                self.processing_file.emit(os.path.basename(file_path))

        # Emit the finished signal with the results
        self.finished.emit(self.file_hashes, self.error_logs, self.empty_files, self.empty_directories)



	# Define a method to calculate the hash of a file
    def calculate_file_hash(self, file_path):
        # Define the size of the blocks to read from the file
        block_size = 65536
        # Get the name of the hash algorithm in lower case
        hash_algorithm = self.hash_algorithm.lower()
        try:
            # Get the size of the file
            file_size = os.path.getsize(file_path)
            # Open the file in binary mode
            with open(file_path, 'rb') as file:
                # Create a hasher for the hash algorithm
                hasher = getattr(hashlib, hash_algorithm)()
                # Read a block from the file
                buffer = file.read(block_size)
                # Track the number of bytes processed
                processed_bytes = 0
                # Loop while there is data in the buffer
                while len(buffer) > 0:
                    # If the process has been cancelled, break from the loop
                    if self.cancelled:
                        break
                    # Update the hasher with the data from the buffer
                    hasher.update(buffer)
                    # Update the number of processed bytes
                    processed_bytes += len(buffer)
                    # Read the next block from the file
                    buffer = file.read(block_size)
                    # Emit a signal to update the file being processed
                    self.processing_file.emit(os.path.basename(file_path))
            # Return the hexdigest of the hash, the file size, and no error
            return hasher.hexdigest(), file_size, None
        except Exception as e:
            # If an exception occurred, return none for the hash and the error message
            error_message = f"Error processing file '{os.path.normpath(file_path)}': {str(e)}"
            return None, file_size, error_message

    # Define a method to calculate the hashes of the files in a zip archive from its path
    def calculate_zip_hashes_from_path(self, zip_path):
        try:
            # Open the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Calculate the hashes of the files in the zip archive
                hashes, errors, empty_files_zip, empty_dirs_zip = self.calculate_zip_hashes(zip_ref, zip_path)
                # Get the size of the zip file
                file_size = os.path.getsize(zip_path)
                # Calculate the hash of the zip file itself
                zip_hash_value, _, _ = self.calculate_file_hash(zip_path)
                # Create a list of the hashes starting with the hash of the zip file itself
                file_hashes = [[os.path.normpath(zip_path), zip_hash_value, file_size]] + hashes
                # Return the hashes, errors, and empty files and directories
                return file_hashes, errors, empty_files_zip, empty_dirs_zip
        except Exception as e:
            # If an exception occurred, return an error message
            error_message = f"Error processing zip file '{os.path.normpath(zip_path)}': {str(e)}"
            return [], [(os.path.normpath(zip_path), error_message)], [], []

    # Define a method to calculate the hashes of the files in a zip archive
    def calculate_zip_hashes(self, zip_ref, zip_path):
        # Create empty lists for the hashes, errors, empty files, and empty directories
        file_hashes = []
        error_logs = []
        empty_files_zip = []
        empty_dirs_zip = []

        # Get the name of the hash algorithm in lower case
        hash_algorithm = self.hash_algorithm.lower()

        # Loop over the names of the files in the zip archive
        for file in zip_ref.namelist():
            # If the process has been cancelled, break from the loop
            if self.cancelled:
                break
            # Read the data of the file
            file_data = zip_ref.read(file)
            # If the file is a zip archive itself
            if file.lower().endswith('.zip'):
                # Get the size of the file
                file_size = len(file_data)
                # Create a hasher for the hash algorithm
                hasher = getattr(hashlib, hash_algorithm)()
                # Update the hasher with the data from the file
                hasher.update(file_data)
                # Calculate the hash of the file
                hash_value = hasher.hexdigest()
                # Add the file's path, hash, and size to the list of hashes
                file_hashes.append([os.path.normpath(zip_path + '/' + file), hash_value, file_size])

                try:
                    # Open the nested zip file
                    with zipfile.ZipFile(io.BytesIO(file_data)) as nested_zip:
                        # Calculate the hashes of the files in the nested zip archive
                        hashes, errors, empty_files_nested, empty_dirs_nested = self.calculate_zip_hashes(nested_zip, os.path.normpath(zip_path + '/' + file))
                        # Add the hashes, errors, empty files, and empty directories to the respective lists
                        file_hashes.extend(hashes)
                        error_logs.extend(errors)
                        empty_files_zip.extend(empty_files_nested)
                        empty_dirs_zip.extend(empty_dirs_nested)
                except Exception as e:
                    # If an exception occurred, create an error message
                    error_message = f"Error processing nested zip file '{os.path.normpath(zip_path + '/' + file)}': {str(e)}"
                    # Create a hasher for the hash algorithm
                    nested_zip_hasher = getattr(hashlib, hash_algorithm)()
                    # Update the hasher with the data from the file
                    nested_zip_hasher.update(file_data)
                    # Calculate the hash of the file
                    nested_zip_hash_value = nested_zip_hasher.hexdigest()
                    # Add the file's path, hash, and size to the list of hashes
                    file_hashes.append([os.path.normpath(zip_path + '/' + file), nested_zip_hash_value, len(file_data)])
                    # Add the file's path and error message to the list of errors
                    error_logs.append((os.path.normpath(zip_path + '/' + file), error_message))
            
            # If the file is not a zip archive itself
            else:
                # Get the size of the file
                file_size = len(file_data)
                # If the file is a directory
                if file.endswith('/'):
                    # Check if the directory is empty
                    is_directory_empty = not any(entry for entry in zip_ref.namelist() if entry.startswith(file) and entry != file)
                    # Use "--FOLDER--" as the hash value
                    hash_value = "--FOLDER--"
                    # Use "N/A" as the file size
                    file_size = "N/A"
                    # If the directory is empty, add it to the list of empty directories
                    if is_directory_empty:
                        empty_dirs_zip.append([os.path.normpath(zip_path + '/' + file), hash_value, file_size])
                    # Add the directory's path, hash value, and file size to the list of hashes
                    file_hashes.append([os.path.normpath(zip_path + '/' + file), hash_value, file_size])
                # If the file is not a directory
                else:
                    # Create a hasher for the hash algorithm
                    hasher = getattr(hashlib, hash_algorithm)()
                    # Update the hasher with the data from the file
                    hasher.update(file_data)
                    # Calculate the hash of the file
                    hash_value = hasher.hexdigest()
                    # Add the file's path, hash, and size to the list of hashes
                    file_hashes.append([os.path.normpath(zip_path + '/' + file), hash_value, file_size])

                    # If the file is empty and it's not a directory, add it to the list of empty files
                    if file_size == 0 and not file.endswith('/'):
                        empty_files_zip.append([os.path.normpath(zip_path + '/' + file), hash_value, 0])
            
            # Emit a signal to update the file being processed
            self.processing_file.emit(os.path.basename(file))
        
        # Return the hashes, errors, empty files, and empty directories
        return file_hashes, error_logs, empty_files_zip, empty_dirs_zip


    # Define a method to calculate the hashes of the files in a folder
    def calculate_folder_hashes(self, folder_path):
        # Create empty lists for the hashes, errors, empty files, and empty directories
        file_hashes = []
        error_logs = []
        empty_files_folder = []
        empty_dirs_folder = []

        try:
            # Walk through the files in the folder and its sub-folders
            for root, dirs, files in os.walk(folder_path):
                # If the process has been cancelled, break from the loop
                if self.cancelled:
                    break

                # Append directory info for each subfolder
                dir_hash_value = "--FOLDER--"
                dir_file_size = "N/A"
                file_hashes.append([os.path.normpath(root), dir_hash_value, dir_file_size])

                # Loop over the files
                for file in files:
                    # Get the full path of the file
                    file_path = os.path.join(root, file)
                    # If the file is a zip archive
                    if file_path.lower().endswith('.zip'):
                        # Calculate the hashes of the files in the zip archive
                        hashes, errors, empty_files_zip, empty_dirs_zip = self.calculate_zip_hashes_from_path(file_path)
                        # If the process has been cancelled, break from the loop
                        if self.cancelled:
                            break
                        # Add the hashes, errors, empty files, and empty directories to the respective lists
                        file_hashes.extend(hashes)
                        error_logs.extend(errors)
                        empty_files_folder.extend(empty_files_zip)
                        empty_dirs_folder.extend(empty_dirs_zip)
                        
                        # Emit a signal to update the file being processed
                        self.processing_file.emit(os.path.basename(file_path))
                    
                    # If the file is not a zip archive
                    else:
                        try:
                            # Calculate the hash of the file
                            hash_value, file_size, error = self.calculate_file_hash(file_path)
                            # If the process has been cancelled, break from the loop
                            if self.cancelled:
                                break
                            # If the file is a directory
                            if file.endswith('/'):
                                # Use "--FOLDER--" as the hash value
                                hash_value = "--FOLDER--"
                                # Use "N/A" as the file size
                                file_size = "N/A"
                                # If the directory is empty and there are no other directories or files, add it to the list of empty directories
                                if len(os.listdir(file_path)) == 0 and len(dirs) == 0 and len(files) == 1:
                                    empty_dirs_folder.append([os.path.normpath(file_path), hash_value, file_size])
                                # Add the directory's path, hash value, and file size to the list of hashes
                                file_hashes.append([os.path.normpath(file_path), hash_value, file_size])
                            # If the file is not a directory
                            else:
                                # Create a list with the file's path, hash, and size
                                file_info = [os.path.normpath(file_path), hash_value, file_size]
                                # Add the file info to the list of hashes
                                file_hashes.append(file_info)
                                # If the file is empty, add the file info to the list of empty files
                                if file_size == 0:
                                    self.empty_files.append(file_info)
                                # If there was an error, add the file's path and error to the list of errors
                                elif error:
                                    error_logs.append((os.path.normpath(file_path), error))
                            
                            # Emit a signal to update the file being processed
                            self.processing_file.emit(os.path.basename(file_path))
                        except Exception as e:
                            # If an exception occurred, create an error message
                            error_message = f"Error processing file '{os.path.normpath(file_path)}': {str(e)}"
                            # Add the error message to the list of errors
                            error_logs.append(error_message)


        except Exception as e:
            # If an exception occurred, create an error message
            error_message = f"Error walking through folder '{os.path.normpath(folder_path)}': {str(e)}"
            # Add the error message to the list of errors
            error_logs.append(error_message)

        # Return the hashes, errors, empty files, and empty directories
        return file_hashes, error_logs, empty_files_folder, empty_dirs_folder


# main window of program
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Initialize the hashing thread
        self.hashing_thread = None
        # Initialize the folder path
        self.folder_path = ""
        # Set processing flag as False
        self.processing = False
        
        # Call update_long_paths_label to initialize the label based on the current system settings
        self.update_long_paths_label()

    # The method that initializes the UI of the main window
    def init_ui(self):
        # Set the window title
        self.setWindowTitle('FileReceipt - [Development Version - For Testing Only]')

        # Get screen dimensions
        screen = QDesktopWidget().screenGeometry()

        # Calculate desired height for the window, ensuring a minimum of 400 pixels
        desired_height = max(int(screen.height() * 0.3), 400)

        # Convert desired_height to an integer before performing the multiplication
        desired_width = int(desired_height * 2.5)

        # Resize the window based on calculated dimensions
        self.resize(desired_width, desired_height)

        # Path to the window icon
        icon_path = resource_path("fricon.png")
        # Set the window icon
        self.setWindowIcon(QIcon(icon_path))

        # Create main layout for the window
        main_layout = QVBoxLayout(self)
        # Set the main layout for the window
        self.setLayout(main_layout)

        # Create top and bottom layout
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        # Add the top and bottom layout to the main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        # Create left and right layout
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Add the left and right layout to the top layout, with weight 4 and 2 respectively
        top_layout.addLayout(left_layout, 3)
        top_layout.addLayout(right_layout, 1)

        # Create a FileList widget
        self.drop_list = FileList()
        # Add the FileList widget to the left layout
        left_layout.addWidget(self.drop_list)

        # Create the 'Remove Selected' button
        remove_button = QPushButton('Remove Selected')
        # Connect the button's clicked signal to the remove_files method
        remove_button.clicked.connect(self.remove_files)
        # Create the 'Remove All' button
        remove_all_button = QPushButton('Remove All')
        # Connect the button's clicked signal to the remove_all_files method
        remove_all_button.clicked.connect(self.remove_all_files)

        # Create a layout for the remove buttons
        remove_layout = QHBoxLayout()
        # Add the remove buttons to the remove_layout
        remove_layout.addWidget(remove_button)
        remove_layout.addWidget(remove_all_button)

        # Add the remove_layout to the left_layout
        left_layout.addLayout(remove_layout)

        # Create a DropZone widget
        self.drop_zone = DropZone(self)
        # Add the DropZone widget to the right layout
        right_layout.addWidget(self.drop_zone)

        # Create the 'Browse for Files' button
        button = QPushButton('Browse for Files')
        # Connect the button's clicked signal to the select_files method
        button.clicked.connect(self.select_files)
        # Add the 'Browse for Files' button to the right layout
        right_layout.addWidget(button)

        # Create the 'Generate FileReceipt' button and set its style
        self.run_button = QPushButton('Generate FileReceipt')
        # Set the CSS style for the run_button
        self.run_button.setStyleSheet('''
            QPushButton {
                background-color: lightgreen;
            }
            QPushButton:hover {
                background-color: #32CD32;
            }
        ''')
        # Connect the button's clicked signal to the toggle_processing method
        self.run_button.clicked.connect(self.toggle_processing)
        # Add the 'Generate FileReceipt' button to the right layout
        right_layout.addWidget(self.run_button)

        # Label for the Hash Algorithm dropdown
        algorithm_label = QLabel('Hash Algorithm:')
        # Create a QComboBox for the Hash Algorithms
        algorithm_dropdown = QComboBox()
        # Add all the hash algorithms to the dropdown
        algorithm_dropdown.addItem('SHA256')
        algorithm_dropdown.addItem('SHA512')
        algorithm_dropdown.addItem('SHA1')
        algorithm_dropdown.addItem('MD5')
        algorithm_dropdown.addItem('SHA3_224')
        algorithm_dropdown.addItem('SHA3_256')
        algorithm_dropdown.addItem('SHA3_384')
        algorithm_dropdown.addItem('SHA3_512')
        algorithm_dropdown.addItem('BLAKE2s')
        algorithm_dropdown.addItem('BLAKE2b')
        # Set the default hash algorithm
        algorithm_dropdown.setCurrentText('SHA256')

        # Function to show hash algorithm information message box
        def show_message_box(self):
            message_box = HashInfoMessageBox()
            message_box.exec_()

        # Create a QLabel with a hyperlink
        algorithm_link = QLabel('<a href="#">What is this?</a>')
        # Don't allow external links
        algorithm_link.setOpenExternalLinks(False)
        # Set the text format to RichText
        algorithm_link.setTextFormat(Qt.RichText)
        # Allow text interaction for the hyperlink
        algorithm_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # Set fixed size policy for the hyperlink
        algorithm_link.setFixedSize(algorithm_link.sizeHint())
        algorithm_link.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Connect the hyperlink's activated signal to the show_message_box function
        algorithm_link.linkActivated.connect(show_message_box)

        # Create a QHBoxLayout for the algorithm dropdown and its label
        algorithm_layout = QHBoxLayout()
        # Add the algorithm label, dropdown, and hyperlink to the layout
        algorithm_layout.addWidget(algorithm_label)
        algorithm_layout.addWidget(algorithm_dropdown)
        algorithm_layout.addWidget(algorithm_link)
        # Add stretch to the layout
        algorithm_layout.addStretch(1)

        # Set the layout's margins to 0
        algorithm_layout.setContentsMargins(0, 0, 0, 0)

        # Add the algorithm layout to the right layout
        right_layout.addLayout(algorithm_layout)

        # Save a reference to the algorithm dropdown
        self.algorithm_dropdown = algorithm_dropdown

        # Create a QVBoxLayout for the progress bar and its label
        progress_layout = QVBoxLayout()
        # Add the progress layout to the right layout
        right_layout.addLayout(progress_layout)

        # Create a QLabel for the processing text
        self.processing_label = QLabel('Processing:')
        # Set a minimum width for the label
        min_label_width = int(desired_width * 0.3)
        # Set the minimum width of the label
        self.processing_label.setMinimumWidth(min_label_width)
        # Align the label's text to the left
        self.processing_label.setAlignment(Qt.AlignLeft)
        # Set the label's size policy
        self.processing_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        # Add the processing label to the progress layout
        progress_layout.addWidget(self.processing_label)

        # Create a QProgressBar widget for displaying the progress
        self.progress_bar = QProgressBar()
        # Add the progress bar to the progress layout
        progress_layout.addWidget(self.progress_bar)

        # Set the spacing between items in the progress layout to 0
        progress_layout.setSpacing(0)
        # Set the contents margins of the progress layout to 0
        progress_layout.setContentsMargins(0, 0, 0, 0)

        # Set the initial value of the progress bar to 0
        self.progress_bar.setValue(0)

        # Create a QHBoxLayout for the bottom toolbar
        bottom_toolbar_layout = QHBoxLayout()
        # Set the margins for the bottom toolbar
        bottom_toolbar_layout.setContentsMargins(0, 15, 0, 0)
        # Add the bottom toolbar layout to the bottom layout
        bottom_layout.addLayout(bottom_toolbar_layout)

        # Create a QLabel for the 'Visit GitHub' label
        label = QLabel('Visit GitHub for more information:')
        # Add the label to the bottom toolbar layout
        bottom_toolbar_layout.addWidget(label)

        # Create a QLabel with a hyperlink to the GitHub repository
        hyperlink = QLabel('<a href="https://github.com/btc-git/FileReceipt">github.com/btc-git/FileReceipt</a>')
        # Allow opening external links
        hyperlink.setOpenExternalLinks(True)
        # Connect the hyperlink's activated signal to the open_link method
        hyperlink.linkActivated.connect(self.open_link)
        # Add the hyperlink to the bottom toolbar layout
        bottom_toolbar_layout.addWidget(hyperlink)

        # Add a stretchable space to push the next widgets to the center
        bottom_toolbar_layout.addStretch(1)

        # Create a QLabel for the "Long file paths are enabled" label
        self.long_paths_label = QLabel('Long file paths are: [Undetected!].')

        # Add the "Long file paths are enabled" label to the bottom toolbar layout
        bottom_toolbar_layout.addWidget(self.long_paths_label)

        # Create a QLabel with a hyperlink to explain the meaning of "?"
        question_label = QLabel('<a href="#">Help?</a>')
        # Don't allow external links
        question_label.setOpenExternalLinks(False)
        # Set the text format to RichText
        question_label.setTextFormat(Qt.RichText)
        # Allow text interaction for the hyperlink
        question_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # Connect the hyperlink's activated signal to the show_long_paths_message_box method
        question_label.linkActivated.connect(self.show_long_paths_message_box)

        # Add the "?" hyperlink to the bottom toolbar layout
        bottom_toolbar_layout.addWidget(question_label)

        # Add a stretchable space to push the next widgets to the center
        bottom_toolbar_layout.addStretch(1)

        # Create a QLabel for the version and license information
        version_label = QLabel('License: <a href="#">GNU GPLv3</a>')
        # Don't allow external links
        version_label.setOpenExternalLinks(False)
        # Set the text format to RichText
        version_label.setTextFormat(Qt.RichText)
        # Connect the version_label's activated signal to the show_license method
        version_label.linkActivated.connect(self.show_license)
        # Add the version label to the bottom toolbar layout
        bottom_toolbar_layout.addWidget(version_label)

    # Function to show long paths information message box
    def show_long_paths_message_box(self):
        message_box = LongPathsMessageBox()
        message_box.exec_()


    # This function is used to update the long file paths label text based on the current system settings
    def update_long_paths_label(self):
        long_paths_enabled = self.check_long_paths_enabled()
        if long_paths_enabled:
            self.long_paths_label.setText("Long file paths: Enabled")
        else:
            self.long_paths_label.setText("Long file paths: NOT Enabled!")

    # This function is used to check if long file paths are enabled on the system
    def check_long_paths_enabled(self):
        try:
            command = "powershell Get-ItemPropertyValue HKLM:\\System\\CurrentControlSet\\Control\\Filesystem LongPathsEnabled"
            result = subprocess.check_output(command, shell=True, text=True).strip()
            return result == "1"
        except subprocess.CalledProcessError as e:
            print(f"Error executing PowerShell command: {e}")
            return False




    def show_license(self):
        # Create a LicenseMessageBox instance
        message_box = LicenseMessageBox()
        # Execute the message box
        message_box.exec_()


    def open_link(self, url):
        # Open the specified URL
        QDesktopServices.openUrl(QUrl(url))


    def remove_files(self):
        # Check if processing is ongoing
        if self.processing:
            return
        # Remove selected files from the drop list
        for item in self.drop_list.selectedItems():
            self.drop_list.file_paths.remove(item.text())
            self.drop_list.takeItem(self.drop_list.row(item))


    def remove_all_files(self):
        # Check if processing is ongoing
        if self.processing:
            return
        # Clear all files from the drop list
        self.drop_list.clear()
        self.drop_list.file_paths.clear()


    def select_files(self):
        # Check if processing is ongoing
        if self.processing:
            return
        # Open a file dialog to select files
        file_paths, _ = QFileDialog.getOpenFileNames()
        # Add the selected files to the drop list
        self.drop_list.addItemsFromUrls([QUrl.fromLocalFile(os.path.normpath(fp)) for fp in file_paths])


    def toggle_processing(self):
        if self.processing:
            self.cancel_processing()
        else:
            self.start_processing()


    def start_processing(self):
        if self.drop_list.count() == 0:
            QMessageBox.warning(self, 'FileReceipt', 'Please select files to generate FileReceipt.')
            return

        # Open a folder dialog to choose the location to save the FileReceipt
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.DirectoryOnly)
        folder_dialog.setWindowTitle('Choose where FileReceipt will be saved...')
        folder_dialog.setOptions(QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        folder_path = folder_dialog.getExistingDirectory(self, 'Choose where FileReceipt will be saved...')

        # Check if a folder path was selected
        if not folder_path:
            QMessageBox.warning(self, 'FileReceipt', 'Please select a location to save the FileReceipt.')
            return

        # Set the folder path and update the processing state
        self.folder_path = folder_path
        self.processing = True

        # Disable drop list and drop zone during processing
        self.drop_list.setEnabled(False)
        self.drop_zone.setEnabled(False)

        # Disable buttons during processing, except for the run button
        for button in self.findChildren(QPushButton):
            if button != self.run_button:
                button.setEnabled(False)

        # Disable the algorithm dropdown during processing
        self.algorithm_dropdown.setEnabled(False)

        # Get the selected hash algorithm
        hash_algorithm = HASH_ALGORITHMS[self.algorithm_dropdown.currentText().lower()]
        # Create a list of file paths from the drop list
        file_paths = list(self.drop_list.file_paths)
        # Create a HashingThread instance for computing file hashes
        self.hashing_thread = HashingThread(file_paths, self.algorithm_dropdown.currentText())
        # Connect the hashing thread signals to update the progress and processing label
        self.hashing_thread.progress.connect(self.update_progress)
        self.hashing_thread.processing_file.connect(self.update_processing_label)
        # Connect the hashing thread's finished signal to process the hash results and enable buttons
        self.hashing_thread.finished.connect(self.process_hash_results)
        self.hashing_thread.finished.connect(self.enable_buttons)
        # Start the hashing thread
        self.hashing_thread.start()

        # Update the run button's text and style to indicate cancellation
        self.run_button.setText('Cancel')
        self.run_button.setStyleSheet('background-color: red;')


    # This function is used to cancel the processing task if required.
    def cancel_processing(self):
        # If the hashing_thread exists
        if self.hashing_thread:
            # Set the 'cancelled' flag of the hashing_thread to True
            self.hashing_thread.cancelled = True
            # Display an information box stating that the generation has been cancelled
            QMessageBox.information(self, 'FileReceipt Cancelled', f'FileReceipt generation has been cancelled.')
            # Enable all buttons in the GUI
            for button in self.findChildren(QPushButton):
                button.setEnabled(True)
            # Enable all combo boxes in the GUI
            for combo_box in self.findChildren(QComboBox):
                combo_box.setEnabled(True)     

        # Reset the progress bar value to 0
        self.progress_bar.setValue(0)
        # Reset the processing label text to 'Processing:'
        self.processing_label.setText('Processing:')

    # This function is used to enable the GUI buttons
    def enable_buttons(self):
        # Enable drop_list, drop_zone, and the main window
        self.drop_list.setEnabled(True)
        self.drop_zone.setEnabled(True)
        self.setEnabled(True)
        # Set processing to False
        self.processing = False

        # Change run_button text to 'Generate FileReceipt' and update its style
        self.run_button.setText('Generate FileReceipt')
        self.run_button.setStyleSheet('''
            QPushButton {
                background-color: lightgreen;
            }
            QPushButton:hover {
                background-color: #32CD32;
            }
        ''')

        # Enable all buttons that are not the run_button
        for button in self.findChildren(QPushButton):
            if button != self.run_button:
                button.setEnabled(True)
        # Enable the algorithm_dropdown
        self.algorithm_dropdown.setEnabled(True)
                
    # This function is used to update the progress bar value
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # This function is used to update the processing label with the name of the file being processed
    def update_processing_label(self, file_name):
        self.processing_label.setText(f'Processing: {file_name}')

    # This function is used to process the hash results of the files
    def process_hash_results(self, file_hashes, error_logs, empty_files, empty_dirs):
        # If the hashing_thread was not cancelled
        if not self.hashing_thread.cancelled:
            # Generate a unique folder_name based on the current timestamp
            folder_name = f'FileReceipt-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
            # Create the full path for the new folder
            folder_path = os.path.join(self.folder_path, folder_name)
            # Create the new folder (and any intermediate directories) if they don't already exist
            os.makedirs(folder_path, exist_ok=True)

            # Define the paths for the txt and csv files that will be created
            txt_file_path = os.path.join(folder_path, f'{folder_name}.txt')
            csv_file_path = os.path.join(folder_path, f'{folder_name}.csv')

            # Sort the file_hashes list by the first element of each tuple (the file path)
            file_hashes.sort(key=lambda x: x[0])

            # Get the selected hash algorithm
            hash_algorithm = self.algorithm_dropdown.currentText()

            # write catalog information to csv file - added io.open and encoding to address emojis in file paths
            with io.open(txt_file_path, 'w', encoding='utf-8') as file:
                # Write the catalog header to the text file
                file.write(f"Catalog of selected files (Path, File Hash [{hash_algorithm}], File Size [bytes]):\n")

                # Write the file information for each file in the file_hashes list
                for hash_info in file_hashes:
                    file.write(f'{os.path.normpath(hash_info[0])}: {hash_info[1]} Size: {hash_info[2]} bytes\n')
                # Add extra new lines for separation
                file.write("\n" * 3)

                # Write the errors section header to the text file
                file.write("Errors:\n")
                if error_logs:
                    # Write each error to the text file
                    for error in error_logs:
                        # Use os.path.normpath() to ensure the paths are displayed correctly
                        file.write(f'{os.path.normpath(error[0])}: {error[1]}\n')
                        file.write('\n')
                else:
                    # Write a message indicating no errors were recorded
                    file.write("No errors were recorded.\n")

                # Add a new line for separation
                file.write('\n')

                # Write the empty files section header to the text file
                file.write("Empty files:\n")
                if empty_files:
                    # Write the information of each empty file to the text file
                    for file_info in empty_files:
                        file.write(f'{os.path.normpath(file_info[0])}: {file_info[1]} Size: {file_info[2]} bytes\n')
                    # Add a new line for separation
                    file.write('\n')
                else:
                    # Write a message indicating no empty files were found
                    file.write("No empty files were found.\n")
                    file.write('\n')

                # Write the empty directories section header to the text file
                file.write("Empty folders:\n")
                if empty_dirs:
                    # Write the information of each empty directory to the text file
                    for dir_info in empty_dirs:
                        file.write(f'{os.path.normpath(dir_info[0])}: {dir_info[1]} Size: {dir_info[2]}\n')
                else:
                    # Write a message indicating no empty directories were found
                    file.write("No empty folders were found.\n")

                # Find duplicate files based on their hashes
                duplicates = self.find_duplicates(file_hashes)
                # Write the duplicates section header to the text file
                file.write("\nFiles with matching hashes:\n")
                if duplicates:
                    # Write the information of each group of duplicate files to the text file
                    for duplicate_group in duplicates:
                        for duplicate in duplicate_group:
                            file.write(f'{os.path.normpath(duplicate[0])}: {duplicate[1]} Size: {duplicate[2]} bytes\n')
                        # Add a new line for separation between duplicate groups
                        file.write('\n')
                else:
                    # Write a message indicating no duplicates were found
                    file.write("No duplicates were found.\n")

                # Add extra new lines for separation
                file.write("\n\n")

                # Get and format local timezone
                local_timezone = get_localzone()
                current_time = datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")

                file.write("Date/Time Generated:\n")
                file.write(current_time + "\n")

            # write catalog information to csv file
            with io.open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write the catalog header to the CSV file
                writer.writerow(["Catalog of Selected Files [Path]:", f"File Hash [{hash_algorithm}]:", "File Size [bytes]:"])

                # Write the file information for each file in the file_hashes list as a row in the CSV file
                for hash_info in file_hashes:
                    writer.writerow([os.path.normpath(hash_info[0]), hash_info[1], hash_info[2]])
                # Add empty rows for separation
                writer.writerow([] * 3)

                # Write the errors section header to the CSV file
                writer.writerow(["Errors:"])
                if error_logs:
                    # Write each error as a row in the CSV file
                    for error in error_logs:
                        # Use os.path.normpath() to ensure the paths are displayed correctly
                        writer.writerow([os.path.normpath(error[0]), error[1]])
                        writer.writerow([])
                else:
                    # Write a message indicating no errors were recorded
                    writer.writerow(["No errors were recorded."])
                    writer.writerow([])

                # Write the empty files section header to the CSV file
                writer.writerow(["Empty files:"])
                if empty_files:
                    # Write the information of each empty file as a row in the CSV file
                    for file_info in empty_files:
                        writer.writerow([os.path.normpath(file_info[0]), file_info[1], file_info[2]])
                    writer.writerow([])
                else:
                    # Write a message indicating no empty files were found
                    writer.writerow(["No empty files were found."])
                    writer.writerow([])

                # Write the empty directories section header to the CSV file
                writer.writerow(["Empty folders:"])
                if empty_dirs:
                    # Write the information of each empty directory as a row in the CSV file
                    for dir_info in empty_dirs:
                        writer.writerow([os.path.normpath(dir_info[0]), dir_info[1], dir_info[2]])
                    writer.writerow([])
                else:
                    # Write a message indicating no empty directories were found
                    writer.writerow(["No empty folders were found."])
                    writer.writerow([])

                # Write the duplicates section header to the CSV file
                writer.writerow(["Files with matching hashes:"])
                if duplicates:
                    # Write the information of each group of duplicate files as rows in the CSV file
                    for duplicate_group in duplicates:
                        for duplicate in duplicate_group:
                            writer.writerow([os.path.normpath(duplicate[0]), duplicate[1], duplicate[2]])
                        writer.writerow([])
                else:
                    # Write a message indicating no duplicates were found
                    writer.writerow(["No duplicates were found."])

                # Add empty rows for separation
                writer.writerow([] * 2)

                # Get and format local timezone
                local_timezone = get_localzone()
                current_time = datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")

                writer.writerow(["Date/Time Generated:"])
                writer.writerow([current_time])

            # Set the progress bar value to 100% to indicate completion
            self.progress_bar.setValue(100)

            # Normalize the folder path
            folder_path = os.path.normpath(folder_path)
            # Show a message box indicating the completion and providing the folder path
            message_box = FinishedMessageBox(folder_path)
            message_box.exec_()

            # Open the folder containing the generated FileReceipt
            self.open_folder(folder_path)
            
        # Set the processing label text back to 'Processing:' and reset the progress bar value to 0
        self.processing_label.setText('Processing:')
        self.progress_bar.setValue(0)

    # This function is used to find duplicate files based on their hashes
    def find_duplicates(self, file_hashes):
        # Create a dictionary to store the count of each hash
        hash_counts = {}
        # Loop through each file_hash tuple in the file_hashes list
        for hash_info in file_hashes:
            # If the file size is not 0 and it's not a directory
            if hash_info[2] != 0 and hash_info[1] != "--FOLDER--":
                # Get the hash value
                hash_value = hash_info[1]
                # If the hash_value is already in the hash_counts dictionary, append the hash_info to the list
                if hash_value in hash_counts:
                    hash_counts[hash_value].append(hash_info)
                # If the hash_value is not in the hash_counts dictionary, add it with a list containing the hash_info
                else:
                    hash_counts[hash_value] = [hash_info]
        # Return a list of all hash_info lists that have more than 1 element (indicating a duplicate file)
        return [duplicate_group for duplicate_group in hash_counts.values() if len(duplicate_group) > 1]


    # This function is used to open the specified folder
    def open_folder(self, folder_path):
        # Get the operating system name
        system = platform.system()
        # Open the folder using the appropriate command based on the operating system
        if system == 'Windows':
            os.startfile(folder_path)
        elif system == 'Darwin':
            subprocess.Popen(['open', folder_path])
        elif system == 'Linux':
            subprocess.Popen(['xdg-open', folder_path])

    # This function is called when the window is closed
    def closeEvent(self, event):
        # If the hashing_thread exists
        if self.hashing_thread is not None:
            # Set the 'cancelled' flag of the hashing_thread to True
            self.hashing_thread.cancelled = True
        # Accept the close event
        event.accept()

# If the script is run directly (and not imported as a module)
if __name__ == '__main__':
    # Create a QApplication
    app = QApplication(sys.argv)
    # Create a MainWindow
    window = MainWindow()
    # Show the MainWindow
    window.show()
    # Enter the QApplication's main event loop, and exit when it is done
    sys.exit(app.exec_())
