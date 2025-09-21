import json
import math
import os
import datetime

# Directory where virtual drive files are stored
SAVE_PATH = "drive_bay"

class Inode:
    """
    Represents a file system inode containing metadata about files and directories.
    Each inode stores file information, block pointers, and timestamps.
    """
    def __init__(self,file_name: str, file_type: str, size: int, pointers: list[tuple], uid: str, time: str, permissions: list[int], mli_pointer: list = []) -> None:
        self.file_name = file_name                                              # Name of the file or directory
        self.file_type = file_type                                              # 'file' or 'directory'
        self.size = size                                                        # size in bytes
        self.pointers = pointers                                                # list of block indices. Each tuple is (start_block, length)
        self.uid = uid                                                          # File creator
        self.time_accessed = time                                               # Last accessed time
        self.time_modified = time                                               # Last modified time
        self.time_created = time                                                # Creation time
        self.time_deleted = None                                                # Deletion time (None if not deleted)
        self.blocks_used = 0
        self.update_blocks_used()                                               # Calculate number of blocks used by this file
        self.permissions = permissions                                          # 3 ints for user, group, others (rwx as 4+2+1)
        self.mli_pointer = mli_pointer                                          # Pointers for Multi-Level Indexing (if needed)
    
    # def __init__(self, pointers: list[tuple], mli_pointer: list = [], MLI_TRUE = True): # Multi-Level Indexing constructor
    #     self.pointers = pointers
    #     self.mli_pointer = mli_pointer
    #     self.MLI_TRUE = MLI_TRUE
    #     self.blocks_used = 0
    #     self.update_blocks_used()
    
    def update_access_time(self) -> None:
        """Update the last accessed timestamp to current time."""
        self.time_accessed = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def update_modified_time(self) -> None:
        """Update both modified and accessed timestamps to current time."""
        self.time_modified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_access_time()
    
    def update_deleted_time(self) -> None:
        """Mark file as deleted by setting deletion timestamp and updating modified time."""
        self.time_deleted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_modified_time()
    
    def update_blocks_used(self) -> None:
        """Calculate total blocks used by summing lengths from all pointer tuples."""
        self.blocks_used = sum([b for a, b in self.pointers])

