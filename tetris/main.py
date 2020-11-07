import ctypes

from pymongo import MongoClient

from tetris.welcome_screen import WelcomeScreen


def main():
    cluster = MongoClient(
        "mongodb+srv://hadar759:noamhadar!25@tetr-net.kcot4.mongodb.net/<dbname>?retryWrites=true&w=majority"
    )
    db = cluster["tetris"]
    collection = db["users"]

    user32 = ctypes.windll.user32
    # Get the width and height of the screen
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    # Start the main menu
    menu = WelcomeScreen(
        width - 200, height - 100, collection, 75, "resources/tetris_background.jpg"
    )
    menu.run()


if __name__ == "__main__":
    main()
