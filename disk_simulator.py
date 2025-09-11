import json

class Inode:
    def __init__(self, file_type: str, size: int, pointers: list):
        self.file_type = file_type  # 'file' or 'directory'
        self.size = size            # size in bytes
        self.pointers = pointers    # list of block indices

drive = [None] * 64

drive[0] = "superblock"
drive[1] = "inode_bitmap"
drive[2] = "data_bitmap"

for i in range(3, 8):
    drive[i] = Inode(file_type=i, size=0, pointers=[]).__dict__

for i in range(8, 64):
    drive[i] = "data_block_" + i.__str__()

for i in range(len(drive)):
    print(f"Block {i}: {drive[i]}")

try:
    with open("virtual_disk.json", "w") as f:
        json.dump(drive, f, indent=4)
except Exception as e:
    print(f"Error writing to file: {e}")

