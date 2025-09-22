# CIS 321 Disk Simulator

A comprehensive command-line virtual disk simulator written in Python that implements a Unix-like file system. This project allows you to create, mount, manage, and interact with virtual drives using a custom shell interface with full directory navigation, file operations, and data persistence.

## Features

- **Virtual Drive Management**: Create, remove, mount, and unmount virtual drives
- **File System Operations**: Complete file system with inodes, bitmaps, and data blocks
- **Directory Navigation**: Full support for hierarchical directories with relative and absolute paths
- **File Operations**: Create, write, read, and display files with content
- **Tab Completion**: Smart path completion for files and directories
- **Interactive Demo**: Comprehensive tutorial showcasing all system capabilities
- **Data Persistence**: All drives saved as JSON files for session recovery
- **Unix-like Commands**: Familiar command interface (ls, cd, cat, mkdir, etc.)

## Requirements

- Python 3.10+
- [cmd2](https://github.com/python-cmd2/cmd2) - Advanced command-line interface framework

Install dependencies:

```bash
pip install -r requirements.txt
```

## Getting Started

Run the main application:

```bash
python main.py
```

You will be greeted with the AFS (Abstract File System) shell prompt. Type `help` or `?` to list available commands.

### Quick Start with Demo

For a comprehensive introduction to the system, run the interactive demo:

```bash
AFS$ demo
```

This will walk you through all major features with explanations and examples.

---

## Command Reference

### File System Management

#### lsblk - List Block Devices

*Display mounted drives and available drive files.*

Usage:

```bash
lsblk [-a|--all]
```

Options:

- `-a, --all`: Include unmounted devices in listing

Examples:

```bash
AFS$ lsblk                    # Show only mounted drives
AFS$ lsblk -a                 # Show all drives (mounted and unmounted)
```

---

#### mkdrive - Create Virtual Drive

*Create a new virtual drive with specified parameters.*

Usage:

```bash
mkdrive [-b BLOCKS] [-s SIZE] [-i INODE] name
```

Options:

- `-b, --block`: Number of blocks (minimum 32, default: interactive prompt)
- `-s, --size`: Block size in bytes (minimum 1024, default: 4096)
- `-i, --inode`: Number of inodes (minimum 1, default: 80)

Examples:

```bash
AFS$ mkdrive MYDRIVE -b 100 -s 4096 -i 50    # Create drive with specific parameters
AFS$ mkdrive STORAGE                          # Create drive with interactive prompts
```

---

#### rmdrive - Remove Virtual Drive

*Remove a virtual drive file from storage.*

Usage:

```bash
rmdrive name
```

Examples:

```bash
AFS$ rmdrive MYDRIVE          # Remove the MYDRIVE.json file
```

**Note**: Drive must be unmounted before removal.

---

#### mount - Mount Virtual Drive

*Load a drive file and make it accessible at a mount point.*

Usage:

```bash
mount [-p PATH] name
```

Options:

- `-p, --path`: Mount path (A-Z, default: interactive prompt)

Examples:

```bash
AFS$ mount MYDRIVE -p C       # Mount MYDRIVE at C:
AFS$ mount STORAGE            # Mount with interactive path selection
```

---

#### unmount - Unmount Virtual Drive

*Disconnect a mounted drive from the file system.*

Usage:

```bash
unmount path
```

Examples:

```bash
AFS$ unmount C                # Unmount drive at C:
```

---

### File and Directory Operations

#### ls - List Directory Contents

*Display files and directories in the specified or current directory.*

Usage:

```bash
ls [path]
```

Examples:

```bash
AFS$ ls                       # List current directory
AFS$ ls C:/                   # List root of drive C:
AFS$ ls documents             # List subdirectory (relative path)
AFS$ ls ..                    # List parent directory
AFS$ ls C:/documents          # List absolute path
```

---

#### cd - Change Directory

*Navigate to a different directory.*

Usage:

```bash
cd [path]
```

Examples:

```bash
AFS$ cd C:/                   # Change to drive root
AFS$ cd documents             # Change to subdirectory
AFS$ cd ..                    # Go to parent directory
AFS$ cd                       # Show current directory
```

---

#### mkdir - Create Directory

*Create a new directory.*

Usage:

```bash
mkdir path
```

Examples:

```bash
AFS$ mkdir documents          # Create directory in current location
AFS$ mkdir C:/projects        # Create with absolute path
AFS$ mkdir photos/vacation    # Create nested directory (parents must exist)
```

---

#### write - Write File

*Create or overwrite a file with specified content.*

Usage:

```bash
write path [data]
```

Examples:

```bash
AFS$ write readme.txt "Welcome to my project"     # Create file with content
AFS$ write C:/documents/notes.txt                 # Create file with interactive input
AFS$ write config.json '{"setting": "value"}'    # Create JSON file
```

**Note**: If data is not provided, you'll be prompted to enter it interactively.

---

#### cat - Display File Contents

*Read and display the contents of a file.*

Usage:

```bash
cat path
```

Examples:

```bash
AFS$ cat readme.txt           # Display file in current directory
AFS$ cat C:/documents/notes.txt   # Display file with absolute path
AFS$ cat ../config.json       # Display file with relative path
```

---

### System Information

#### displaydata - Show Drive Layout

*Display visual representation of drive data block usage.*

Usage:

```bash
displaydata path
```

Examples:

```bash
AFS$ displaydata C            # Show data layout for drive C:
```

Output shows used (#) and free (-) blocks in a visual grid format.

---

#### demo - Interactive Tutorial

*Run a comprehensive demonstration of all system features.*

Usage:

```bash
demo
```

The demo includes:

- Virtual drive creation and mounting
- Directory structure creation
- File operations and content management
- Navigation with relative paths
- System monitoring and diagnostics

---

### Utility Commands

#### greet - Sample Command

*Demonstration command showing argument parsing.*

Usage:

```bash
greet [-g|--goodbye] name
```

Examples:

```bash
AFS$ greet Alice              # Say hello to Alice
AFS$ greet --goodbye Bob      # Say goodbye to Bob
```

---

#### exit - Exit Application

*Close the AFS shell.*

Usage:

```bash
exit
```

---

## Advanced Features

### Path Resolution

The system supports both absolute and relative paths:

- **Absolute paths**: `C:/documents/file.txt`
- **Relative paths**: `documents/file.txt`
- **Parent directory**: `..` (go up one level)
- **Current directory**: `.` (current location)
- **Sibling directories**: `../photos` (go up, then into photos)

### Tab Completion

Smart tab completion is available for:

- Drive letters (A:, B:, C:, etc.)
- Directory names
- File names
- Command names

### Working Directory

The shell maintains a current working directory concept:

- Prompt shows current location: `AFS[C:/documents]$`
- Relative paths resolve from current directory
- Use `cd` without arguments to see current location

## File System Structure

### Virtual Drive Layout

Each virtual drive uses a Unix-like file system structure:

```Block 0:     Superblock (metadata)
Block 1:     Inode bitmap
Block 2:     Data block bitmap  
Block 3-N:   Inode table
Block N+1-M: Data blocks
```

### Data Storage

- **Inodes**: Store file metadata (name, size, permissions, timestamps)
- **Data blocks**: Store actual file content (32 bytes per block for demo)
- **Bitmaps**: Track allocation of inodes and data blocks
- **Directories**: Special inodes that organize file hierarchy

---

## Example Workflow

Here's a typical session demonstrating the system:

```bash
# Start the application
python main.py

# Create and mount a drive
AFS$ mkdrive WORKSPACE -b 64 -s 4096 -i 40
AFS$ mount WORKSPACE -p D
AFS$ cd D:/

# Create directory structure
AFS[D:/]$ mkdir projects
AFS[D:/]$ mkdir documents
AFS[D:/]$ mkdir temp

# Create some files
AFS[D:/]$ write README.md "# My Workspace\nThis is my project workspace."
AFS[D:/]$ write projects/todo.txt "- Learn file systems\n- Complete project\n- Write documentation"

# Navigate and explore
AFS[D:/]$ ls
AFS[D:/]$ cd projects
AFS[D:/projects]$ ls
AFS[D:/projects]$ cat todo.txt
AFS[D:/projects]$ ls ..
AFS[D:/projects]$ cd ..

# System information
AFS[D:/]$ lsblk
AFS[D:/]$ displaydata D
```

---

## Troubleshooting

### Common Issues

#### "No drive is mounted at X:"

- Make sure you've mounted a drive at that path using `mount`
- Check mounted drives with `lsblk`

#### "Directory does not exist"

- Verify the path exists using `ls`
- Use tab completion to see available options
- Check your current directory with `cd`

#### "No free inodes available"

- The drive is full of files/directories
- Create a new drive with more inodes using `mkdrive -i <count>`

#### "Not enough space on drive"

- The drive's data blocks are full
- Create a larger drive using `mkdrive -b <blocks>`

### Tips

- Use the `demo` command to learn the system interactively
- Tab completion helps with path navigation
- The prompt shows your current location
- All drives are saved automatically to `drive_bay/` directory
- Use relative paths (`..`, `.`) for efficient navigation

---

## Technical Details

### Implementation

- **Language**: Python 3.10+
- **CLI Framework**: cmd2 for advanced command parsing and completion
- **Storage**: JSON serialization for drive persistence
- **Architecture**: Unix-like file system with inodes and block allocation

### File System Features

- **Hierarchical directories**: Full directory tree support
- **Path resolution**: Absolute and relative path handling
- **Block allocation**: First-fit allocation strategy
- **Metadata tracking**: Creation, modification, and access times
- **Permission system**: Unix-style permission bits
- **Data integrity**: Bitmap-based allocation tracking

---

## Notes

- All virtual drives are stored as JSON files in the `drive_bay/` directory
- Drive files persist between sessions - mounted drives are restored on startup
- Block size and inode count are set at drive creation and cannot be changed
- The system uses 32-byte data blocks for demonstration purposes
- File names are case-sensitive and follow Unix conventions
- Maximum file name length is 255 characters

For more details on each command, use the `help <command>` within the shell.
