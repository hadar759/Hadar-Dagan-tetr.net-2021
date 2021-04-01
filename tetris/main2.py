import ctypes
import socket

from pymongo import MongoClient

from game_server import GameServer
from server_communicator import ServerCommunicator
from tetris.main_menu import MainMenu
from tetris.waiting_room import WaitingRoom
from tetris.welcome_screen import WelcomeScreen


def main():
    user32 = ctypes.windll.user32
    # Get the width and height of the screen
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    """sock = socket.socket()
    sock.connect(("172.21.192.1", 44444))
    # Start the main menu
    menu = WaitingRoom({"username": "hadar759"},
                       True, "Hadar759's room", sock, ServerCommunicator("10.100.102.17", "8000"),
                       width - 200, height - 100, 75, "resources/tetris_background.jpg"
                       )
    menu.run()"""

    menu = WelcomeScreen(
        width - 200, height - 100, 75, "resources/tetris_background.jpg"
    )
    menu.run()

    """user32 = ctypes.windll.user32
    # Get the width and height of the screen
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    menu = MainMenu(width - 200, height - 100, 75, "resources/tetris_background.jpg")
    menu.run()"""


if __name__ == "__main__":
    main()
