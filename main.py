import cmd2
from disk_simulator import *

mounted_drives: dict[str, Drive] = {"A": Drive(64), "B": Drive(128)}
drive_choices:list[str] = [f[:-5] for f in os.listdir(SAVE_PATH) if f.endswith(".json")] if os.path.exists(SAVE_PATH) else []

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
    lsblk_parser.add_argument('-a', '--all', action='store_true', help='include unmounted devices')
    @cmd2.with_argparser(lsblk_parser)
    def do_lsblk(self, args) -> None:
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





    mkdrive_parser = cmd2.Cmd2ArgumentParser(description='Create a new virtual drive.')
    mkdrive_parser.add_argument('-b', '--block', type=int, help='Size of the new drive in blocks (must be at least 32)', default=None)
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

        save_drive(Drive(block, None, size, inode), name + ".json")
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




    mount_parser = cmd2.Cmd2ArgumentParser(description='Mount a virtual drive.')
    mount_parser.add_argument('-p', '--path', type=str, help='Path to mount the drive')
    mount_parser.add_argument('name', nargs=1, choices=drive_choices, help='Name of the drive to mount')
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
        display: list[str] = []
        message = ""
        for i in range(data_start, drive.block_list[0]["total_blocks"]):
            if drive.block_list[i] == '':
                message += "-"
            else:
                message += "#"
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

    


    write_parser = cmd2.Cmd2ArgumentParser(description='Write data to a mounted drive.')
    write_parser.add_argument('path', nargs=1, help='Path of the drive to write to')
    write_parser.add_argument('data', nargs='1', help='Data to write to the file. Enclose in quotes for multiple words.')
    @cmd2.with_argparser(write_parser)
    def do_write(self, args) -> None:
        self.poutput(args.path)
        self.poutput(args.data)
        path = args.path[0]
        if path[0] not in mounted_drives:
            self.perror(f"Error: No drive is mounted at {path[0]}.")
            return
        data = args.data[0]
        
        drive = mounted_drives[path[0]]
        
        




    def do_exit(self, args) -> bool:
        """Exit the application."""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    import sys
    app = MyApp()
    sys.exit(app.cmdloop())