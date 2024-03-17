### * Program under development. Current version is for testing only. (3/17/2024) *

# FileReceipt
FileReceipt is a program that quickly catalogs user-selected files and folders. It creates a precise inventory of files that are nested within folders, subfolders, and zip files, eliminating the need for time-consuming manual inspection and documentation. It also calculates a hash value for each file, which can help verify that files are original, identical, and unaltered.

Having a record of files transferred between parties can be useful for coordination and resloving disputes. For example, the sender can create a FileReceipt before sending (or use [another method](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-7.3) to catalog information), creating a record of what they're sending. Similarly, the receiver can create a FileReceipt upon receipt to document what they've received. These two catalogs can be compared to ensure consistency and can be regenerated at any point to verify both parties possess identical files. [File verification](https://en.wikipedia.org/wiki/File_verification) using [cryptographic hash functions](https://en.wikipedia.org/wiki/Cryptographic_hash_function) is a [reliable and widely accepted](https://csrc.nist.gov/Projects/Hash-Functions) method to [ensure data integrity](https://learn.microsoft.com/en-us/dotnet/standard/security/ensuring-data-integrity-with-hash-codes).

Click [here](https://github.com/btc-git/FileReceipt/raw/main/FileReceipt.exe) to download the latest version (9/1/2023).

<p align="center">
  <img src="https://crimlawtech.com/FileReceiptScreenshot.PNG" alt="FileReceipt Screenshot" width="90%">
</p>

### FileReceipt records the following information for each file:

- File Path
- File Name
- File Hash
- File Size
- Folder Path
- Folder Name

### FileReceipt also records:
- Errors encountered during processing
- Empty Files (0 bytes)
- Empty Folders (0 items)
- Files with matching hashes

## Usage

To use FileReceipt:
1. Add files and folders to the file list box by either dragging and dropping or clicking the "Browse for Files" button.
2. Once files have been added to the list, click "Generate FileReceipt" and select a location to save the FileReceipt.
3. After the processing is complete, a folder will open containing a text file and a CSV file (spreadsheet) that both contain the same catalog information in different formats.

FileReceipt works [recursively](https://en.wikipedia.org/wiki/Recursion_(computer_science)), meaning if you add a folder or zip file to the list, it will search inside and catalog all the files, folders, and zip files within it. By adding the top-level folder or zip file, you can catalog the entire directory structure and contents of everything nested inside.

FileReceipt calculates a [hash value](https://en.wikipedia.org/wiki/Cryptographic_hash_function) for each file that it catalogs. This value is unique to the file and can be used to demonstrate that files are identical or have not changed over time. Once a hash value has been calculated, it can be recalculated again at any time and will remain the same as long as the file has not changed. If the hash value differs on any subsequent recalculation, it means the files are no longer the same.

FileReceipt uses hash algorithm [SHA-256](https://en.wikipedia.org/wiki/SHA-2) by default, but can be changed to use SHA-512, SHA-1, MD5, or other common algorithms. Changing the hash algorithm may be necessary to coordinate with other programs or individuals. When comparing files, in order for the hash values of identical files to match, the same hash algorithm must be used.

#### NOTE: Enable the "Long File Path" option in Windows for most accurate results.
By default, Windows imposes a limit on the length of file paths and names, restricting them to approximately 260 characters combined. If a file path exceeds this limit due to long folder names or file names, some programs will not be able to open the file, even if the file is visible in Windows File Explorer.

| ---------------- File Path ----------------- || ----- File Name ----- |

C:\DocumentsFolder\WorkProjectsFolder\SampleDocument.PDF

| ---------- Total File Path Length: 56 Characters Long ----------- |

To overcome this limitation, the "Long File Paths" option must be manually enabled in Windows. If this option is not enabled, FileReceipt will not correctly catalog files with long file paths and may record errors or omit files from the catalog.

WARNING: Modifying the Windows Registry can be dangerous and render your computer unusable. Seek assistance from your IT department or proceed with caution before making changes.

Visit the following pages for information and instructions on enabling "Long File Paths":
   - [Long File Paths in Windows](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry)
   - [Enabling Long File Paths](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html)

## Download (for most users)

Download the latest version of FileReceipt on GitHub [here](https://github.com/btc-git/FileReceipt/raw/main/FileReceipt.exe). (3/17/2023)
- You may receive a [warning](https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/) when you run the program for the first time. To bypass the warning, click 'More info' and then 'Run anyway.' The program has been submitted to Microsoft and cleared their Smart Screen security analysis, which should make the warnings go away eventually.

## Build (for developers)

Prerequisites: [Python 3.x](https://www.python.org/) and [PyQt5](https://pypi.org/project/PyQt5/)

Source Code: All FileReceipt source code and files are on the GitHub [repository](https://github.com/btc-git/FileReceipt).

### Windows Build Instructions (macOS build coming soon)
1. Install Python 3.x: 
   - Download Python 3.x from the official Python [website](https://www.python.org/downloads/).
   - Follow the installation instructions provided by the Python installer.
2. Install PyQt5:
   - Open a command prompt or terminal.
   - Run the following command to install PyQt5:
     ```
     pip install pyqt5
     ```
3. Build the standalone executable:
   - Open a command prompt or terminal.
   - Navigate to the directory where you have the FileReceipt.py and other repository files located.
   - Run the following command to build the standalone executable using PyInstaller:
     ```
     pyinstaller --onefile --windowed --icon=C:\FileReceipt\fricon.ico --add-data "fricon.png;." --add-data "license.txt;." FileReceipt.py
     ```
   Note: Replace `C:\FileReceipt\fricon.ico` with the actual path to your fricon.ico file.

## Update History
3/17/2024 - Changed zip file processing to utilize disk space (temp file) instead of RAM to avoid crashing when processing very large files. Added a threshold preventing recursive cataloging of zip files containing more than 1000 files.

## License
FileReceipt is licensed under the GNU General Public License v3.0.
See the [LICENSE](https://github.com/btc-git/FileReceipt/blob/main/LICENSE.txt) file in the project for the full license text.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Contact
Brian@CrimLawTech.com

Copyright (c) 2023 Brian Cummings
