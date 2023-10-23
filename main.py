# This is a sample Python script.
import argparse

from app.app_manager import AppManager
from app.manifest import Manifest
from common import cleanup_temporary_folders
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


from gui.main_window import MainWindow
from app.state import State


def main(args):
    state = State()
    app_manager = AppManager(state, args.terraformer_path)
    window = MainWindow(state, app_manager)
    window.mainloop()
    cleanup_temporary_folders()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Your script description")
    parser.add_argument("--terraformer_path", type=str, default=None,
                        help="Path to the terraformer executable")

    args = parser.parse_args()
    main(args)
