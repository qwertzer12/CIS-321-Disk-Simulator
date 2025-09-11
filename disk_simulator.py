import json

drive = [None] * 64

drive[0] = "superblock"
drive[1] = "inode_bitmap"
drive[2] = "data_bitmap"

for i in range(3, 8):
    drive[i] = "inode_" + i.__str__()

for i in range(8, 64):
    drive[i] = "data_block_" + i.__str__()

for i in range(len(drive)):
    print(f"Block {i}: {drive[i]}")

json_drive = json.dumps(drive, indent=4)
with open("virtual_disk.json", "w") as f:
    f.write(json_drive)

