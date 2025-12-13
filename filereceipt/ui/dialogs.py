import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QTextEdit, QSpacerItem, QSizePolicy, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from ..utils import resource_path


class LongPathsMessageBox(QDialog):
    """Dialog that displays information about long file paths in Windows."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Long File Paths in Windows')
        # Remove context help button in title bar
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package
        # icon in pyinstaller onefile build
        icon_path = resource_path("fricon.ico")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QLabel instance for the main paragraph
        text_label = QLabel(
            'Long file paths must be enabled for accurate results while using '
            'this program.\n\nBy default, Windows imposes a character limit '
            'on the length of file paths and file names, restricting them to '
            'approximately 260 characters in total. If the character limit '
            'is exceeded due to long folder and file names, some programs '
            'will not be able to view or open these files, even if they '
            'are visible in Windows File Explorer.\n\n| -------------------'
            ' File Path ------------------- || ------ File Name ------ '
            '|\n\n C:\\DocumentsFolder\\WorkProjectsFolder\\SampleDocument.PDF'
            '\n\n| ---------- Example File Path Length: 56 Characters Long '
            '---------- |\n\nTo overcome the 260 character limit, the "Long '
            'File Paths" option must be manually enabled in Windows. Without '
            'enabling this setting, FileReceipt, and other programs, will '
            'encounter difficulties consistently opening files within long '
            'file paths. Consequently, when creating a FileReceipt for files '
            'and folders with long paths, failure to enable the "Long File '
            'Paths" setting can lead to error messages and/or the omission '
            'of files from the catalog.\n\nWARNING: Modifying Windows can be '
            'dangerous and may render your computer unusable. Seek assistance '
            'from your IT department and proceed with caution before making '
            'changes.'
        )

        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create a QLabel instance for the sentence with hyperlinks
        link_label = QLabel(
            'Visit the following pages for information and instructions on enabling '
            'Long File Paths: <a href="https://support.cs.jhu.edu/wiki/Windows_Path_Length_Limit_Reached">'
            'Enabling Long File Paths</a> and <a href="https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file#maximum-path-length-limitation">'
            'Long File Paths in Windows</a>.'
        )
        link_label.setWordWrap(True)
        # Set the interaction flags on the QLabel to allow for text browser
        # interactions - allows for clickable links
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


class HashInfoMessageBox(QDialog):
    """Dialog that displays information about hash algorithm selection."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Hash Algorithm Selection')
        # remove context help button in title bar
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package
        # icon in pyinstaller onefile build
        icon_path = resource_path("fricon.ico")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QLabel instance for the main paragraph
        text_label = QLabel(
            'FileReceipt calculates a hash value for each file that it '
            'catalogs. The hash value serves as a unique identifier for '
            'the file.\n\n'
            'By default, FileReceipt utilizes the SHA-256 hash algorithm '
            'to calculate a SHA-256 hash value for each file. However, '
            'other commonly used hash algorithms can be selected from '
            'the dropdown menu. Changing the hash algorithm may be useful '
            'to coordinate with external programs, processes, or '
            'individuals. In order for hash values of identical files to '
            'match, the same hash algorithm must be used to compare files.'
        )
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create a QLabel instance for the sentence with hyperlinks
        link_label = QLabel(
            'For more information, see these pages on '
            '<a href="https://en.wikipedia.org/wiki/File_verification">File Verification</a> '
            'and <a href="https://en.wikipedia.org/wiki/Cryptographic_hash_function">'
            'Cryptographic Hash Functions</a>.'
        )
        link_label.setWordWrap(True)
        # Set the interaction flags on the QLabel to allow for text browser
        # interactions - allows for clickable links
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


