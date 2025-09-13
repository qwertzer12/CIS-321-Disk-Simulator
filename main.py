import cmd2
from disk_simulator import *

mounted_drives: dict[str, Drive] = {"A": Drive(64), "B": Drive(128)}

class MyApp(cmd2.Cmd):
    """A simple command-line application using cmd2."""
    def __init__(self) -> None:
        super().__init__()
        self.intro = "Welcome to MyApp! Type help or ? to list commands.\n"
        self.prompt = "AFS$ "
    delattr(cmd2.Cmd, 'do_shell')
    delattr(cmd2.Cmd, 'do_run_pyscript')
    delattr(cmd2.Cmd, 'do_run_script')
    delattr(cmd2.Cmd, 'do_py')
    delattr(cmd2.Cmd, 'do_edit')




    greet_parser = cmd2.Cmd2ArgumentParser(description='Greet the user.')
    greet_parser.add_argument('-g', '--goodbye', action='store_true', help='switch to say goodbye')
    greet_parser.add_argument('name', nargs='+', help='name of the person to greet')
    @cmd2.with_argparser(greet_parser)
    def do_greet(self, args) -> None:
        if args.goodbye:
            self.poutput(f"Goodbye, {' '.join(args.name)}!")
        else:
            self.poutput(f"Hello, {' '.join(args.name)}!")



    lsblk_parser = cmd2.Cmd2ArgumentParser(description='List block devices.')
    @cmd2.with_argparser(lsblk_parser)
    def do_lsblk(self, args) -> None:
        self.poutput("Listing block devices...")

        for path, drive in mounted_drives.items():
            self.poutput(f"Drive: {path}, Size: {drive.block_list[0]["total_blocks"]}")
        # Here you would add the actual logic to list block devices
        # For example, using the `lsblk` command and capturing its output




    mkdrive_parser = cmd2.Cmd2ArgumentParser(description='Create a new virtual drive.')
    mkdrive_parser.add_argument('-b', '--block', type=int, help='Size of the new drive in blocks')
    mkdrive_parser.add_argument('-s', '--size', type=int, help='Size of the blocks in bytes (default 4096)', default=4096)
    mkdrive_parser.add_argument('-i', '--inode', type=int, help='Number of inodes (default 80)', default=80)
    mkdrive_parser.add_argument('name', nargs=1, help='Name of the new drive')
    @cmd2.with_argparser(mkdrive_parser)
    def do_mkdrive(self, args) -> None:
        name = args.name[0].upper() if args.name[0].isalpha() else args.name[0]

        block = args.block
        size = args.size
        inode = args.inode
        while block is None:
            self.poutput("Enter block count:")
            answer = input()
            if not answer.isdigit():
                self.perror("Error: Blocks must be an integer.")
                pass
            else:
                block = int(answer)

        save_drive(Drive(block, None, size, inode), name + ".json")
        self.poutput(f"Created new drive: {name}, {block} blocks in {size} byte increments.\n Remember to mount the new drive.")




    mount_parser = cmd2.Cmd2ArgumentParser(description='Mount a virtual drive.')
    mount_parser.add_argument('-p', '--path', type=str, help='Path to mount the drive')
    mount_parser.add_argument('name', nargs=1, help='Name of the drive to mount')
    @cmd2.with_argparser(mount_parser)
    def do_mount(self, args) -> None:
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




    def do_exit(self, args) -> bool:
        """Exit the application."""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    import sys
    app = MyApp()
    sys.exit(app.cmdloop())