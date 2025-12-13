import os
import io
import csv
from datetime import datetime
from tzlocal import get_localzone


def write_results_to_csv(csv_file_path, file_hashes, error_logs, empty_files, 
                         empty_dirs, hash_algorithm, recursion_threshold):
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
        writer.writerow(["Catalog of Selected Files [Path]:", f"File Hash [{hash_algorithm}]:", "File Size [bytes]:"])

        # Write the file information for each file in the file_hashes list as a row in the CSV file
        for hash_info in file_hashes:
            writer.writerow([os.path.normpath(hash_info[0]), hash_info[1], hash_info[2]])
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
        stats = calculate_statistics(file_hashes, empty_files, empty_dirs)
        writer.writerow([f"Files Cataloged: {stats['total_files']}"])
        writer.writerow([f"Folders Cataloged: {stats['total_folders']}"])
        writer.writerow([f"Zip Archives Found: {stats['total_zips']}"])
        writer.writerow([f"Total Input Size: {stats['total_size']:,} bytes"])
        writer.writerow([f"Archive Size: {stats['zip_size']:,} bytes"])
        writer.writerow([f"Extracted Content Size: {stats['unzipped_size']:,} bytes"])
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


def calculate_statistics(file_hashes, empty_files, empty_dirs):
    """Calculate file processing statistics.
    
    Args:
        file_hashes: List of [path, hash, size] tuples
        empty_files: List of [path, hash, size] for empty files
        empty_dirs: List of [path, "--FOLDER--", "N/A"] for empty directories
        
    Returns:
        Dictionary containing statistics about processed files
    """
    total_files = 0
    total_folders = 0
    total_zips = 0
    total_size = 0
    zip_size = 0
    
    # Count files and calculate sizes from file_hashes
    for hash_info in file_hashes:
        if hash_info[1] == "--FOLDER--":
            # This is a directory entry
            total_folders += 1
        else:
            # This is a file entry
            total_files += 1
            file_size = hash_info[2]
            total_size += file_size
            
            # Check if it's a zip file
            if hash_info[0].lower().endswith('.zip'):
                total_zips += 1
                zip_size += file_size
    
    # Add empty files to total count and size
    total_files += len(empty_files)
    total_size += sum(f[2] for f in empty_files)
    
    # Add empty directories to total folder count
    total_folders += len(empty_dirs)
    
    # Calculate unzipped file size (total minus zip files)
    unzipped_size = total_size - zip_size
    
    return {
        'total_files': total_files,
        'total_folders': total_folders,
        'total_zips': total_zips,
        'total_size': total_size,
        'zip_size': zip_size,
        'unzipped_size': unzipped_size
    }