class Drive:
    """
    Represents a virtual disk drive with blocks, inodes, and a file system structure.
    Uses a Unix-like inode system with superblock, bitmaps, and data blocks.
    """
    def __init__(self, name: str, total_blocks: int, block_list: list = None, block_size: int = 4096, inode_count: int = 80) -> None:
        self.block_list = block_list if block_list is not None else [None] * total_blocks
        
        # Calculate filesystem layout - similar to Unix filesystem structure
        inode_bitmap_start = 1  # Block 0 is superblock, block 1 is inode bitmap
        data_bitmap_start = inode_bitmap_start + 1
        inode_start = data_bitmap_start + 1
        inode_per_block = block_size // 256  # Assuming each inode is 256 bytes
        inode_size = math.ceil(inode_count / inode_per_block)  # Number of blocks needed for inodes
        data_size = total_blocks - (inode_start + inode_size)  # Remaining blocks for data


        # Initialize superblock (block 0) with filesystem metadata
        self.block_list[0] = { # Superblock
            "name": name,
            "total_blocks": total_blocks,
            "block_size": block_size,
            "inode_bitmap_start": inode_bitmap_start,
            "inode_bitmap_size": 1,
            "data_bitmap_start": data_bitmap_start,
            "data_bitmap_size": 1,
            "inode_start": inode_start,
            "inode_size": inode_size,
            "data_start": inode_start + inode_size,
            "data_size": data_size
            }
        
        # Initialize filesystem structures
        self.block_list[inode_bitmap_start] = [False] * inode_count # Track which inodes are in use
        self.block_list[data_bitmap_start] = [False] * data_size # Track which data blocks are in use
        
        # Initialize inode table blocks
        for i in range(inode_start, inode_start + inode_size): # initialize inode blocks
            self.block_list[i] = [None] * inode_per_block
        
        # Mark all inodes as free initially
        for i in range(inode_count): # initialize inodes as free
            self.block_list[inode_start + (i // inode_per_block)][i % inode_per_block] = Inode(file_name='' ,file_type="free", size=0, pointers=[], uid='', time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), permissions=[7,7,7]).__dict__
        
        # Initialize data blocks as empty
        for i in range(self.block_list[0]["data_start"], total_blocks): # initialize data blocks
            self.block_list[i] = ''

        # Create root directory (inode 0)
        root_inode = Inode(file_name='/', file_type='directory', size=0, pointers=[], uid='system', time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), permissions=[7,7,7])
        self.write_inode('', root_inode, 0) # Create root directory inode

    def find_free_inode(self) -> int | None:
        """
        Search for the first available inode in the inode bitmap.
        Returns the inode index or None if no free inodes exist.
        """
        inode_bitmap = self.block_list[self.block_list[0]["inode_bitmap_start"]]
        for i, used in enumerate(inode_bitmap):
            if not used:
                return i
        return None
    
    def find_free_data_blocks(self, count: int) -> list[tuple] | None:
        """
        Find contiguous free data blocks for file storage.
        Returns list of (start_block, length) tuples or None if insufficient space.
        Uses first-fit allocation strategy.
        """
        data_bitmap = self.block_list[self.block_list[0]["data_bitmap_start"]]
        free_blocks = []
        start = None
        length = 0
        progress = 0

        if count <= 0:
            return None

        for i, used in enumerate(data_bitmap):
            if not used:
                if start is None:
                    start = i
                length += 1
                progress += 1
                if progress == count:
                    free_blocks.append((start, length))
                    return free_blocks
            else:
                if start is not None:
                    free_blocks.append((start, length))
                    start = None
                    length = 0
        
        print("ERROR")
        return None
    
    def write_inode(self, data: str, file_inode: Inode, inode_index: int) -> bool:
        """
        Write file data and inode to disk.
        For directories: only creates inode without data blocks.
        For files: allocates data blocks and writes content.
        Returns True on success, False on failure (insufficient space).
        """
        INODE_BLOCK_START = self.block_list[0]["inode_bitmap_start"]

        if file_inode.file_type.lower() == "directory":
            # For directories, no data blocks are allocated, just set up the inode
            file_inode.pointers = []
            file_inode.size = 0
            file_inode.update_modified_time()
            self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)] = file_inode.__dict__
            self.block_list[INODE_BLOCK_START][inode_index] = True  # Mark inode as used
            return True

        # File handling: allocate data blocks and write content
        CHAR_BLOCK_SIZE = 32  # Number of characters per data block (small for demo purposes)
        
        # Handle empty files specially
        if len(data) == 0:
            # For empty files, no data blocks are needed, just create the inode
            file_inode.pointers = []
            file_inode.size = 0
            file_inode.update_modified_time()
            self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)] = file_inode.__dict__
            self.block_list[INODE_BLOCK_START][inode_index] = True  # Mark inode as used
            return True
        
        DATA_BLOCKS_NEEDED = math.ceil(len(data) / CHAR_BLOCK_SIZE)
        FREE_DATA_BLOCKS = self.find_free_data_blocks(DATA_BLOCKS_NEEDED)

        if FREE_DATA_BLOCKS is None:
            return False
        
        # Write data to allocated blocks
        DATA_BITMAP_START = self.block_list[0]["data_bitmap_start"]
        DATA_START = self.block_list[0]["data_start"]
        data_offset = 0
        for (start, length) in FREE_DATA_BLOCKS:
            for j in range(length):
                self.block_list[DATA_BITMAP_START][start + j] = True  # Mark data block as used
                block_data = data[data_offset:data_offset+CHAR_BLOCK_SIZE]  # Extract chunk for this block
                self.block_list[DATA_START + start + j] = block_data  # Write data to block
                data_offset += CHAR_BLOCK_SIZE

        # Update inode metadata and store in inode table
        file_inode.pointers = FREE_DATA_BLOCKS
        file_inode.size = len(data)
        file_inode.update_modified_time()
        self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)] = file_inode.__dict__

        

        self.block_list[INODE_BLOCK_START][inode_index] = True  # Mark inode as used
        return True
    
    def load_inode(self, inode_index: int) -> str | None:
        """
        Read file data from disk using inode information.
        Returns concatenated data from all blocks or None if inode not in use.
        """
        inode_bitmap = self.block_list[self.block_list[0]["inode_bitmap_start"]]
        if not inode_bitmap[inode_index]:
            return None
        
        # Reconstruct file data from blocks pointed to by inode
        data_inode = self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)]
        data = ""
        for (start, length) in data_inode["pointers"]:
            for j in range(length):
                data += self.block_list[self.block_list[0]["data_start"] + start + j]
        return data
    
    def delete_inode(self, inode_index: int) -> bool:
        """
        Delete a file by freeing its inode and all associated data blocks.
        Returns True on success, False if inode wasn't in use.
        """
        inode_bitmap = self.block_list[self.block_list[0]["inode_bitmap_start"]]
        data_bitmap = self.block_list[self.block_list[0]["data_bitmap_start"]]
        if not inode_bitmap[inode_index]:
            return False
        
        # Free all data blocks associated with this inode
        data_inode = self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)]
        for (start, length) in data_inode["pointers"]:
            for j in range(length):
                data_bitmap[start + j] = False  # Mark data block as free

        inode_bitmap[inode_index] = False  # Mark inode as free
        
        return True
    
    def find_file(self, file_name: str) -> int | None:
        """
        Search for a file by name across all inodes.
        Returns inode index if found, None otherwise.
        """
        inode_bitmap = self.block_list[self.block_list[0]["inode_bitmap_start"]]
        inode_start = self.block_list[0]["inode_start"]
        inode_size = self.block_list[0]["inode_size"]
        inode_per_block = self.block_list[0]["block_size"] // 256

        for i in range(len(inode_bitmap)):
            if inode_bitmap[i]:
                inode = self.block_list[inode_start + (i // inode_per_block)][i % inode_per_block]
                if inode["file_name"] == file_name:
                    return i
        return None
    

def save_drive(drive: Drive, filename: str) -> None:
    """
    Serialize a Drive object to JSON file for persistent storage.
    Creates the save directory if it doesn't exist.
    """
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    try:
        with open(os.path.join(SAVE_PATH, filename), "w") as f:
            json.dump(drive.__dict__, f, indent=4)
    except Exception as e:
        print(f"Error writing to file: {e}")

def load_drive(filename: str) -> Drive | None:
    """
    Load a Drive object from JSON file.
    Returns Drive instance or None if file not found or corrupted.
    """
    try:
        with open(os.path.join(SAVE_PATH, filename), "r") as f:
            data = json.load(f)
            # Reconstruct Drive object from saved data
            drive = Drive(name=data["block_list"][0]["name"], total_blocks=data["block_list"][0]["total_blocks"], block_list=data["block_list"])
            return drive
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file {filename}.")
        return None

if __name__ == "__main__":
    # Demo/testing code for the disk simulator
    MainDrive = Drive("A", total_blocks=64)
    drive = MainDrive.block_list
    test_inode = Inode("test.txt", "File", 1, [], "user", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), [7,7,7], [])
    test_inode2 = Inode("test2.txt", "File", 1, [], "user", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), [7,7,7], [])

    MainDrive.write_inode("Hello, World! This is a test file.", test_inode, MainDrive.find_free_inode())
    print(MainDrive.load_inode(1))
    MainDrive.write_inode("This is another test file.", test_inode2, MainDrive.find_free_inode())

    save_drive(MainDrive, "test_drive.json")

    print(MainDrive.find_file("test.txt"))
    print(MainDrive.find_file("test2.txt"))