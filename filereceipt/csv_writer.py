import os
import io
import csv
from datetime import datetime
from tzlocal import get_localzone


def write_results_to_csv(csv_file_path, file_hashes, error_logs, empty_files, 
                         empty_dirs, hash_algorithm, recursion_threshold,
                         input_size=0):
    """Write file receipt results to a CSV file.
    
    Args:
        csv_file_path: Path where the CSV file will be saved
        file_hashes: List of [path, hash, size] tuples
        error_logs: List of (path, error_message) tuples
        empty_files: List of [path, hash, size] for empty files
        empty_dirs: List of [path, "--FOLDER--", "N/A"] for empty directories
        hash_algorithm: Name of the hash algorithm used
        recursion_threshold: Recursion threshold value used
    """
    with io.open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the catalog header to the CSV file
        writer.writerow(["Item #:", "File / Folder Name:", "File / Folder Path:", f"File Hash [{hash_algorithm}]:", "File Size [bytes]:"])

        # Write the file information for each file in the file_hashes list as a row in the CSV file
        for index, hash_info in enumerate(file_hashes, start=1):
            is_folder = hash_info[1] == "--FOLDER--"
            basename = os.path.basename(hash_info[0])
            file_name = f"{basename} [Folder]" if is_folder else basename
            display_hash = "[Folder]" if is_folder else hash_info[1]
            writer.writerow([index, file_name, os.path.normpath(hash_info[0]), display_hash, hash_info[2]])
        # Add empty rows for separation
        writer.writerow([] * 3)

        # Write the errors section header to the CSV file
        writer.writerow(["Errors:"])
        # Deduplicate the error logs while preserving order
        unique_errors = list(dict.fromkeys(error_logs))
        if unique_errors:
            # Write each error as a row in the CSV file
            for error in unique_errors:
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
        duplicates = find_duplicates(file_hashes)
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

        # Write the statistics section header to the CSV file
        writer.writerow(["File Processing Statistics:"])
        stats = calculate_statistics(file_hashes, empty_files, empty_dirs, duplicates)
        writer.writerow([f"Files Cataloged: {stats['total_files']}"])
        writer.writerow([f"Folders Cataloged: {stats['total_folders']}"])
        writer.writerow([f"Zip Archives Cataloged: {stats['total_zips']}"])
        writer.writerow([f"Input File Size: {input_size:,} bytes"])
        writer.writerow([f"Total Cataloged File Size: {stats['total_size']:,} bytes"])
        writer.writerow([f"Files With Duplicates: {stats['duplicate_groups']}"])
        writer.writerow([f"Redundant Duplicate Files: {stats['extra_duplicates']}"])
        writer.writerow([f"Empty Files: {len(empty_files)}"])
        writer.writerow([f"Empty Folders: {len(empty_dirs)}"])
        writer.writerow([f"Processing Errors: {len(unique_errors)}"])
        writer.writerow([])

        # Write the file type statistics section
        writer.writerow(["File Type Statistics:"])
        writer.writerow(["Extension:", "Files:", "Total Size [bytes]:"])
        for ext, ext_data in calculate_extension_statistics(file_hashes):
            writer.writerow([ext, ext_data['count'], f"{ext_data['size']:,}"])
        writer.writerow([])

        # Add empty rows for separation
        writer.writerow([] * 2)

        # Get and format local timezone
        local_timezone = get_localzone()
        current_time = datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")

        writer.writerow(["Date/Time Generated:"])
        writer.writerow([current_time])
        
        # Get the recursion threshold setting used
        threshold_text = "Off (no limit)" if recursion_threshold == -1 else str(recursion_threshold)
        writer.writerow([f"Recursion Threshold Used: {threshold_text}"])


def find_duplicates(file_hashes):
    """Find duplicate files based on their hashes.
    
    Args:
        file_hashes: List of [path, hash, size] tuples
        
    Returns:
        List of duplicate groups, where each group is a list of duplicate file entries
    """
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


def calculate_statistics(file_hashes, empty_files, empty_dirs, duplicates=None):
    """Calculate file processing statistics.
    
    Args:
        file_hashes: List of [path, hash, size] tuples
        empty_files: List of [path, hash, size] for empty files
        empty_dirs: List of [path, "--FOLDER--", "N/A"] for empty directories
        duplicates: Optional list of duplicate groups from find_duplicates()
        
    Returns:
        Dictionary containing statistics about processed files
    """
    total_files = 0
    total_folders = 0
    total_zips = 0
    total_size = 0
    zip_on_disk_size = 0  # compressed on-disk size of ALL zip entries (expanded or not)
    standalone_size = 0  # non-zip files that are NOT inside any zip archive

    # Build a set of all cataloged paths to detect which zips were expanded.
    all_paths = set(hash_info[0] for hash_info in file_hashes)
    expanded_zips = set()
    for hash_info in file_hashes:
        path = hash_info[0]
        if path.lower().endswith('.zip') and hash_info[1] != "--FOLDER--":
            prefix = path + os.sep
            if any(p.startswith(prefix) for p in all_paths):
                expanded_zips.add(path)

    def _is_inside_zip(path):
        """Return True if the path lives inside a zip archive."""
        parts = path.replace('\\', '/').split('/')
        return any(part.lower().endswith('.zip') for part in parts[:-1])

    # Count files and calculate sizes from file_hashes
    for hash_info in file_hashes:
        if hash_info[1] == "--FOLDER--":
            total_folders += 1
        else:
            total_files += 1
            path = hash_info[0]
            size = hash_info[2]

            if path.lower().endswith('.zip'):
                total_zips += 1
                zip_on_disk_size += size  # always record the on-disk compressed size
                if path not in expanded_zips:
                    # Unexpanded zip: count its compressed size as cataloged content
                    total_size += size
            else:
                total_size += size
                if not _is_inside_zip(path):
                    standalone_size += size

    # Add empty files to total count and size
    total_files += len(empty_files)
    total_size += sum(f[2] for f in empty_files)

    # Add empty directories to total folder count
    total_folders += len(empty_dirs)

    # Duplicate stats: groups with more than one copy, and total redundant files
    if duplicates is None:
        duplicates = find_duplicates(file_hashes)
    duplicate_groups = len(duplicates)
    extra_duplicates = sum(len(group) - 1 for group in duplicates)

    return {
        'total_files': total_files,
        'total_folders': total_folders,
        'total_zips': total_zips,
        'total_size': total_size,
        'zip_on_disk_size': zip_on_disk_size,
        'standalone_size': standalone_size,
        'duplicate_groups': duplicate_groups,
        'extra_duplicates': extra_duplicates
    }


def calculate_extension_statistics(file_hashes):
    """Count files and total size per extension, sorted by size descending.

    Args:
        file_hashes: List of [path, hash, size] tuples

    Returns:
        List of (extension, {'count': int, 'size': int}) sorted by size descending.
        Files with no extension are grouped under '(none)'.
    """
    ext_stats = {}
    for hash_info in file_hashes:
        if hash_info[1] == "--FOLDER--":
            continue
        _, ext = os.path.splitext(hash_info[0])
        ext = ext.lower() if ext else "(none)"
        try:
            size = int(hash_info[2])
        except (ValueError, TypeError):
            size = 0
        if ext not in ext_stats:
            ext_stats[ext] = {'count': 0, 'size': 0}
        ext_stats[ext]['count'] += 1
        ext_stats[ext]['size'] += size
    return sorted(ext_stats.items(), key=lambda x: x[1]['size'], reverse=True)
