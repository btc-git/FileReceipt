import os
from PyQt5.QtWidgets import QLabel, QListWidget, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent


class DropZone(QLabel):
    """Drag and drop zone for files and folders."""
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
        # Set the text for this QLabel to guide users to drag and drop
        # files and folders - split onto multiple lines
        self.setText("\nDrag and Drop Files\nand Folders Here\n")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        self.parent().drop_list.addItemsFromUrls(event.mimeData().urls())


class FileList(QListWidget):
    """File list box for files to be processed."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set this QListWidget to accept drops
        self.setAcceptDrops(True)
        # Initialize the file_paths as an empty set
        self.file_paths = set()
        # Set the selection mode for this QListWidget to allow multiple
        # items to be selected
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Create a font with the desired font size
        font = self.font()
        font.setPointSize(12)  # Set your desired font size here
        self.setFont(font)  # Set the modified font to the QListWidget

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        self.addItemsFromUrls(event.mimeData().urls())

    def addItemsFromUrls(self, urls):
        """Add items to the list from URLs."""
        # Get the local file paths from the URLs
        file_paths = [url.toLocalFile() for url in urls]
        # Normalize the file paths
        normalized_paths = [
            os.path.normpath(file_path) for file_path in file_paths
        ]
        # Get the new paths that are not already in self.file_paths
        new_paths = set(normalized_paths) - self.file_paths
        # Update self.file_paths with the new paths
        self.file_paths.update(new_paths)
        # Clear the items in this QListWidget
        self.clear()
        # Add the file paths to this QListWidget
        self.addItems(list(self.file_paths))
