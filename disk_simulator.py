import json
import math
import os

SAVE_PATH = "drive_bay"

class Inode:
    def __init__(self, file_type: str, size: int, pointers: list) -> None:
        self.file_type = file_type  # 'file' or 'directory'
        self.size = size            # size in bytes
        self.pointers = pointers    # list of block indices

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
            self.block_list[inode_start + (i // inode_per_block)][i % inode_per_block] = Inode(file_type="free", size=0, pointers=[]).__dict__

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

    drive[0] = { # Superblock
        "total_blocks": len(drive),
        "block_size": 4096,

        "inode_bitmap_start": 1,
        "inode_bitmap_size": 1,
        "data_bitmap_start": 2,
        "data_bitmap_size": 1,
        "inode_start": 3,
        "inode_size": 5,
        "data_start": 8,
        "data_size": 56
    }
    drive[1] = [False] * (64 - 8) # inode bitmap
    drive[2] = [False] * (64 - 8) # data bitmap

    for i in range(3, 8):
        drive[i] = Inode(file_type=i, size=0, pointers=[(12,42),(45,48)]).__dict__

    for i in range(8, 64):
        drive[i] = "data_block_" + i.__str__()

    for i in range(len(drive)):
        print(f"Block {i}: {drive[i]}")

    # Save the drive structure to a JSON file
    save_drive(MainDrive, "virtual_disk.json")

