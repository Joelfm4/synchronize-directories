from tempfile import TemporaryDirectory
import unittest
import time
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from synchronization import *
from watch_changes import FolderMonitor

class TestFirsSynchronization(unittest.TestCase):

    # ----------Initialization Functions---------- #
    def setUp(self):
        self.source_dir = TemporaryDirectory()
        self.replica_dir = TemporaryDirectory()

        self.source_path = self.source_dir.name
        self.replica_path = self.replica_dir.name 


    def cleanUp(self):
        self.source_dir.cleanup()
        self.replica_dir.cleanup()


    def create_files_in_source(self, files):
        for file_name, content in files.items():
            file_path = os.path.join(self.source_dir.name, file_name)
            with open(file_path, "w") as f:
                f.write(content)


    def create_files_in_replica(self, files):
        for file_name, content in files.items():
            file_path = os.path.join(self.replica_path, file_name)
            with open(file_path, "w") as f:
                f.write(content)


    def create_directories_in_source(self, directories):
        for directory in directories:
            os.mkdir(os.path.join(self.source_path, directory))


    def create_directories_in_replica(self, directories):
        for directory in directories:
            os.mkdir(os.path.join(self.replica_path, directory))


    # ----------TESTS---------- #

    def test_replica_directory_is_empty(self):
        """ Function Test 0 - Is empty function """
        self.assertTrue(replica_directory_is_empty(self.replica_path))
        self.cleanUp()


    def test_first_synchronization(self):
        """ Scenario 0 - First synchronization where replica is emplty """

        files:dict = {
            "star.txt":"UY Scut",
            "car.txt": "Alfa Romeo"
        }        
        self.create_files_in_source(files)
        update_replica_directory(self.source_path, self.replica_path)
        
        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "star.txt")), "File 'star.txt' was not copied")
        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "car.txt")), "File 'car.txt' was not copied")
        
        self.cleanUp()


    def test_initial_sync_replica_has_files(self):
        """ Scenario 1 - First synchronization where replica has files """

        files:dict = {
            "star.txt":"UY Scut",
            "car.txt": "Alfa Romeo"
        }

        self.create_files_in_replica(files)
        update_replica_directory(self.source_path, self.replica_path)
        
        self.assertTrue(replica_directory_is_empty(self.replica_path), "Replica directory is not empty")
        
        self.cleanUp()


    def test_fisrt_sync_with_extra_files_in_replica(self):
        """ Scenario 2 - First synchronization where replica have extra files"""

        files:dict = {
            "star.txt":"UY Scut",
            "car.txt": "Alfa Romeo"
        }        
        self.create_files_in_source(files)

        files["house.txt"] = "yellow house"
        self.create_files_in_replica(files) 
        
        update_replica_directory(self.source_path, self.replica_path)

        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "star.txt")), "File 'star.txt' was not created")
        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "car.txt")), "File 'car.txt' was not created")
        self.assertFalse(os.path.exists(os.path.join(self.replica_path, "house.txt")), "File 'house.txt' was not deleted")

        self.cleanUp()


    def test_sync_when_source_has_additional_files(self):
        """ Scenario 3 - Synchronization where both have files but source have extra files"""

        files:dict = {
            "star.txt":"UY Scut",
            "car.txt": "Alfa Romeo"
        }        
        self.create_files_in_replica(files) 

        files["house.txt"] = "yellow house"
        self.create_files_in_source(files)
        
        update_replica_directory(self.source_path, self.replica_path)

        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "star.txt")), "File 'star.txt' was not created")
        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "car.txt")), "File 'car.txt' was not created")
        self.assertTrue(os.path.exists(os.path.join(self.replica_path, "house.txt")), "File 'house.txt' was not updated")
        
        self.cleanUp()


    def test_rename_file_source(self):
        """ Scenario 4 - Renamed a file and listened for a renamed type change"""

        files:dict = {
            "star.txt":"UY Scut",
        }        

        self.create_files_in_source(files)

        directory_monitor = FolderMonitor(self.source_path)
        directory_monitor.start()

        try:
            os.rename(
                os.path.join(self.source_path, "star.txt"),
                os.path.join(self.source_path, "sun.txt")
            )
        
            for _ in range(5):
                changes = directory_monitor.get_changes()
                if changes:
                    change = changes[0]
                    self.assertEqual(change['type'], 'renamed', "File Change[type] isn't renamed")
                    self.assertEqual(change['old_path'], os.path.join(self.source_path, "star.txt"), "Old file path is incorrect")
                    self.assertEqual(change['new_path'], os.path.join(self.source_path, "sun.txt", "New file path is incorrect"))

        finally:
            directory_monitor.stop()
            self.cleanUp()


    def test_rename_folder_source(self):
        """ Scenario 5 - Renamed directory """
        directories:list = ["sales"] 

        self.create_directories_in_source(directories)

        directory_monitor = FolderMonitor(self.source_path)
        directory_monitor.start()

        try:
            os.rename(
                os.path.join(self.source_path, "sales"),
                os.path.join(self.source_path, "Sales")
            )
        
            for _ in range(5):
                changes = directory_monitor.get_changes()
                if changes:
                    change = changes[0]
                    self.assertEqual(change['type'], 'renamed', "Folder Change[type] isn't renamed")
                    self.assertEqual(change['old_path'], os.path.join(self.source_path, "sales"), "Old path is incorrect")
                    self.assertEqual(change['new_path'], os.path.join(self.source_path, "Sales", "New path is incorrect"))

        finally:
            directory_monitor.stop()
            self.cleanUp()


    def test_edit_source_file(self):
        """ Scenario 6 - Edit a file inside source directory """
        ...


    def test_add_file_source(self):
        """ Scenario 7 - Add a file to the original directory that is not in the replica """
        ...

        
    def test_add_directory_source(self):
        """ Scenario 8 - Add a directory to the original directory that is not in the replica """
        ...

        
    def test_move_file_source(self):
        """ Scenario 9 - Move a file from directory A to directory B """
        ...

        
    def test_move_folder_source(self):
        """ Scenario 10 - Move a directory from directory A to directory B """
        ...


if __name__=='__main__':
    unittest.main()
