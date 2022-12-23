"""Run dance-a-mole as Python module."""

import danceamole.main

if __name__ == "__main__":
    # The ``prog`` needs to be set in the argparse.
    # Otherwise, the program name in the help shown to the user will be ``__main__``.
    danceamole.main.main(prog="danceamole")
