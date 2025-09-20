import cmd2
from disk_simulator import *

# Global state for the file system simulator
mounted_drives: dict[str, Drive] = {"A": Drive("A", 64), "B": Drive("B", 128)}  # Pre-mount sample drives
drive_choices:list[str] = [f[:-5] for f in os.listdir(SAVE_PATH) if f.endswith(".json")] if os.path.exists(SAVE_PATH) else []  # Available drive files
pwd = {"drive": None, "path": "/"}  # Current working directory state

class MyApp(cmd2.Cmd):
    """
    Command-line interface for the virtual file system simulator.
    Provides Unix-like commands for managing virtual drives and files.
    """
    def __init__(self) -> None:
        super().__init__()
        self.intro = "Welcome to MyApp! Type help or ? to list commands.\n"
        self.prompt = "AFS$ "
    
    # Remove unwanted cmd2 built-in commands for security/simplicity
    delattr(cmd2.Cmd, 'do_shell')
    delattr(cmd2.Cmd, 'do_run_pyscript')
    delattr(cmd2.Cmd, 'do_run_script')
    delattr(cmd2.Cmd, 'do_py')
    delattr(cmd2.Cmd, 'do_edit')


    # Sample command demonstrating cmd2 argument parsing
    greet_parser = cmd2.Cmd2ArgumentParser(description='Greet the user.')
    greet_parser.add_argument('-g', '--goodbye', action='store_true', help='switch to say goodbye')
    greet_parser.add_argument('name', nargs='+', help='name of the person to greet')
    @cmd2.with_argparser(greet_parser)
    def do_greet(self, args) -> None:
        if args.goodbye:
            self.poutput(f"Goodbye, {' '.join(args.name)}!")
        else:
            self.poutput(f"Hello, {' '.join(args.name)}!")


    # File system management commands
    lsblk_parser = cmd2.Cmd2ArgumentParser(description='List block devices.')
    lsblk_parser.add_argument('-a', '--all', action='store_true', help='include unmounted devices')
    @cmd2.with_argparser(lsblk_parser)
    def do_lsblk(self, args) -> None:
        """Display mounted drives and optionally available drive files."""
        mode = "all" if args.all else "mounted only"
        self.poutput(f"Mode: {mode}")

        if mode == "mounted only":
            if not mounted_drives:
                self.poutput("No drives are currently mounted.")
                return
            self.poutput("Mounted drives:")
            for path, drive in mounted_drives.items():
                self.poutput(f"Drive: {path}, Size: {drive.block_list[0]["total_blocks"]}")
            return
        elif mode == "all":
            self.poutput("All block devices:")
            if mounted_drives:
                self.poutput("    Mounted drives:")
                for path, drive in mounted_drives.items():
                    self.poutput(f"Drive: {path}, Size: {drive.block_list[0]["total_blocks"]}")
            unmounted_drives = []
            try:
                for file in os.listdir(SAVE_PATH):
                    if file.endswith(".json"):
                        unmounted_drives.append(file)
            except FileNotFoundError:
                pass
            if unmounted_drives:
                self.poutput("    Raw drive files:")
                for file in unmounted_drives:
                    self.poutput(f"Drive file: {file[0:-5]}")
                    if file not in drive_choices:
                        drive_choices.append(file[0:-5])





    # Drive creation command with validation and interactive prompts
    mkdrive_parser = cmd2.Cmd2ArgumentParser(description='Create a new virtual drive.')
    mkdrive_parser.add_argument('-b', '--block', type=int, help='Size of the new drive in blocks (must be at least 32)', default=None)
    mkdrive_parser.add_argument('-s', '--size', type=int, help='Size of the blocks in bytes (default 4096)', default=4096)
    mkdrive_parser.add_argument('-i', '--inode', type=int, help='Number of inodes (default 80)', default=80)
    mkdrive_parser.add_argument('name', nargs=1, help='Name of the new drive')
    @cmd2.with_argparser(mkdrive_parser)
    def do_mkdrive(self, args) -> None:
        """Create a new virtual drive with specified parameters, prompting for missing values."""
        name = args.name[0].upper() if args.name[0].isalpha() else args.name[0]

        block = args.block
        size = args.size
        inode = args.inode

        # Interactive validation loops for missing or invalid parameters
        while block is None:
            self.poutput("Enter block count:")
            answer = input()
            if not answer.isdigit():
                self.perror("Error: Blocks must be an integer.")
                pass
            elif int(answer) < 32:
                self.perror("Error: Blocks must be at least 32.")
                pass
            else:
                block = int(answer)
        
        if size < 1024:
            self.perror("Error: Block size must be at least 1024 bytes.")
            size = None
        
        while size is None:
            self.poutput("Enter block size (in bytes):")
            answer = input()
            if not answer.isdigit():
                self.perror("Error: Block size must be an integer.")
                pass
            elif int(answer) < 1024:
                self.perror("Error: Block size must be at least 1024 bytes.")
                pass
            else:
                size = int(answer)
            
        if inode < 1:
            self.perror("Error: There must be at least 1 inode.")
            inode = None

        while inode is None:
            self.poutput("Enter inode count:")
            answer = input()
            if not answer.isdigit():
                self.perror("Error: Inode count must be an integer.")
                pass
            elif int(answer) < 1:
                self.perror("Error: There must be at least 1 inode.")
                pass
            else:
                inode = int(answer)

        save_drive(Drive(name, block, None, size, inode), name + ".json")
        drive_choices.append(name)
        self.poutput(f"Created new drive: {name}, {block} blocks in {size} byte increments.\n Remember to mount the new drive.")





    rmdrive_parser = cmd2.Cmd2ArgumentParser(description='Remove a virtual drive file.')
    rmdrive_parser.add_argument('name', nargs=1, choices=drive_choices, help='Name of the drive to remove')
    @cmd2.with_argparser(rmdrive_parser)
    def do_rmdrive(self, args) -> None:

        name = args.name[0].upper() if args.name[0].isalpha() else args.name[0]
        try:
            os.remove(os.path.join(SAVE_PATH, name + ".json"))
            self.poutput(f"Removed drive file: {name}.json")
        except FileNotFoundError:
            self.perror(f"Error: Drive file {name}.json not found.")
        except Exception as e:
            self.perror(f"Error removing drive file {name}.json: {e}")




    # Drive mounting system - load drive files into memory for access
    mount_parser = cmd2.Cmd2ArgumentParser(description='Mount a virtual drive.')
    mount_parser.add_argument('-p', '--path', type=str, help='Path to mount the drive')
    mount_parser.add_argument('name', nargs=1, choices=drive_choices, help='Name of the drive to mount')
    @cmd2.with_argparser(mount_parser)
    def do_mount(self, args) -> None:
        """Load a drive file and make it accessible at a specified mount point."""
        path = args.path.upper() if args.path and args.path.isalpha() else args.path if args.path else None
        name = args.name[0]

        if path in mounted_drives:
            self.perror(f"Error: Drive {name} is already mounted.")
            path = None
        
        while path is None:
            self.poutput("Enter mount path (A-Z):")
            answer = input().upper()
            if not answer.isalpha() or len(answer) != 1:
                self.perror("Error: Path must be a single letter A-Z.")
                pass
            elif answer in mounted_drives:
                self.perror(f"Error: Path {answer} is already in use.")
                pass
            else:
                path = answer
        
        drive = load_drive(name + ".json")
        if drive is None:
            self.perror(f"Error: Could not load drive {name}. Make sure the file exists.")
            return
        mounted_drives[path] = drive

        self.poutput(f"Mounted drive {name} at {path}.")
    


    unmount_parser = cmd2.Cmd2ArgumentParser(description='Unmount a virtual drive.')
    unmount_parser.add_argument('path', nargs=1, help='Path of the drive to unmount')
    @cmd2.with_argparser(unmount_parser)
    def do_unmount(self, args) -> None:
        path = args.path[0].upper()
        if path not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {path}.")
            return
        del mounted_drives[path]
        self.poutput(f"Unmounted drive at {path}.")




    displaydata_parser = cmd2.Cmd2ArgumentParser(description='Display the contents of a mounted drive.')
    displaydata_parser.add_argument('path', nargs=1, help='Path of the drive to display')
    @cmd2.with_argparser(displaydata_parser)
    def do_displaydata(self, args) -> None:
        path = args.path[0].upper()
        if path not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {path}.")
            return
        drive = mounted_drives[path]
        self.poutput(f"Contents of drive at {path}:")
        data_start = drive.block_list[0]["data_start"]
        
        # Create visual representation of data block usage
        display: list[str] = []
        message = ""
        for i in range(data_start, drive.block_list[0]["total_blocks"]):
            if drive.block_list[i] == '':
                message += "-"  # Empty block
            else:
                message += "#"  # Used block
            if len(message) == 8:
                display.append(message)
                message = ""
        
        if message:
            display.append(message)
        
        print_chain = []
        for i in range(0, len(display)):
            print_chain.append(display[i])
            if (i + 1) % 2 == 0 or i == len(display) - 1:
                self.poutput(" ".join(print_chain))
                print_chain = []

    
    # File creation and writing system with path validation
    write_parser = cmd2.Cmd2ArgumentParser(description='Write data to a mounted drive.')
    write_parser.add_argument('path', nargs=1, help='Path of the file to write to (e.g., A:/file.txt, file.txt, ../file.txt)')
    write_parser.add_argument('data', nargs='?', help='Data to write to the file. Enclose in quotes for multiple words. If not provided, you will be prompted to enter the data.')
    @cmd2.with_argparser(write_parser)
    def do_write(self, args) -> None:
        """Write data to a file on a mounted drive, creating or overwriting as needed."""
        target_path = args.path[0]
        data = args.data if args.data else None
        
        # If no data provided, prompt user for input
        if data is None:
            self.poutput("Enter the data to write to the file (press Enter when done):")
            data = input()
            if data is None:
                data = ""  # Handle case where user presses Ctrl+C or similar

        # Resolve path (handle relative paths using current working directory)
        resolved_path = self._resolve_path(target_path)
        if resolved_path is None:
            return

        # Parse drive and file path
        if len(resolved_path) < 3 or resolved_path[1:3] != ":/":
            self.perror("Error: Invalid path format. Use format 'A:/filename' or relative paths like 'filename'.")
            return

        drive_letter = resolved_path[0].upper()
        file_path = resolved_path[3:] if len(resolved_path) > 3 else ""

        # Check if drive is mounted
        if drive_letter not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {drive_letter}.")
            return

        drive = mounted_drives[drive_letter]

        # Validate that we have a filename
        if file_path == "":
            self.perror("Error: Please specify a filename to write to.")
            return
        
        # Check if file is being written to a subdirectory
        if '/' in file_path:
            # Extract directory path from the resolved absolute path
            dir_parts = file_path.split('/')[:-1]  # Get all parts except the filename
            
            # Validate all parent directories exist using absolute paths
            for i in range(len(dir_parts)):
                # Build the absolute directory path up to this point
                dir_path_check = '/' + '/'.join(dir_parts[:i+1])
                
                # Check if the directory exists
                if drive.find_file(dir_path_check) is None:
                    display_dir_path = '/'.join(dir_parts[:i+1])
                    self.perror(f"Error: Directory '{display_dir_path}' does not exist. Create the directory first using mkdir.")
                    return
                
                # Check if the found path is actually a directory
                dir_inode_index = drive.find_file(dir_path_check)
                if dir_inode_index is not None:
                    inode_start = drive.block_list[0]["inode_start"]
                    inode_per_block = drive.block_list[0]["block_size"] // 256
                    dir_inode = drive.block_list[inode_start + (dir_inode_index // inode_per_block)][dir_inode_index % inode_per_block]
                    if dir_inode["file_type"].lower() != "directory":
                        display_dir_path = '/'.join(dir_parts[:i+1])
                        self.perror(f"Error: '{display_dir_path}' is not a directory.")
                        return

        # Check if file already exists
        existing_inode_index = drive.find_file(f"/{file_path}")
        if existing_inode_index is not None:
            # File exists - delete the old one to allow overwriting
            inode_start = drive.block_list[0]["inode_start"]
            inode_per_block = drive.block_list[0]["block_size"] // 256
            existing_inode = drive.block_list[inode_start + (existing_inode_index // inode_per_block)][existing_inode_index % inode_per_block]
            
            # Check if it's actually a file (not a directory)
            if existing_inode["file_type"].lower() == "directory":
                self.perror(f"Error: '{file_path}' is a directory, not a file.")
                return
            
            # Delete the existing file
            drive.delete_inode(existing_inode_index)
            self.poutput(f"Overwriting existing file '{file_path}'.")

        free_inode = drive.find_free_inode()
        if free_inode is None:
            self.perror("Error: No free inodes available.")
            return
        
        data_inode = Inode(
            file_name=f"/{file_path}",  # Store path without drive like "/foo/bar/file.txt"
            file_type="File",
            size=len(data),
            pointers=[],
            uid="user",
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            permissions=[7,7,7],
            mli_pointer=[]
        )

        if not drive.write_inode(data, data_inode, free_inode):
            self.perror("Error: Not enough space on drive to write data.")
            return
        self.poutput(f"Wrote data to {resolved_path} on drive.")
        save_drive(drive, drive.block_list[0]["name"] + ".json")
        return
        


    # Directory creation with extensive path validation
    mkdir_parser = cmd2.Cmd2ArgumentParser(description='Create a directory on a mounted drive.')
    mkdir_parser.add_argument('path', nargs=1, help='Path of the directory to create (e.g., A:/mydir, mydir, ../mydir)')
    @cmd2.with_argparser(mkdir_parser)
    def do_mkdir(self, args) -> None:
        """Create a directory with comprehensive validation of path format and parent directories."""
        target_path = args.path[0]
        
        # Resolve path (handle relative paths using current working directory)
        resolved_path = self._resolve_path(target_path)
        if resolved_path is None:
            return

        # Parse drive and directory path
        if len(resolved_path) < 3 or resolved_path[1:3] != ":/":
            self.perror("Error: Invalid path format. Use format 'A:/dirname' or relative paths like 'dirname'.")
            return

        drive_letter = resolved_path[0].upper()
        dir_name = resolved_path[3:] if len(resolved_path) > 3 else ""

        # Check if drive is mounted
        if drive_letter not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {drive_letter}.")
            return
        
        # Validate that we have a directory name
        if dir_name == "" or dir_name == "/":
            self.perror("Error: Directory name cannot be empty or just '/'.")
            return
        
        # Validate directory name characters (no invalid filesystem characters)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\']
        if any(char in dir_name for char in invalid_chars):
            self.perror(f"Error: Directory name contains invalid characters: {', '.join(invalid_chars)}")
            return
        
        # Validate directory name length (reasonable limit)
        if len(dir_name) > 255:
            self.perror("Error: Directory name too long (maximum 255 characters).")
            return
        
        # Validate no leading/trailing spaces or dots
        if dir_name.startswith(' ') or dir_name.endswith(' '):
            self.perror("Error: Directory name cannot start or end with spaces.")
            return
        if dir_name.startswith('.') or dir_name.endswith('.'):
            self.perror("Error: Directory name cannot start or end with dots.")
            return
        
        drive = mounted_drives[drive_letter]
        
        # Check if directory already exists
        existing_inode = drive.find_file(f"/{dir_name}")
        if existing_inode is not None:
            self.perror(f"Error: Directory '{dir_name}' already exists.")
            return
        
        # Validate parent directories exist for nested paths
        if '/' in dir_name:
            parts = dir_name.split('/')
            # Check each parent directory exists
            current_path_without_drive = "/"
            for i, part in enumerate(parts[:-1]):  # All parts except the last (which we're creating)
                current_path_without_drive += part
                if drive.find_file(current_path_without_drive) is None:
                    self.perror(f"Error: Parent directory '{'/'.join(parts[:i+1])}' does not exist. Create parent directories first.")
                    return
                
                # Verify it's actually a directory
                parent_inode_index = drive.find_file(current_path_without_drive)
                if parent_inode_index is not None:
                    inode_start = drive.block_list[0]["inode_start"]
                    inode_per_block = drive.block_list[0]["block_size"] // 256
                    parent_inode = drive.block_list[inode_start + (parent_inode_index // inode_per_block)][parent_inode_index % inode_per_block]
                    if parent_inode["file_type"].lower() != "directory":
                        self.perror(f"Error: '{'/'.join(parts[:i+1])}' is not a directory.")
                        return
                current_path_without_drive += "/"
        
        # Check for available inodes
        free_inode = drive.find_free_inode()
        if free_inode is None:
            self.perror("Error: No free inodes available.")
            return
        
        # Create directory inode
        dir_inode = Inode(
            file_name=f"/{dir_name}",  # Store path without drive like "/foo/bar"
            file_type="Directory",
            size=0,
            pointers=[],
            uid="user",
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            permissions=[7,7,7],
            mli_pointer=[]
        )
        
        # Write the inode to disk
        if not drive.write_inode('', dir_inode, free_inode):
            self.perror("Error: Not enough space on drive to create directory.")
            return
        
        self.poutput(f"Created directory '{resolved_path}'.")
        save_drive(drive, drive.block_list[0]["name"] + ".json")
        return




    rmdir_parser = cmd2.Cmd2ArgumentParser(description='Remove a directory from a mounted drive.')
    rmdir_parser.add_argument('path', nargs=1, help='Path of the directory to remove (e.g., A:/mydir)')
    @cmd2.with_argparser(rmdir_parser)
    def do_rmdir(self, args) -> None:
        pass


    # Directory navigation command - change working directory
    cd_parser = cmd2.Cmd2ArgumentParser(description='Change the current working directory.')
    cd_parser.add_argument('path', nargs='?', help='Directory path to change to (e.g., A:/, A:/mydir, mydir, .., .)')
    @cmd2.with_argparser(cd_parser)
    def do_cd(self, args) -> None:
        """Change the current working directory to an existing directory."""
        global pwd
        
        target_path = args.path if args.path else None
        
        # If no path specified, show current directory
        if target_path is None:
            if pwd["drive"] is None:
                self.poutput("No current directory set. Use 'cd A:/' to set initial directory.")
                return
            self.poutput(f"Current directory: {pwd['drive']}:{pwd['path']}")
            return
        
        # Resolve path (handle relative paths)
        resolved_path = self._resolve_path(target_path)
        if resolved_path is None:
            return
        
        # Parse drive and directory path
        if len(resolved_path) < 3 or resolved_path[1:3] != ":/":
            self.perror("Error: Invalid path format. Use format 'A:/' or 'A:/dirname'.")
            return
        
        drive_letter = resolved_path[0].upper()
        dir_path = resolved_path[3:] if len(resolved_path) > 3 else ""
        
        # Check if drive is mounted
        if drive_letter not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {drive_letter}.")
            return
        
        drive = mounted_drives[drive_letter]
        
        # Handle root directory case
        if dir_path == "":
            # Changing to root directory
            pwd["drive"] = drive_letter
            pwd["path"] = "/"
            self.poutput(f"Changed directory to {drive_letter}:/")
            # Update prompt to show current directory
            self.prompt = f"AFS:{drive_letter}:/$ "
            return
        
        # Check if the target directory exists
        target_full_path = f"/{dir_path}"
        dir_inode_index = drive.find_file(target_full_path)
        if dir_inode_index is None:
            self.perror(f"Error: Directory '{dir_path}' does not exist.")
            return
        
        # Verify it's actually a directory
        inode_start = drive.block_list[0]["inode_start"]
        inode_per_block = drive.block_list[0]["block_size"] // 256
        dir_inode = drive.block_list[inode_start + (dir_inode_index // inode_per_block)][dir_inode_index % inode_per_block]
        if dir_inode["file_type"].lower() != "directory":
            self.perror(f"Error: '{dir_path}' is not a directory.")
            return
        
        # Update the current working directory
        pwd["drive"] = drive_letter
        pwd["path"] = f"/{dir_path}"
        self.poutput(f"Changed directory to {drive_letter}:/{dir_path}")
        
        # Update prompt to show current directory
        self.prompt = f"AFS[{drive_letter}:/{dir_path}]$ "


    # Directory listing with support for relative and absolute paths
    ls_parser = cmd2.Cmd2ArgumentParser(description='List directory contents.')
    ls_parser.add_argument('path', nargs='?', help='Optional directory path to list (e.g., A:/, A:/mydir, mydir)')
    @cmd2.with_argparser(ls_parser)
    def do_ls(self, args) -> None:
        """List directory contents for the current working directory or specified path."""
        target_path = args.path if args.path else None
        
        # If no path specified, use current working directory
        if target_path is None:
            if pwd["drive"] is None:
                self.perror("Error: No current directory set. Please specify a path like 'A:/' or mount a drive and use 'cd'.")
                return
            target_path = f"{pwd['drive']}:{pwd['path']}"
        
        # Resolve path (handle relative paths)
        resolved_path = self._resolve_path(target_path)
        if resolved_path is None:
            return
        
        # Parse drive and directory path
        if len(resolved_path) < 3 or resolved_path[1:3] != ":/":
            self.perror("Error: Invalid path format. Use format 'A:/' or 'A:/dirname'.")
            return
        
        drive_letter = resolved_path[0].upper()
        dir_path = resolved_path[3:] if len(resolved_path) > 3 else ""
        
        # Check if drive is mounted
        if drive_letter not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {drive_letter}.")
            return
        
        drive = mounted_drives[drive_letter]
        
        # List files and directories
        self._list_directory_contents(drive, drive_letter, dir_path)
    
    def _resolve_path(self, path: str) -> str | None:
        """
        Resolve relative paths to absolute paths using current working directory.
        Handles ., .., and relative paths appropriately with proper path normalization.
        """
        if path.startswith('/'):
            # Absolute path without drive - use current drive
            if pwd["drive"] is None:
                self.perror("Error: No current directory set. Please specify a drive letter.")
                return None
            result_path = f"{pwd['drive']}:{path}"
        elif ':' in path:
            # Already absolute path with drive
            result_path = path
        else:
            # Relative path - combine with current directory
            if pwd["drive"] is None:
                self.perror("Error: No current directory set. Please specify a drive letter.")
                return None
            
            # Combine current path with relative path
            current_path = pwd["path"].rstrip('/')
            if current_path == "":
                current_path = "/"
            
            # Build combined path
            if current_path == "/":
                combined = f"/{path}"
            else:
                combined = f"{current_path}/{path}"
            
            result_path = f"{pwd['drive']}:{combined}"
        
        # Now normalize the path to resolve .. and . components
        return self._normalize_path(result_path)
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path by resolving . and .. components.
        Takes a path like 'A:/dir1/dir2/../file.txt' and returns 'A:/dir1/file.txt'
        """
        if ':' not in path:
            return path
            
        drive_part, path_part = path.split(':', 1)
        
        # Split path into components
        if path_part.startswith('/'):
            path_part = path_part[1:]  # Remove leading slash
        
        if path_part == "":
            return f"{drive_part}:/"
            
        components = path_part.split('/')
        normalized = []
        
        for component in components:
            if component == '.' or component == '':
                # Skip current directory references and empty components
                continue
            elif component == '..':
                # Go up one directory
                if normalized:
                    normalized.pop()
                # If we're already at root, .. has no effect
            else:
                normalized.append(component)
        
        # Reconstruct the path
        if not normalized:
            return f"{drive_part}:/"
        else:
            return f"{drive_part}:/{'/'.join(normalized)}"
    
    def _list_directory_contents(self, drive: Drive, drive_letter: str, dir_path: str) -> None:
        """
        List the contents of a directory by scanning inodes for matching file paths.
        Displays files and directories in a formatted table with type, name, size, and modification time.
        """
        # Determine what we're looking for
        if dir_path == "":
            # Root directory
            current_dir = "/"
            target_prefix = "/"
        else:
            # Subdirectory
            current_dir = f"/{dir_path}"
            target_prefix = f"/{dir_path}/"
        
        # Check if the target directory exists (unless it's root)
        if dir_path != "":
            target_full_path = f"/{dir_path}"
            dir_inode_index = drive.find_file(target_full_path)
            if dir_inode_index is None:
                self.perror(f"Error: Directory '{dir_path}' does not exist.")
                return
            
            # Verify it's actually a directory
            inode_start = drive.block_list[0]["inode_start"]
            inode_per_block = drive.block_list[0]["block_size"] // 256
            dir_inode = drive.block_list[inode_start + (dir_inode_index // inode_per_block)][dir_inode_index % inode_per_block]
            if dir_inode["file_type"].lower() != "directory":
                self.perror(f"Error: '{dir_path}' is not a directory.")
                return
        
        # Collect all files and directories by scanning inode table
        items = []
        inode_bitmap = drive.block_list[drive.block_list[0]["inode_bitmap_start"]]
        inode_start = drive.block_list[0]["inode_start"]
        inode_per_block = drive.block_list[0]["block_size"] // 256
        
        for i in range(len(inode_bitmap)):
            if inode_bitmap[i]:
                inode = drive.block_list[inode_start + (i // inode_per_block)][i % inode_per_block]
                file_name = inode["file_name"]
                file_type = inode["file_type"]
                
                # Skip free inodes and the root directory itself
                if file_type == "free" or file_name == "/":
                    continue
                
                # For root directory listing
                if dir_path == "":
                    # Show items directly in root (like /test, not /test/something)
                    if file_name.startswith("/") and file_name != "/":
                        # Remove the leading slash for display
                        display_name = file_name[1:]
                        # Only show direct children (no further slashes)
                        if "/" not in display_name:
                            items.append({
                                "name": display_name,
                                "type": file_type,
                                "size": inode["size"],
                                "modified": inode["time_modified"]
                            })
                else:
                    # For subdirectory listing
                    if file_name.startswith(target_prefix):
                        # Get the relative name after the directory prefix
                        relative_name = file_name[len(target_prefix):]
                        # Only show direct children (no further slashes)
                        if "/" not in relative_name and relative_name != "":
                            items.append({
                                "name": relative_name,
                                "type": file_type,
                                "size": inode["size"],
                                "modified": inode["time_modified"]
                            })
        
        # Display results in formatted table
        if not items:
            self.poutput(f"Directory '{drive_letter}:{current_dir}' is empty.")
            return
        
        self.poutput(f"Contents of '{drive_letter}:{current_dir}':")
        self.poutput(f"{'Type':<10} {'Name':<20} {'Size':<8} {'Modified'}")
        self.poutput("-" * 60)
        
        # Sort items: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x["type"].lower() != "directory", x["name"].lower()))
        
        for item in items:
            type_display = "DIR" if item["type"].lower() == "directory" else "FILE"
            size_display = "-" if item["type"].lower() == "directory" else str(item["size"])
            self.poutput(f"{type_display:<10} {item['name']:<20} {size_display:<8} {item['modified']}")


    # File content display command
    cat_parser = cmd2.Cmd2ArgumentParser(description='Display the contents of a file.')
    cat_parser.add_argument('path', nargs=1, help='Path of the file to display (e.g., A:/file.txt, file.txt, ../file.txt)')
    @cmd2.with_argparser(cat_parser)
    def do_cat(self, args) -> None:
        """Display the contents of a file on a mounted drive."""
        target_path = args.path[0]
        
        # Resolve path (handle relative paths using current working directory)
        resolved_path = self._resolve_path(target_path)
        if resolved_path is None:
            return
        
        # Parse drive and file path
        if len(resolved_path) < 3 or resolved_path[1:3] != ":/":
            self.perror("Error: Invalid path format. Use format 'A:/filename' or relative paths like 'filename'.")
            return
        
        drive_letter = resolved_path[0].upper()
        file_path = resolved_path[3:] if len(resolved_path) > 3 else ""
        
        # Check if drive is mounted
        if drive_letter not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {drive_letter}.")
            return
        
        # Validate that we have a filename
        if file_path == "":
            self.perror("Error: Please specify a filename to display.")
            return
        
        drive = mounted_drives[drive_letter]
        
        # Check if file exists
        file_inode_index = drive.find_file(f"/{file_path}")
        if file_inode_index is None:
            self.perror(f"Error: File '{file_path}' does not exist.")
            return
        
        # Verify it's actually a file (not a directory)
        inode_start = drive.block_list[0]["inode_start"]
        inode_per_block = drive.block_list[0]["block_size"] // 256
        file_inode = drive.block_list[inode_start + (file_inode_index // inode_per_block)][file_inode_index % inode_per_block]
        
        if file_inode["file_type"].lower() == "directory":
            self.perror(f"Error: '{file_path}' is a directory, not a file. Use 'ls' to list directory contents.")
            return
        
        # Read and display file contents
        file_content = drive.load_inode(file_inode_index)
        if file_content is None:
            self.perror(f"Error: Unable to read file '{file_path}'.")
            return
        
        # Display the file content
        if file_content == "":
            self.poutput(f"File '{file_path}' is empty.")
        else:
            self.poutput(file_content)


    def do_exit(self, args) -> bool:
        """Exit the application."""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    import sys
    app = MyApp()
    sys.exit(app.cmdloop())