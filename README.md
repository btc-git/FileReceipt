### * Program under development. Independently validate all FileReceipt results. (8/23/2023) *

# FileReceipt
FileReceipt is a program that quickly generates a precise catalog of user-selected files, folders, and zip files. It is particularly useful for creating an inventory of files that are nested within folders, subfolders, and zip files, eliminating the need for time-consuming manual inspection and documentation.

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
1. Add files and folders to the file list box by either dragging and dropping them or clicking "Browse for Files".
2. Once files have been added to the list, click "Generate FileReceipt" and select a location to save the FileReceipts.
3. After the processing is complete, a folder will open containing a text file and a CSV file (spreadsheet) that both contain the same catalog information in different formats.

FileReceipt works [recursively](https://en.wikipedia.org/wiki/Recursion_(computer_science)), meaning if you add a folder or zip file to the list, it will search inside and catalog all the files, folders, and zip files within it. By adding the top-level folder or zip file, you can capture the entire directory structure and contents of everything nested inside.

FileReceipt calculates a [hash value](https://en.wikipedia.org/wiki/Cryptographic_hash_function) for each file that it processes. This value is unique to the file and can be used to demonstrate the file is the same and has not been tampered with or changed over time. Once a hash value has been calculated for a file, it can be recalculated again at any time and will remain the same. If the hash value changes on any subsequent recalculation, it means the file is not the same as when the hash value was originally calculated. 

FileReceipt uses hash algorithm [SHA-256](https://en.wikipedia.org/wiki/SHA-2) by default, but can be changed to use SHA-512, SHA-1, MD5, or other common algorithms. Changing the hash algorithm may be necessary to coordinate with other programs or individuals. When comparing files, in order for the hash values of identical files to match, the same hash algorithm must be used.

One application for FileReceipt is resolving disputes over digital files transferred between parties. For example, the sender can generate a FileReceipt before sending (or catalog information another way), creating a record of what they're sending. Similarly, the receiver can create a FileReceipt upon receipt to document what they've actually received. These two catalogs can be compared to ensure consistency and can be regenerated at any point to verify both parties possess identical files. [File verification](https://en.wikipedia.org/wiki/File_verification) using [cryptographic hash functions](https://en.wikipedia.org/wiki/Cryptographic_hash_function) is a reliable and [widely accepted](https://csrc.nist.gov/Projects/Hash-Functions) method to [ensure data integrity](https://learn.microsoft.com/en-us/dotnet/standard/security/ensuring-data-integrity-with-hash-codes).

#### NOTE: Windows users should enable the "Long File Path" option for accurate results.
By default, Windows imposes a limit on the length of file paths and names, restricting them to approximately 260 characters. If a file path exceeds this limit due to long folder names or file names, some programs might be unable to open the file, even if it appears visible in Windows File Explorer.

| ---------------- File Path ----------------- || ----- File Name ----- |

C:\DocumentsFolder\WorkProjectsFolder\SampleDocument.PDF

| --------- Example File Path Length: 56 Characters Long --------- |

To overcome this limitation, the "Long File Paths" option must be manually enabled in Windows. Without enabling this setting, FileReceipt, and other programs, may encounter difficulties consistently opening files within long file paths. Consequently, when creating a FileReceipt for files and folders with long paths, failure to enable the "Long File Paths" setting may lead to errors or omission of these files from the catalog.

WARNING: Modifying the Windows Registry can be dangerous and may render your computer unusable. Seek assistance from your IT department or proceed with caution and create a backup before making changes.

Visit the following pages for information and instructions on enabling "Long File Paths":
   - [Long File Paths in Windows](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=registry)
   - [Enabling Long File Paths](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-Windows-10-default-path-length-limitation-MAX-PATH-is-256-characters.html)

## Download (for most users)

Download the latest release on GitHub [here](https://github.com/btc-git/FileReceipt/raw/main/FileReceipt.exe). (8/23/2023)
- You may receive a [warning](https://learn.microsoft.com/en-us/windows/security/operating-system-security/virus-and-threat-protection/microsoft-defender-smartscreen/) when you run the program for the first time. To bypass the warning, click 'More info' and then 'Run anyway.' The program has been submitted to Microsoft for security analysis, which should make that warning go away soon.

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

## License
FileReceipt is licensed under the GNU General Public License v3.0.
See the [LICENSE](https://github.com/btc-git/FileReceipt/blob/main/LICENSE.txt) file in the project for the full license text.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. 

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Contact
Brian@CrimLawTech.com

Copyright (c) 2023 Brian Cummings
