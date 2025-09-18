import json
import math
import os
import datetime

SAVE_PATH = "drive_bay"

class Inode:
    def __init__(self,file_name: str, file_type: str, size: int, pointers: list[tuple], uid: str, time: str, permissions: list[int], mli_pointer: list = []) -> None:
        self.file_name = file_name                                              # Name of the file or directory
        self.file_type = file_type                                              # 'file' or 'directory'
        self.size = size                                                        # size in bytes
        self.pointers = pointers                                                # list of block indices. Each tuple is (start_block, length)
        self.uid = uid                                                          # File creator
        self.time_accessed = time                                               # Last accessed time
        self.time_modified = time                                               # Last modified time
        self.time_created = time                                                # Creation time
        self.time_deleted = None                                                # Deletion time
        self.blocks_used = 0
        self.update_blocks_used()                                               # Number of blocks used
        self.permissions = permissions                                          # 3 ints for user, group, others (rwx as 4+2+1)
        self.mli_pointer = mli_pointer                                          # Pointers for Multi-Level Indexing (if needed)
    
    # def __init__(self, pointers: list[tuple], mli_pointer: list = [], MLI_TRUE = True): # Multi-Level Indexing constructor
    #     self.pointers = pointers
    #     self.mli_pointer = mli_pointer
    #     self.MLI_TRUE = MLI_TRUE
    #     self.blocks_used = 0
    #     self.update_blocks_used()
    
    def update_access_time(self) -> None:
        self.time_accessed = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def update_modified_time(self) -> None:
        self.time_modified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_access_time()
    
    def update_deleted_time(self) -> None:
        self.time_deleted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_modified_time()
    
    def update_blocks_used(self) -> None:
        self.blocks_used = sum([b for a, b in self.pointers])

class Drive:
    def __init__(self, total_blocks: int, block_list: list = None, block_size: int = 4096, inode_count: int = 80) -> None:
        self.block_list = block_list if block_list is not None else [None] * total_blocks
        inode_bitmap_start = 1
        data_bitmap_start = inode_bitmap_start + 1
        inode_start = data_bitmap_start + 1
        inode_per_block = block_size // 256  # Assuming each inode is 16 bytes
        inode_size = math.ceil(inode_count / inode_per_block)  # Assuming each inode is 16 bytes
        data_size = total_blocks - (inode_start + inode_size)


        self.block_list[0] = { # Superblock
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
        self.block_list[inode_bitmap_start] = [False] * inode_count # initialize inode bitmap
        self.block_list[data_bitmap_start] = [False] * data_size # initialize data bitmap
        for i in range(inode_start, inode_start + inode_size): # initialize inode blocks
            self.block_list[i] = [None] * inode_per_block
        
        for i in range(inode_count): # initialize inodes as free
            self.block_list[inode_start + (i // inode_per_block)][i % inode_per_block] = Inode(file_name='' ,file_type="free", size=0, pointers=[], uid='', time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), permissions=[7,7,7]).__dict__
        
        for i in range(self.block_list[0]["data_start"], total_blocks): # initialize data blocks
            self.block_list[i] = ''

    def find_free_inode(self) -> int | None:
        inode_bitmap = self.block_list[self.block_list[0]["inode_bitmap_start"]]
        for i, used in enumerate(inode_bitmap):
            if not used:
                return i
        return None
    
    def find_free_data_blocks(self, count: int) -> list[tuple] | None:
        data_bitmap = self.block_list[self.block_list[0]["data_bitmap_start"]]
        free_blocks = []
        start = None
        length = 0
        progress = 0

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
    
    def write_file(self, data: str, file_inode: Inode, inode_index: int) -> bool:
        INODE_BLOCK_START = self.block_list[0]["inode_bitmap_start"]

        CHAR_BLOCK_SIZE = 32  # Number of characters per block
        DATA_BLOCKS_NEEDED = math.ceil(len(data) / CHAR_BLOCK_SIZE)
        FREE_DATA_BLOCKS = self.find_free_data_blocks(DATA_BLOCKS_NEEDED)

        if FREE_DATA_BLOCKS is None:
            return False
        
        DATA_BITMAP_START = self.block_list[0]["data_bitmap_start"]
        DATA_START = self.block_list[0]["data_start"]
        data_offset = 0
        for (start, length) in FREE_DATA_BLOCKS:
            for j in range(length):
                self.block_list[DATA_BITMAP_START][start + j] = True  # Mark data block as used
                block_data = data[data_offset:data_offset+CHAR_BLOCK_SIZE]
                self.block_list[DATA_START + start + j] = block_data  # Write data to block
                data_offset += CHAR_BLOCK_SIZE

        file_inode.pointers = FREE_DATA_BLOCKS
        file_inode.size = len(data)
        file_inode.update_modified_time()
        self.block_list[self.block_list[0]["inode_start"] + (inode_index // (self.block_list[0]["block_size"] // 256))][inode_index % (self.block_list[0]["block_size"] // 256)] = file_inode.__dict__

        

        self.block_list[INODE_BLOCK_START][inode_index] = True  # Mark inode as used
        return True
    

def save_drive(drive: Drive, filename: str) -> None:
    
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    try:
        with open(os.path.join(SAVE_PATH, filename), "w") as f:
            json.dump(drive.__dict__, f, indent=4)
    except Exception as e:
        print(f"Error writing to file: {e}")

def load_drive(filename: str) -> Drive | None:
    try:
        with open(os.path.join(SAVE_PATH, filename), "r") as f:
            data = json.load(f)
            drive = Drive(total_blocks=data["block_list"][0]["total_blocks"], block_list=data["block_list"])
            return drive
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file {filename}.")
        return None

if __name__ == "__main__":
    MainDrive = Drive(total_blocks=64)
    drive = MainDrive.block_list
    test_inode = Inode("test.txt", "File", 1, [], "user", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), [7,7,7], [])
    MainDrive.write_file("Hello, World! This is a test file.", test_inode, MainDrive.find_free_inode())
    save_drive(MainDrive, "test_drive.json")