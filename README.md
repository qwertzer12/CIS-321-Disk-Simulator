# CIS 321 Disk Simulator

A command-line virtual disk simulator written in Python. This project allows you to create, mount, manage, and interact with virtual drives using a custom shell interface.

## Features

- Create and remove virtual drives
- Mount and unmount drives
- List block devices (mounted and unmounted)
- Write data to drives
- Display drive contents
- Simulate basic file system operations

## Requirements

- Python 3.10+
- [cmd2](https://github.com/python-cmd2/cmd2)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Getting Started

Run the main application:

```bash
python main.py
```

You will be greeted with a custom shell prompt (`AFS$`). Type `help` or `?` to list available commands.

---

## Command Reference

### greet

_Greet a user or say goodbye._

Usage:

```greet [-g|--goodbye] name
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### lsblk

_List block devices._

Usage:

```lsblk [-a|--all]
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### mkdrive

_Create a new virtual drive._

Usage:

```mkdrive [-b BLOCKS] [-s SIZE] [-i INODE] name
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### rmdrive

_Remove a virtual drive file._

Usage:

```rmdrive name
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### mount

_Mount a virtual drive._

Usage:

```mount [-p PATH] name
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### unmount

_Unmount a virtual drive._

Usage:

```unmount path
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### displaydata

_Display the contents of a mounted drive._

Usage:

```displaydata path
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### write

_Write data to a mounted drive._

Usage:

```write path data
```

Instructions: <!-- TODO: Add usage examples and details here -->

---

### exit

_Exit the application._

Usage:

```exit
```

---

## Notes

- All virtual drives are stored as JSON files in the `drive_bay/` directory.
- Make sure to mount a drive before performing operations on it.
- For more details on each command, use the `help` command within the shell.
