import csv
import hashlib
import io
import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from filereceipt.csv_writer import (
    calculate_statistics,
    find_duplicates,
    write_results_to_csv,
)
from filereceipt.hashing import HashingThread


class CatalogingTests(unittest.TestCase):
    def run_worker(self, paths, threshold=-1):
        worker = HashingThread(paths, "SHA256", threshold)
        worker.run()
        return worker

    def test_empty_files_are_counted_once(self):
        with tempfile.TemporaryDirectory() as root:
            empty_path = os.path.join(root, "empty.txt")
            full_path = os.path.join(root, "full.txt")
            open(empty_path, "wb").close()
            with open(full_path, "wb") as file:
                file.write(b"content")

            worker = self.run_worker([root])
            stats = calculate_statistics(
                worker.file_hashes,
                worker.empty_files,
                worker.empty_directories,
            )

            self.assertEqual(stats["total_files"], 2)
            self.assertEqual(len(worker.empty_files), 1)

    def test_failed_read_is_an_error_not_an_empty_file(self):
        with tempfile.TemporaryDirectory() as root:
            file_path = os.path.join(root, "unreadable.bin")
            with open(file_path, "wb") as file:
                file.write(b"content")

            worker = HashingThread([file_path], "SHA256", 1)
            worker.calculate_file_hash = lambda _: (None, 0, "simulated read failure")
            worker.run()

            self.assertEqual(worker.file_hashes, [])
            self.assertEqual(worker.empty_files, [])
            self.assertEqual(
                worker.error_logs,
                [(os.path.normpath(file_path), "simulated read failure")],
            )

    def test_overlapping_inputs_are_processed_once(self):
        with tempfile.TemporaryDirectory() as root:
            child_path = os.path.join(root, "child.txt")
            content = b"one physical file"
            with open(child_path, "wb") as file:
                file.write(content)

            worker = self.run_worker([root, child_path])
            files = [
                entry for entry in worker.file_hashes
                if entry[1] != "--FOLDER--"
            ]

            self.assertEqual(worker.file_paths, [os.path.normpath(root)])
            self.assertEqual(len(files), 1)
            self.assertEqual(worker.input_size, len(content))
            self.assertEqual(find_duplicates(worker.file_hashes), [])

    def test_zip_threshold_counts_files_not_directories(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, "ten-files.zip")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("folder/", b"")
                for index in range(10):
                    archive.writestr(f"folder/{index}.txt", b"x")

            worker = self.run_worker([archive_path], threshold=10)
            cataloged_files = [
                entry for entry in worker.file_hashes
                if entry[1] != "--FOLDER--"
            ]

            self.assertEqual(len(cataloged_files), 11)
            self.assertEqual(worker.error_logs, [])

    def test_threshold_skip_is_reported(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, "eleven-files.zip")
            with zipfile.ZipFile(archive_path, "w") as archive:
                for index in range(11):
                    archive.writestr(f"{index}.txt", b"x")

            worker = self.run_worker([archive_path], threshold=10)

            self.assertEqual(len(worker.file_hashes), 1)
            self.assertEqual(len(worker.error_logs), 1)
            self.assertIn("more than 10 files", worker.error_logs[0][1])

    def test_implicit_zip_folders_are_cataloged(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, "implicit-folders.zip")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("folder/subfolder/file.txt", b"x")

            worker = self.run_worker([archive_path])
            folder_paths = {
                entry[0] for entry in worker.file_hashes
                if entry[1] == "--FOLDER--"
            }

            self.assertEqual(len(folder_paths), 2)
            self.assertIn(
                os.path.normpath(os.path.join(archive_path, "folder")),
                folder_paths,
            )
            self.assertIn(
                os.path.normpath(
                    os.path.join(archive_path, "folder", "subfolder")
                ),
                folder_paths,
            )

    def test_nested_zip_files_and_empty_files_are_cataloged(self):
        with tempfile.TemporaryDirectory() as root:
            nested_content = b"nested content" * 10000
            inner_data = io.BytesIO()
            with zipfile.ZipFile(inner_data, "w") as inner_archive:
                inner_archive.writestr("folder/file.txt", nested_content)
                inner_archive.writestr("folder/empty.bin", b"")

            archive_path = os.path.join(root, "outer.zip")
            with zipfile.ZipFile(archive_path, "w") as outer_archive:
                outer_archive.writestr("inner.zip", inner_data.getvalue())

            with patch.object(
                zipfile.ZipFile,
                "read",
                side_effect=AssertionError("ZIP members must be streamed"),
            ):
                worker = self.run_worker([archive_path])
            cataloged_paths = {entry[0] for entry in worker.file_hashes}
            inner_display_path = os.path.normpath(
                os.path.join(archive_path, "inner.zip")
            )
            nested_file_path = os.path.normpath(
                os.path.join(inner_display_path, "folder", "file.txt")
            )
            nested_entry = next(
                entry for entry in worker.file_hashes
                if entry[0] == nested_file_path
            )

            self.assertIn(inner_display_path, cataloged_paths)
            self.assertIn(nested_file_path, cataloged_paths)
            self.assertEqual(nested_entry[1], hashlib.sha256(nested_content).hexdigest())
            self.assertEqual(nested_entry[2], len(nested_content))
            self.assertEqual(len(worker.empty_files), 1)
            self.assertEqual(worker.error_logs, [])

    def test_folder_walk_errors_are_recorded(self):
        with tempfile.TemporaryDirectory() as root:
            denied_path = os.path.join(root, "denied")

            def failing_walk(path, followlinks=False, onerror=None):
                onerror(PermissionError(13, "Access denied", denied_path))
                return iter(())

            worker = HashingThread([root], "SHA256", 1)
            with patch("filereceipt.hashing.os.walk", side_effect=failing_walk):
                _, errors, _, _ = worker.calculate_folder_hashes(root, 1, 0)

            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0][0], os.path.normpath(denied_path))
            self.assertIn("Access denied", errors[0][1])

    def test_corrupt_zip_is_cataloged_and_reported(self):
        with tempfile.TemporaryDirectory() as root:
            archive_path = os.path.join(root, "broken.zip")
            with open(archive_path, "wb") as file:
                file.write(b"not a zip")

            worker = self.run_worker([archive_path])

            self.assertEqual(len(worker.file_hashes), 1)
            self.assertTrue(worker.file_hashes[0][1])
            self.assertEqual(len(worker.error_logs), 1)

    def test_csv_uses_duplicate_group_label(self):
        with tempfile.TemporaryDirectory() as root:
            csv_path = os.path.join(root, "report.csv")
            entries = [
                [os.path.join(root, "first.txt"), "same", 4],
                [os.path.join(root, "second.txt"), "same", 4],
            ]

            write_results_to_csv(
                csv_path,
                entries,
                [],
                [],
                [],
                "SHA256",
                1000,
                input_size=8,
            )

            with open(csv_path, newline="", encoding="utf-8") as file:
                first_column = [
                    row[0] for row in csv.reader(file) if row
                ]

            self.assertIn("Duplicate Groups: 1", first_column)
            self.assertNotIn("Files With Duplicates: 1", first_column)
            self.assertIn("FileReceipt Version: 1.5.1", first_column)


if __name__ == "__main__":
    unittest.main()