class ThresholdInfoMessageBox(QDialog):
    """Dialog that displays information about the recursion threshold."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Recursion Threshold Information')
        # Remove context help button in title bar
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        # Create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Set the path to the icon image
        icon_path = resource_path("fricon.ico")
        self.setWindowIcon(QIcon(icon_path))

        # Create a QLabel instance for the main paragraph
        text_label = QLabel(
            'The "Recursion Threshold" option allows you to control how files within zip archives are processed.\n\n'
            'You can select from the following options:\n'
            '• 1 (no recursion): Skip processing the contents of zip archives entirely.\n'
            '• 10, 100, 1000: Skip processing zip archives with more than the selected number of files.\n'
            '• Off (no limit): Process all files in zip archives, regardless of count.\n\n'
            'When a threshold is set, zip files containing more files than the threshold will be skipped to prevent excessive hash calculations and logging, but the zip file itself will still be added to the catalog. '
            'Note that processing zip files containing many files may take a long time.'
        )
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create close button for window
        ok_button = QPushButton('Close')
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QHBoxLayout()
        # Add stretchable space on right and left of OK button
        ok_button_layout.addStretch(1)
        ok_button_layout.addWidget(ok_button)
        ok_button_layout.addStretch(1)
        layout.addLayout(ok_button_layout)


class LicenseMessageBox(QDialog):
    """Dialog that displays the FileReceipt license."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FileReceipt License: GNU GPLv3')
        # remove context help button in title bar
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        # create layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # set the path to the icon image - also used to package
        # icon in pyinstaller onefile build
        icon_path = resource_path("fricon.ico")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a QScrollArea, make its content resizable, and
        # add it to the layout
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Create a QWidget for the scroll content, and set it as the
        # widget for the scroll area
        scroll_content = QWidget(scroll_area)
        scroll_area.setWidget(scroll_content)

        # Create a QVBoxLayout for the scroll content, and set it as
        # the layout for the scroll content
        content_layout = QVBoxLayout(scroll_content)
        scroll_content.setLayout(content_layout)

        # Create a QTextEdit and set it to read-only mode
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Get the license file path, read its content, and set it as
        # the plain text for the QTextEdit - also used to package
        # icon in pyinstaller onefile build
        file_path = resource_path("LICENSE.txt")
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
            text_edit.setPlainText(file_content)

        # Set the stylesheet for the QTextEdit to define the font size
        text_edit.setStyleSheet("font-size: 11pt;")
        # Add the QTextEdit to the content layout
        content_layout.addWidget(text_edit)

        # Create a QPushButton labeled 'Close', connect its clicked
        # signal to the accept slot, and add it to a layout
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

        # Calculate the window size based on 70% of the screen size,
        # and resize the window accordingly
        window_width = int(screen_geometry.width() * 0.4)
        window_height = int(screen_geometry.height() * 0.6)
        self.resize(QSize(window_width, window_height))


class FinishedMessageBox(QDialog):
    """Dialog that appears when file processing is complete."""
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FileReceipt Complete!')
        # remove context help button in title bar
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        # Create a QVBoxLayout, set its alignment to center, and set
        # it as the layout for this dialog
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # set the path to the icon image - also used to package
        # icon in pyinstaller onefile build
        icon_path = resource_path("fricon.ico")
        # set window using path specified above
        self.setWindowIcon(QIcon(icon_path))

        # Create a spacer item and add it to the layout
        spacer_top = QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addItem(spacer_top)

        # Create a QLabel with a message about where the file receipt was
        # saved, set its word wrap to false, set its stylesheet, and add
        # it to the layout
        text_label = QLabel(
            f'FileReceipt saved to {os.path.normpath(folder_path)}'
        )
        text_label.setWordWrap(False)
        text_label.setStyleSheet("font-size: 11pt;")
        layout.addWidget(text_label)

        # Create another spacer item with expanding vertical size policy and
        # add it to the layout
        spacer_bottom = QSpacerItem(
            20, 20, QSizePolicy.Fixed, QSizePolicy.Expanding
        )
        layout.addItem(spacer_bottom)

        # Create a QHBoxLayout for the button
        button_layout = QHBoxLayout()

        # Create a QPushButton labeled 'Ok', set its size to its recommended
        # size, connect its clicked signal to the accept slot, and add it
        # to the button layout
        ok_button = QPushButton('Ok')
        ok_button.setFixedSize(ok_button.sizeHint())
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)
