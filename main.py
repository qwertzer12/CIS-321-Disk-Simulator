import cmd2
from disk_simulator import *

mounted_drives: dict[str, Drive] = {"A": Drive(64), "B": Drive(128)}

class MyApp(cmd2.Cmd):
    """A simple command-line application using cmd2."""
    def __init__(self):
        super().__init__()
        self.intro = "Welcome to MyApp! Type help or ? to list commands.\n"
        self.prompt = "AFS$ "
    delattr(cmd2.Cmd, 'do_shell')
    delattr(cmd2.Cmd, 'do_run_pyscript')
    delattr(cmd2.Cmd, 'do_run_script')
    delattr(cmd2.Cmd, 'do_py')
    delattr(cmd2.Cmd, 'do_edit')

    greet_parser = cmd2.Cmd2ArgumentParser()
    greet_parser.add_argument('-g', '--goodbye', action='store_true', help='switch to say goodbye')
    greet_parser.add_argument('name', nargs='+', help='name of the person to greet')
    @cmd2.with_argparser(greet_parser)
    def do_greet(self, args):
        """Greet the user."""
        if args.goodbye:
            self.poutput(f"Goodbye, {' '.join(args.name)}!")
        else:
            self.poutput(f"Hello, {' '.join(args.name)}!")


    def do_lsblk(self, args):
        """List block devices."""
        self.poutput("Listing block devices...")

        for path, drive in mounted_drives.items():
            self.poutput(f"Drive: {path}, Size: {drive.block_list[0]["total_blocks"]}")
        # Here you would add the actual logic to list block devices
        # For example, using the `lsblk` command and capturing its output

    mkdrive_parser = cmd2.Cmd2ArgumentParser()
    mkdrive_parser.add_argument('-s', '--size', type=int, help='Size of the new drive in blocks')
    mkdrive_parser.add_argument('name', nargs='+', help='Name of the new drive')
    @cmd2.with_argparser(mkdrive_parser)
    def do_mkdrive(self, args):
        """Create a new virtual drive."""

        if len(args.name) > 1:
            self.perror("Error: Drive can only be one word.")
            return
        name = args.name[0].upper() if args.name[0].isalpha() else args.name[0]

        size = args.size
        while size is None:
            self.poutput("Enter size:")
            answer = input()
            if not answer.isdigit():
                self.perror("Error: Size must be an integer.")
                pass
            else:
                size = int(answer)

        save_drive_to_json(Drive(size), name + ".json")
        self.poutput(f"Created new drive: {name}, Size: {size} blocks.\n Remember to mount the new drive.")



    def do_exit(self, args):
        """Exit the application."""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    import sys
    app = MyApp()
    sys.exit(app.cmdloop())