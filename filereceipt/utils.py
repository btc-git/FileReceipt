import os
import sys
import platform
import subprocess
import shutil
from PyQt5.QtGui import QIcon


def resource_path(relative_path):
    """Get the correct path for a resource file.
    
    Works whether the script is running as a standalone script or packed 
    into a standalone executable (using tools like PyInstaller).
    
    Args:
        relative_path: Relative path to the resource file
        
    Returns:
        Absolute path to the resource
    """
    # The '_MEIPASS' attribute is set by PyInstaller, and it contains
    # the path to the temporary folder
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # If the script is not running as a standalone executable, then
        # the base path is the current directory
        base_path = os.path.abspath("")
    # Join the base path and the relative path to get the absolute
    # path to the resource
    return os.path.join(base_path, relative_path)


def get_window_icon():
    """Get the window icon using resource_path."""
    icon_path = resource_path("fricon.ico")
    return QIcon(icon_path)


def open_folder(file_path):
    """Open the specified folder and highlight/select the file.
    
    Args:
        file_path: Path to the file or folder to open
    """
    system = platform.system()
    try:
        if system == 'Windows':
            subprocess.Popen(f'explorer /select,"{os.path.normpath(file_path)}"')
        elif system == 'Darwin':
            subprocess.Popen(['open', '-R', file_path])
        elif system == 'Linux':
            if shutil.which('xdg-open'):
                subprocess.Popen(['xdg-open', file_path])
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None, 'Error', 'xdg-open not found. Please install xdg-utils.')
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(None, 'Error', f"Failed to open folder: {e}")
