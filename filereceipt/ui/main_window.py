import os
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QProgressBar, QFileDialog, QMessageBox, QDesktopWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from ..config import HASH_ALGORITHM_DISPLAY_NAMES
from ..utils import resource_path, open_folder
from ..hashing import HashingThread
from ..csv_writer import write_results_to_csv
from .dialogs import (
    LongPathsMessageBox, HashInfoMessageBox, ThresholdInfoMessageBox,
    LicenseMessageBox, FinishedMessageBox
)
from .widgets import DropZone, FileList


class MainWindow(QWidget):
    """Main application window for FileReceipt."""
    
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

    def init_ui(self):
        """Initialize the UI of the main window."""
        # Set the window title
        self.setWindowTitle('FileReceipt - [Development Version - For Testing Only]')

        # Get screen dimensions
        screen = QDesktopWidget().screenGeometry()

        # Calculate desired height for the window, ensuring a minimum of 400 pixels
        desired_height = max(int(screen.height() * 0.35), 400)

        # Convert desired_height to an integer before performing the multiplication
        desired_width = int(desired_height * 2.5)

        # Resize the window based on calculated dimensions
        self.resize(desired_width, desired_height)

        # Path to the window icon
        icon_path = resource_path("fricon.ico")
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

        # Add the left and right layout to the top layout, with weight 3 and 1 respectively
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
        for algo_name in HASH_ALGORITHM_DISPLAY_NAMES:
            algorithm_dropdown.addItem(algo_name)
        # Set the default hash algorithm
        algorithm_dropdown.setCurrentText('SHA256')

        # Function to show hash algorithm information message box
        def show_message_box(self):
            message_box = HashInfoMessageBox()
            message_box.exec_()

        # Create a QLabel with a hyperlink
        algorithm_link = QLabel('<a href="#" style="text-decoration: none;">[?]</a>')
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

        # Create the recursion threshold dropdown
        threshold_label = QLabel("Zip Recursion Threshold:")
        self.threshold_dropdown = QComboBox()
        self.threshold_dropdown.addItem("1 (no recursion)", 1)
        self.threshold_dropdown.addItem("10", 10)
        self.threshold_dropdown.addItem("100", 100)
        self.threshold_dropdown.addItem("1000", 1000)
        self.threshold_dropdown.addItem("Off (no limit)", -1)
        # Set default to 1000
        self.threshold_dropdown.setCurrentIndex(3)

        # Create a QLabel with a hyperlink for the threshold dropdown
        threshold_link = QLabel('<a href="#" style="text-decoration: none;">[?]</a>')
        # Don't allow external links
        threshold_link.setOpenExternalLinks(False)
        # Set the text format to RichText
        threshold_link.setTextFormat(Qt.RichText)
        # Allow text interaction for the hyperlink
        threshold_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # Set fixed size policy for the hyperlink
        threshold_link.setFixedSize(threshold_link.sizeHint())
        threshold_link.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Connect the hyperlink's activated signal to the ThresholdInfoMessageBox
        threshold_link.linkActivated.connect(lambda: ThresholdInfoMessageBox(self).exec_())

        # Create a QHBoxLayout for the threshold dropdown and its hyperlink
        threshold_layout = QHBoxLayout()
        # Add the threshold label, dropdown, and hyperlink to the layout
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_dropdown)
        threshold_layout.addWidget(threshold_link)
        # Add stretch to the layout
        threshold_layout.addStretch(1)

        # Add the threshold layout to the right layout
        right_layout.addLayout(threshold_layout)

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
        question_label = QLabel('<a href="#" style="text-decoration: none;">[?]</a>')
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

    def show_long_paths_message_box(self):
        """Show long paths information message box."""
        message_box = LongPathsMessageBox()
        message_box.exec_()

    def update_long_paths_label(self):
        """Update the long file paths label text based on the current system settings."""
        try:
            long_paths_enabled = self.check_long_paths_enabled()
        except subprocess.CalledProcessError as e:
            long_paths_enabled = None
            print(f"Error checking long paths: {e}")

        if long_paths_enabled is None:
            self.long_paths_label.setText("Long file paths: Check failed")
        elif long_paths_enabled:
            self.long_paths_label.setText("Long file paths: Enabled")
        else:
            self.long_paths_label.setText("Long file paths: NOT Enabled!")

    def check_long_paths_enabled(self):
        """Check if long file paths are enabled on the system."""
        try:
            command = "powershell Get-ItemPropertyValue HKLM:\\System\\CurrentControlSet\\Control\\Filesystem LongPathsEnabled"
            result = subprocess.check_output(command, shell=True, text=True).strip()
            return result == "1"
        except subprocess.CalledProcessError as e:
            print(f"Error executing PowerShell command: {e}")
            return False

    def show_license(self):
        """Show the FileReceipt license dialog."""
        message_box = LicenseMessageBox()
        message_box.exec_()

    def open_link(self, url):
        """Open the specified URL."""
        QDesktopServices.openUrl(QUrl(url))

    def remove_files(self):
        """Remove selected files from the drop list."""
        if self.processing:
            return
        for item in self.drop_list.selectedItems():
            self.drop_list.file_paths.remove(item.text())
            self.drop_list.takeItem(self.drop_list.row(item))

    def remove_all_files(self):
        """Remove all files from the drop list."""
        if self.processing:
            return
        self.drop_list.clear()
        self.drop_list.file_paths.clear()

    def select_files(self):
        """Open a file dialog to select files."""
        if self.processing:
            return
        file_paths, _ = QFileDialog.getOpenFileNames()
        self.drop_list.addItemsFromUrls([QUrl.fromLocalFile(os.path.normpath(fp)) for fp in file_paths])

    def toggle_processing(self):
        """Toggle between start and cancel processing."""
        if self.processing:
            self.cancel_processing()
        else:
            self.start_processing()

    def start_processing(self):
        """Start the file processing."""
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

        # Create a list of file paths from the drop list
        file_paths = list(self.drop_list.file_paths)
        
        # Get the recursion threshold value from the dropdown
        threshold_value = self.threshold_dropdown.currentData()
        
        # Create a HashingThread instance with the selected threshold value
        self.hashing_thread = HashingThread(file_paths, self.algorithm_dropdown.currentText(), threshold_value)
        
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

    def cancel_processing(self):
        """Cancel the processing task."""
        if self.hashing_thread:
            # Set the 'cancelled' flag of the hashing_thread to True
            self.hashing_thread.cancelled = True
            self.hashing_thread.wait()  # Ensure the thread completes gracefully
            # Display an information box stating that the generation has been cancelled
            QMessageBox.information(self, 'FileReceipt Cancelled', 'FileReceipt generation has been cancelled.')
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

    def enable_buttons(self):
        """Enable the GUI buttons."""
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

    def update_progress(self, value):
        """Update the progress bar value."""
        self.progress_bar.setValue(value)

    def update_processing_label(self, file_name):
        """Update the processing label with the name of the file being processed."""
        self.processing_label.setText(f'Processing: {file_name}')

    def process_hash_results(self, file_hashes, error_logs, empty_files, empty_dirs):
        """Process the hash results of the files."""
        if not self.hashing_thread.cancelled:
            # Generate a unique file name based on the current timestamp
            file_name = f'FileReceipt-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
            # Create the full path for the CSV file
            csv_file_path = os.path.join(self.folder_path, file_name)

            # Sort the file_hashes list by the first element of each tuple (the file path)
            file_hashes.sort(key=lambda x: x[0])

            # Get the selected hash algorithm and recursion threshold
            hash_algorithm = self.algorithm_dropdown.currentText()
            threshold_value = self.threshold_dropdown.currentData()

            # Write the results to CSV file
            try:
                write_results_to_csv(
                    csv_file_path,
                    file_hashes,
                    error_logs,
                    empty_files,
                    empty_dirs,
                    hash_algorithm,
                    threshold_value
                )
            except Exception as e:
                error_msg = f"Failed to write CSV file: {str(e)}"
                QMessageBox.critical(self, 'FileReceipt Error', error_msg)
                self.progress_bar.setValue(0)
                self.processing_label.setText('Processing:')
                return

            # Set the progress bar value to 100% to indicate completion
            self.progress_bar.setValue(100)

            # Show a message box indicating the completion and providing the CSV file path
            message_box = FinishedMessageBox(csv_file_path)
            message_box.exec_()

            # Open the folder containing the generated CSV file and select the file
            open_folder(csv_file_path)

        # Set the processing label text back to 'Processing:' and reset the progress bar value to 0
        self.processing_label.setText('Processing:')
        self.progress_bar.setValue(0)

    def closeEvent(self, event):
        """Handle window close event."""
        # If the hashing_thread exists
        if self.hashing_thread is not None:
            # Set the 'cancelled' flag of the hashing_thread to True
            self.hashing_thread.cancelled = True
        # Accept the close event
        event.accept()
