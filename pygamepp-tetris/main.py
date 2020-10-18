"""
Hadar Dagan
31.5.2020
v1.0
"""
import ctypes

import main_menu


def main():
    user32 = ctypes.windll.user32
    # Get the width and height of the screen
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    # Start the main menu
    menu = main_menu.MainMenu(width - 200, height - 100, 75, "./resources/tetris_background.jpg")
    menu.run()


if __name__ == "__main__":
    main()
