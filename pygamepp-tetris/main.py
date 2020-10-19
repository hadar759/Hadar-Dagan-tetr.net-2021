import ctypes

from .main_menu import *


def main():
    user32 = ctypes.windll.user32
    # Get the width and height of the screen
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    # Start the main menu
    menu = MainMenu(width - 200, height - 100, 75, "./resources/tetris_background.jpg")
    menu.run()


if __name__ == "__main__":
    main()
