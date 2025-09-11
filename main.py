import cmd2
import argparse

class MyApp(cmd2.Cmd):
    """A simple command-line application using cmd2."""
    def __init__(self):
        super().__init__()
        self.intro = "Welcome to MyApp! Type help or ? to list commands.\n"
        self.prompt = "AFS$ "

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

    def do_exit(self, args):
        """Exit the application."""
        print("Goodbye!")
        return True

if __name__ == '__main__':
    import sys
    app = MyApp()
    sys.exit(app.cmdloop())