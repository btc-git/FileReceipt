import os
import hashlib
import zipfile
import tempfile
from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from .config import HASH_ALGORITHMS


class HashingThread(QThread):
    """Thread for processing files and calculating hashes without blocking UI."""
    progress = QtCore.pyqtSignal(int)
    processing_file = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(list, list, list, list)

    def __init__(self, file_paths, hash_algorithm, recursion_threshold):
        super().__init__()
        self.file_paths = file_paths  # File paths to process
        self.file_hashes = []  # Store file hashes
        self.error_logs = []  # Store any errors during the process
        self.empty_files = []  # Store info of empty files
        self.empty_directories = []  # Store info of empty directories
        self.recursion_threshold = recursion_threshold  # Recursion threshold value
        self.cancelled = False  # Flag to cancel the process
        self.hash_algorithm = hash_algorithm  # Hash algorithm to use
        # Add new variables for improved progress tracking
        self.processed_files_count = 0  # Count of files processed so far
        self.total_files_estimate = 0   # Initial estimate of total files
        self.progress_lock = QtCore.QMutex()  # Mutex for thread-safe progress updates

    def get_total_file_count(self, file_paths):
        """Estimate total files to be processed including inside zips."""
        total_count = 0
        for path in file_paths:
            if os.path.isfile(path):
                total_count += 1
                # Add an estimate for zip files based on a sampling method
                if path.lower().endswith('.zip') and self.recursion_threshold != 1:
                    try:
                        with zipfile.ZipFile(path, 'r') as zip_ref:
                            zip_file_count = len(zip_ref.namelist())
                            # If under threshold or no threshold, count all files
                            if self.recursion_threshold <= 0 or zip_file_count <= self.recursion_threshold:
                                total_count += zip_file_count
                            # Add estimation for nested zips - just a rough estimate
                            for item in zip_ref.namelist():
                                if item.lower().endswith('.zip'):
                                    total_count += 10  # Rough estimate per nested zip
                    except Exception:
                        # Just count the zip file itself if we can't open it
                        pass
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path, followlinks=False):
                    total_count += len(files)
                    # Add estimates for zip files in directories
                    for file in files:
                        if file.lower().endswith('.zip') and self.recursion_threshold != 1:
                            zip_path = os.path.join(root, file)
                            try:
                                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                    zip_file_count = len(zip_ref.namelist())
                                    # If under threshold or no threshold, count all files
                                    if self.recursion_threshold <= 0 or zip_file_count <= self.recursion_threshold:
                                        total_count += zip_file_count
                                    # Add estimation for nested zips
                                    for item in zip_ref.namelist():
                                        if item.lower().endswith('.zip'):
                                            total_count += 10  # Rough estimate per nested zip
                            except Exception:
                                # Skip if zip can't be read
                                pass
        return max(1, total_count)  # Ensure we don't return 0

    def update_progress(self):
        """Update progress in a thread-safe way."""
        self.progress_lock.lock()
        self.processed_files_count += 1
        progress_value = min(99, int((self.processed_files_count / max(self.total_files_estimate, self.processed_files_count)) * 100))
        self.progress.emit(progress_value)
        self.progress_lock.unlock()

    def run(self):
        """Main thread execution - process all files."""
        # Get initial estimate of total files (including inside zips)
        self.total_files_estimate = self.get_total_file_count(self.file_paths)
        self.processed_files_count = 0  # Reset counter

        # Compute the total size of the top-level inputs the user actually provided
        self.input_size = 0
        for p in self.file_paths:
            try:
                if os.path.isfile(p):
                    self.input_size += os.path.getsize(p)
                elif os.path.isdir(p):
                    for root, dirs, files in os.walk(p, followlinks=False):
                        for f in files:
                            try:
                                self.input_size += os.path.getsize(os.path.join(root, f))
                            except OSError:
                                pass
            except OSError:
                pass

        # Loop over all file paths
        for file_path in self.file_paths:
            # Break the loop if the process has been cancelled
            if self.cancelled:
                break

            # Check if the file path is a file
            if os.path.isfile(file_path):
                # Update progress for this file
                self.update_progress()
                self.processing_file.emit(os.path.basename(file_path))
                
                # Handle zip files separately
                if file_path.lower().endswith('.zip'):
                    # Calculate the hash of the zip file itself
                    self.processing_file.emit(f"Hashing archive: {os.path.basename(file_path)}")
                    hash_value, file_size, error_message = self.calculate_file_hash(file_path)
                    
                    if error_message:
                        # Append error to error logs
                        self.error_logs.append((os.path.normpath(file_path), error_message))
                    else:
                        # Add the zip file itself to the file_hashes
                        self.file_hashes.append([os.path.normpath(file_path), hash_value, file_size])
                        
                        # Only process the contents if recursion threshold is not 1
                        if self.recursion_threshold != 1:
                            # Check if recursion threshold is greater than 1 and zip has too many files
                            if self.recursion_threshold > 1:
                                try:
                                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                                        if len(zip_ref.namelist()) > self.recursion_threshold:
                                            continue  # Skip processing this zip's contents
                                except Exception as e:
                                    self.error_logs.append((os.path.normpath(file_path), f"Error reading zip file '{file_path}': {str(e)}"))
                                    continue
                                    
                            # Calculate hashes for files inside the zip file
                            hashes, errors, empty_files_zip, empty_dirs_zip = self.calculate_zip_hashes(file_path)
                            
                            # Don't add the zip file itself again since we already added it above
                            # Only add the internal files (starting from index 1)
                            if len(hashes) > 1:
                                self.file_hashes.extend(hashes[1:])
                                
                            # Note: self.empty_files and self.empty_directories are already
                            # accumulated inside calculate_zip_hashes; do not re-extend here.
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
                hashes, errors, empty_files_folder, empty_dirs_folder = self.calculate_folder_hashes(file_path, self.total_files_estimate, self.processed_files_count)
                # Append hashes and errors to respective lists
                self.file_hashes.extend(hashes)
                self.error_logs.extend(errors)
                self.empty_files.extend(empty_files_folder)
                self.empty_directories.extend(empty_dirs_folder)

            # If the process hasn't been cancelled, calculate and emit the progress
            if not self.cancelled:
                progress_value = int((self.processed_files_count / self.total_files_estimate) * 100)
                self.progress.emit(progress_value)
                self.processing_file.emit(os.path.basename(file_path))

        # Ensure we reach 100% at the end
        if not self.cancelled:
            self.progress.emit(100)
            
        # Emit the finished signal with the results
        self.finished.emit(self.file_hashes, self.error_logs, self.empty_files, self.empty_directories)

    def calculate_file_hash(self, file_path):
        """Calculate the hash of a file."""
        file_size = None  # Initialize to avoid UnboundLocalError
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
            return None, file_size if file_size is not None else 0, error_message

    def calculate_zip_hashes(self, zip_path):
        """Calculate hashes for files inside a zip archive."""
        try:
            # Normalize zip path immediately
            zip_path = os.path.normpath(zip_path)
            file_size = os.path.getsize(zip_path)
            zip_hash_value, _, _ = self.calculate_file_hash(zip_path)
            file_hashes = [[zip_path, zip_hash_value, file_size]]

            # Early threshold check - don't process contents if threshold is 1
            if self.recursion_threshold == 1:
                return file_hashes, [], [], []  # Return empty lists for errors and empty files/dirs

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Early threshold check - skip if over limit
                if self.recursion_threshold > 1 and len(zip_ref.namelist()) > self.recursion_threshold:
                    error_message = f"Zip file '{zip_path}' contents not processed: contains more than {self.recursion_threshold} files"
                    self.error_logs.append((zip_path, error_message))
                    return file_hashes, self.error_logs, [], []
                    
                with tempfile.TemporaryDirectory() as temp_dir:
                    all_entries = zip_ref.namelist()
                    for zipped_file in all_entries:
                        # Handle directory entries in zip files
                        if zipped_file.endswith('/'):
                            # Sanitize entry path: strip leading slashes to prevent drive-root paths
                            safe_entry = zipped_file.lstrip('/')
                            if not safe_entry:
                                continue  # Skip bare '/' entries
                            # Process directory entry
                            # Store path, normalized properly
                            original_dir_path = os.path.normpath(os.path.join(zip_path, safe_entry))
                            
                            # Check if directory is empty (no entries with this dir as prefix)
                            is_empty = not any(
                                entry != zipped_file and entry.startswith(zipped_file) 
                                for entry in all_entries
                            )
                            
                            if is_empty:
                                self.empty_directories.append([original_dir_path, "--FOLDER--", "N/A"])
                            else:
                                file_hashes.append([original_dir_path, "--FOLDER--", "N/A"])
                            continue
                            
                        # Extract this file now (instead of extractall upfront) so that
                        # progress signals fire between files rather than after a long block.
                        try:
                            zip_ref.extract(zipped_file, temp_dir)
                        except Exception as e:
                            original_file_path = os.path.normpath(os.path.join(zip_path, zipped_file))
                            self.error_logs.append((original_file_path, f"Error extracting '{zipped_file}': {str(e)}"))
                            continue

                        # Process files (non-directory entries)
                        temp_file_path = os.path.join(temp_dir, zipped_file)
                        original_file_path = os.path.normpath(os.path.join(zip_path, zipped_file))
                        
                        # Update progress for this file inside the zip
                        self.update_progress()
                        self.processing_file.emit(os.path.basename(zipped_file))
                        
                        # Check if it's a nested zip file
                        if zipped_file.lower().endswith('.zip'):
                            nested_hashes, nested_errors, nested_empty_files, nested_empty_dirs = self.calculate_nested_zip_hashes(temp_file_path, original_file_path)
                            file_hashes.extend(nested_hashes)
                            self.error_logs.extend(nested_errors)
                            self.empty_files.extend(nested_empty_files)
                            self.empty_directories.extend(nested_empty_dirs)
                        else:
                            # Process each regular file in the temporary directory
                            hash_value, file_size, error_message = self.calculate_file_hash(temp_file_path)
                            if error_message:
                                self.error_logs.append((original_file_path, error_message))
                            else:
                                file_hashes.append([original_file_path, hash_value, file_size])
                                if file_size == 0:
                                    self.empty_files.append([original_file_path, hash_value, file_size])

            return file_hashes, self.error_logs, self.empty_files, self.empty_directories
        except Exception as e:
            error_message = f"Error processing zip file '{zip_path}': {str(e)}"
            self.error_logs.append((zip_path, error_message))
            
            # Still attempt to return the zip file's hash even if we can't process its contents
            try:
                zip_path = os.path.normpath(zip_path)
                file_size = os.path.getsize(zip_path)
                zip_hash_value, _, _ = self.calculate_file_hash(zip_path)
                file_hashes = [[zip_path, zip_hash_value, file_size]]
                return file_hashes, self.error_logs, [], []
            except Exception as inner_e:
                # If we completely fail to get the zip file's hash, only then return empty list
                additional_error = f"Also failed to calculate hash for zip file: {str(inner_e)}"
                self.error_logs.append((zip_path, additional_error))
                return [], self.error_logs, [], []

    def calculate_nested_zip_hashes(self, zip_path, parent_zip_path, temp_dir_context=None):
        """Process nested zip files with proper path handling."""
        file_hashes = []
        error_logs = []
        empty_files_zip = []
        empty_dirs_zip = []
        hash_algorithm = self.hash_algorithm.lower()
        
        # Normalize paths
        zip_path = os.path.normpath(zip_path)
        parent_zip_path = os.path.normpath(parent_zip_path)
        
        # Determine if we own the temp directory (and need to clean it up)
        owns_temp_dir = temp_dir_context is None
        if owns_temp_dir:
            temp_dir_context = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_context.__enter__()
        else:
            temp_dir = temp_dir_context

        try:
            # Always calculate and add the hash of the nested zip file itself first
            try:
                file_size = os.path.getsize(zip_path)
                hasher = getattr(hashlib, hash_algorithm)()
                
                with open(zip_path, 'rb') as f:
                    buffer = f.read(65536)  # Read in 64kb chunks
                    while len(buffer) > 0:
                        if self.cancelled:
                            return file_hashes, error_logs, empty_files_zip, empty_dirs_zip
                        hasher.update(buffer)
                        buffer = f.read(65536)
                
                # Add the nested zip file itself to the results
                zip_hash = hasher.hexdigest()
                file_hashes.append([parent_zip_path, zip_hash, file_size])
            except Exception as e:
                error_message = f"Error calculating hash for nested zip file '{parent_zip_path}': {str(e)}"
                error_logs.append((parent_zip_path, error_message))
                # Even with error, try to continue processing if possible

            # Now try to process the contents of the nested zip
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Early threshold check
                    if self.recursion_threshold > 1 and len(zip_ref.namelist()) > self.recursion_threshold:
                        error_message = f"Nested zip file '{parent_zip_path}' not processed: contains more than {self.recursion_threshold} files"
                        error_logs.append((parent_zip_path, error_message))
                        return file_hashes, error_logs, empty_files_zip, empty_dirs_zip
                    
                    for file in zip_ref.namelist():
                        if self.cancelled:
                            break
                        
                        # Process directory entries in zip files
                        if file.endswith('/'):
                            safe_entry = file.lstrip('/')
                            if not safe_entry:
                                continue  # Skip bare '/' entries
                            normalized_path = os.path.normpath(os.path.join(parent_zip_path, safe_entry))
                            
                            # Check if directory is empty
                            is_empty = not any(
                                entry != file and entry.startswith(file) 
                                for entry in zip_ref.namelist()
                            )
                            
                            if is_empty:
                                empty_dirs_zip.append([normalized_path, "--FOLDER--", "N/A"])
                            else:
                                file_hashes.append([normalized_path, "--FOLDER--", "N/A"])
                            continue
                        
                        # Update progress for this file inside the nested zip
                        self.update_progress()
                        self.processing_file.emit(os.path.basename(file))
                        
                        # Construct normalized paths
                        normalized_file_path = os.path.join(parent_zip_path, file.replace('/', os.sep))
                        normalized_file_path = os.path.normpath(normalized_file_path)

                        # Handle nested zip files
                        if file.lower().endswith('.zip'):
                            try:
                                # Extract to persistent temp directory - use return value for actual path
                                extracted_path = zip_ref.extract(file, temp_dir)
                                extracted_path = os.path.normpath(extracted_path)
                                
                                # Calculate hash of the nested zip file itself and add it to results
                                zip_file_size = os.path.getsize(extracted_path)
                                hasher = getattr(hashlib, hash_algorithm)()
                                with open(extracted_path, 'rb') as f:
                                    buffer = f.read(65536)
                                    while len(buffer) > 0:
                                        if self.cancelled:
                                            return file_hashes, error_logs, empty_files_zip, empty_dirs_zip
                                        hasher.update(buffer)
                                        buffer = f.read(65536)
                                zip_hash = hasher.hexdigest()
                                file_hashes.append([normalized_file_path, zip_hash, zip_file_size])
                                
                                # Process the nested zip with shared temp directory
                                with zipfile.ZipFile(extracted_path, 'r') as nested_zip:
                                    # Check threshold for deeply nested zip
                                    if self.recursion_threshold > 1 and len(nested_zip.namelist()) > self.recursion_threshold:
                                        error_message = f"Deep nested zip file '{normalized_file_path}' not processed: contains more than {self.recursion_threshold} files"
                                        error_logs.append((normalized_file_path, error_message))
                                    else:
                                        # Extract and process each file in the nested zip
                                        for nested_file in nested_zip.namelist():
                                            if nested_file.endswith('/'):
                                                # Process directory entry in nested zip
                                                safe_nested = nested_file.lstrip('/')
                                                if not safe_nested:
                                                    continue  # Skip bare '/' entries
                                                nested_dir_path = os.path.normpath(os.path.join(normalized_file_path, safe_nested))
                                                is_nested_dir_empty = not any(
                                                    nf != nested_file and nf.startswith(nested_file) 
                                                    for nf in nested_zip.namelist()
                                                )
                                                
                                                if is_nested_dir_empty:
                                                    empty_dirs_zip.append([nested_dir_path, "--FOLDER--", "N/A"])
                                                else:
                                                    file_hashes.append([nested_dir_path, "--FOLDER--", "N/A"])
                                            else:
                                                # Process file in nested zip - use returned path from extract
                                                nested_file_path = nested_zip.extract(nested_file, temp_dir)
                                                nested_file_path = os.path.normpath(nested_file_path)
                                                nested_original_path = os.path.normpath(os.path.join(normalized_file_path, nested_file))
                                                
                                                # Check if this file is also a zip - recursively process if so
                                                if nested_file.lower().endswith('.zip'):
                                                    # Recursively process this deeply nested zip with shared temp directory
                                                    deep_hashes, deep_errors, deep_empty_files, deep_empty_dirs = self.calculate_nested_zip_hashes(nested_file_path, nested_original_path, temp_dir)
                                                    file_hashes.extend(deep_hashes)
                                                    error_logs.extend(deep_errors)
                                                    empty_files_zip.extend(deep_empty_files)
                                                    empty_dirs_zip.extend(deep_empty_dirs)
                                                else:
                                                    # Process regular file
                                                    hash_value, file_size, error_message = self.calculate_file_hash(nested_file_path)
                                                    if error_message:
                                                        error_logs.append((nested_original_path, error_message))
                                                    else:
                                                        file_hashes.append([nested_original_path, hash_value, file_size])
                                                        if file_size == 0:
                                                            empty_files_zip.append([nested_original_path, hash_value, 0])
                            except Exception as e:
                                error_message = f"Error processing nested zip file '{normalized_file_path}': {str(e)}"
                                error_logs.append((normalized_file_path, error_message))
                        else:
                            # Process regular files in zip
                            file_data = zip_ref.read(file)
                            file_size = len(file_data)
                            hasher = getattr(hashlib, hash_algorithm)()
                            hasher.update(file_data)
                            hash_value = hasher.hexdigest()
                            
                            file_hashes.append([normalized_file_path, hash_value, file_size])
                            if file_size == 0:
                                empty_files_zip.append([normalized_file_path, hash_value, 0])
            
            except Exception as e:
                error_message = f"Error processing zip file '{parent_zip_path}': {str(e)}"
                error_logs.append((parent_zip_path, error_message))
        
        finally:
            # Only clean up if we created the temp directory
            if owns_temp_dir:
                temp_dir_context.__exit__(None, None, None)
        
        return file_hashes, error_logs, empty_files_zip, empty_dirs_zip

    def calculate_folder_hashes(self, folder_path, total_files, current_file):
        """Calculate hashes for all files in a folder with proper path handling."""
        # Normalize the folder path
        folder_path = os.path.normpath(folder_path)
        file_hashes = []
        error_logs = []
        empty_files_folder = []
        empty_dirs_folder = []

        try:
            for root, dirs, files in os.walk(folder_path, followlinks=False):
                if self.cancelled:
                    break

                # Normalize root path once
                norm_root = os.path.normpath(root)
                
                # Check if this directory is empty
                is_empty = len(dirs) == 0 and len(files) == 0
                if is_empty:
                    empty_dirs_folder.append([norm_root, "--FOLDER--", "N/A"])
                else:
                    file_hashes.append([norm_root, "--FOLDER--", "N/A"])

                # Process files in this directory
                for file in files:
                    # Increment file counter and update progress
                    self.processed_files_count += 1
                    progress_value = int((self.processed_files_count / total_files) * 100)
                    self.progress.emit(progress_value)

                    # Create normalized file path
                    file_path = os.path.join(norm_root, file)
                    norm_file_path = os.path.normpath(file_path)
                    
                    # Process zip files
                    if norm_file_path.lower().endswith('.zip'):
                        hash_value, file_size, error_message = self.calculate_file_hash(norm_file_path)
                        
                        # Add the zip file itself to the results
                        file_hashes.append([norm_file_path, hash_value, file_size])
                        
                        # Skip processing zip contents if recursion threshold is 1
                        if self.recursion_threshold == 1:
                            continue
                            
                        # Check threshold for zip contents
                        if self.recursion_threshold > 1:
                            try:
                                with zipfile.ZipFile(norm_file_path, 'r') as zip_ref:
                                    if len(zip_ref.namelist()) > self.recursion_threshold:
                                        error_message = f"Zip file '{norm_file_path}' contents not processed: contains more than {self.recursion_threshold} files"
                                        self.error_logs.append((norm_file_path, error_message))
                                        continue
                            except Exception as e:
                                self.error_logs.append((norm_file_path, f"Error reading zip file '{norm_file_path}': {str(e)}"))
                                continue
                        
                        # Process zip contents if no errors with the zip file itself
                        if error_message:
                            self.error_logs.append((norm_file_path, error_message))
                        else:
                            hashes, errors, empty_files_zip, empty_dirs_zip = self.calculate_zip_hashes(norm_file_path)
                            # Skip the first item which is the zip file itself (already added)
                            if len(hashes) > 1:
                                file_hashes.extend(hashes[1:])
                            # Note: self.empty_files and self.empty_directories are already
                            # accumulated inside calculate_zip_hashes; do not re-extend here.

                        self.processing_file.emit(os.path.basename(norm_file_path))
                    else:
                        # Process regular files
                        hash_value, file_size, error = self.calculate_file_hash(norm_file_path)
                        if self.cancelled:
                            break
                            
                        # Create normalized file info
                        file_info = [norm_file_path, hash_value, file_size]
                        
                        # Add file to appropriate collections
                        file_hashes.append(file_info)
                        if file_size == 0:
                            empty_files_folder.append(file_info)
                        elif error:
                            error_logs.append((norm_file_path, error))

                        self.processing_file.emit(os.path.basename(norm_file_path))

        except Exception as e:
            error_message = f"Error walking through folder '{folder_path}': {str(e)}"
            error_logs.append((folder_path, error_message))

        return file_hashes, error_logs, empty_files_folder, empty_dirs_folder
