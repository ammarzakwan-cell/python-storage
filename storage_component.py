import logging
from pathlib import Path
import json
from fs.osfs import OSFS
from fs_s3fs import S3FS
from fs.sftpfs import SFTPFS
from fs.errors import ResourceNotFound

class StorageComponent:
    def __init__(self):
        self.config = self._load_config("config.json")
        self.filesystem = {}
        self.active_disk = None
        self.disk_config = None
        self.default_disk = 'local'  # Default disk can be set here
    
    def _load_config(self, config_path: str):
        """Load configuration from a file."""
        with open(config_path, 'r') as file:
            return json.load(file)
        
    def get_adapter(self):
        """Return the adapter (filesystem) for the selected disk."""
        if self.active_disk in self.filesystem:
            return self.filesystem[self.active_disk]
        
        # If adapter is not already set, load the disk configuration
        self.disk(self.active_disk)
        return self.filesystem.get(self.active_disk)

    def disk(self, disk: str = None):
        """Set the active disk and initialize the corresponding adapter."""
        self.active_disk = disk or self.default_disk

        if self.active_disk in self.filesystem:
            return self

        try:
            self.disk_config = self.config['disks'][self.active_disk]
            driver = self.disk_config['driver']
            if driver == 'sftp':
                self._create_sftp_driver()
            elif driver == 's3':
                self._create_s3_driver()
            else:
                self._create_local_driver()
        except Exception as e:
            logging.error(f"Error initializing disk: {e}")
        return self

    def _create_sftp_driver(self):
        """Create SFTP connection."""
        try:
            sftp_config = self.disk_config.get('sftp', {})
            host = sftp_config.get('host')
            username = sftp_config.get('username')
            password = sftp_config.get('password')
            port = sftp_config.get('port', 22)
            
            self.filesystem[self.active_disk] = SFTPFS(f"sftp://{username}:{password}@{host}:{port}")
        except Exception as e:
            logging.error(f"Error creating SFTP driver: {e}")

    def _create_s3_driver(self):
        """Create S3 connection."""
        try:
            s3_config = self.disk_config.get('s3', {})
            bucket = s3_config.get('bucket')
            key = s3_config.get('key')
            secret = s3_config.get('secret')
            region = s3_config.get('region')

            self.filesystem[self.active_disk] = S3FS(f"{bucket}://", key=key, secret=secret, region=region)
        except Exception as e:
            logging.error(f"Error creating S3 driver: {e}")

    def _create_local_driver(self):
        """Create local filesystem driver."""
        try:
            root = str(Path(self.disk_config.get('root', '/')).resolve())
            self.filesystem[self.active_disk] = OSFS(root)
        except Exception as e:
            logging.error(f"Error creating local driver: {e}")
    
    def store(self, path: str, content: str):
        """Store a file in the given filesystem."""
        try:
            self.get_adapter().writetext(path, content)
            print(f"File '{path}' stored successfully.")
        except Exception as e:
            logging.error(f"Error storing file '{path}': {e}")

    def get(self, path: str) -> str:
        """Get the content of a file from the given filesystem."""
        try:
            return self.get_adapter().readtext(path)
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as e:
            logging.error(f"Error reading file '{path}': {e}")

    def delete(self, path: str):
        """Delete a file from the given filesystem."""
        try:
            self.get_adapter().remove(path)
            print(f"File '{path}' deleted successfully.")
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as e:
            logging.error(f"Error deleting file '{path}': {e}")

    def is_exist(self, path: str) -> bool:
        """Check if a file exists in the given filesystem."""
        try:
            return self.get_adapter().exists(path)
        except Exception as e:
            logging.error(f"Error checking file existence for '{path}': {e}")
            return False

    def upload(self, source_path: str, dest_path: str):
        """
        Upload a file from the local filesystem to the given filesystem.
        
        :param fs: Target filesystem (e.g., S3)
        :param source_path: Path of the file on the local filesystem
        :param dest_path: Path to store the file in the target filesystem
        """
        try:
            with open(source_path, 'rb') as local_file:
                self.get_adapter().writebytes(dest_path, local_file.read())
            print(f"File '{source_path}' uploaded to '{dest_path}' successfully.")
        except Exception as e:
            logging.error(f"Error uploading file '{source_path}' to '{dest_path}': {e}")

    def list(self, directory: str = "/") -> list:
        """
        List files in the specified directory of the given filesystem.
        
        :param fs: Target filesystem (e.g., local or S3)
        :param directory: Directory path to list files from
        :return: List of file and directory names
        """
        
        try:
            return self.get_adapter().listdir(directory)
        except ResourceNotFound:
            logging.error(f"Directory '{directory}' not found.")
            return []
        except Exception as e:
            logging.error(f"Error listing directory '{directory}': {e}")
            return []


# Initialize the PyFilesystemExample with the path to your configuration
fs_example = StorageComponent()
# Set the active disk (choose between 'local', 's3_disk', or 'sftp_disk')
fs = fs_example.disk('local')  # or fs_example.disk('s3_disk')
print(fs.list())

test = fs_example.disk('second_local').list()
print(test)


