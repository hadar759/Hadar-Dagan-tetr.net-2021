import ctypes
from menus.welcome_screen import WelcomeScreen


class Main:
    @staticmethod
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
                           width - 200, height - 100, 75, "tetris-resources/tetris_background.jpg"
                           )
        menu.run()"""
        try:
            menu = WelcomeScreen(
                width - 200,
                height - 100,
                75,
                "tetris/tetris-resources/tetris_background.jpg",
            )
            menu.run()
        except Exception as e:
            print(e)
            quit()

        """menu = MainMenu({"username": "hadar759"}, ServerCommunicator("127.0.0.1", "8000"), width - 200, height - 100, 75, "tetris-resources/tetris_background.jpg")
        menu.run()"""


if __name__ == "__main__":
    Main.main()
