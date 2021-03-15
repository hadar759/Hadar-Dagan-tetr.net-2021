import pickle
import socket
import threading
import time
from typing import Optional, Tuple, Dict

import pygame

from server_communicator import ServerCommunicator
from tetris.tetris_screen import TetrisScreen
from tetris.colors import Colors
from tetris.tetris_client import TetrisClient
from tetris.tetris_game import TetrisGame
from tetris.waiting_room import WaitingRoom


class MainMenu(TetrisScreen):
    """The starting screen of the game"""

    GAME_PORT = 44444
    BUTTON_PRESS = pygame.MOUSEBUTTONDOWN

    def __init__(
        self,
        user: Dict,
        server_communicator: ServerCommunicator,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
        skin: int = 1,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.buttons = {}
        self.user = user
        self.skin = skin
        self.text_cursor_ticks = pygame.time.get_ticks()
        self.server_communicator = server_communicator
        self.socket = socket.socket()

    def run(self):
        """Main loop of the main menu"""
        while True:
            self.create_menu()
            self.running = True
            old_time = round(time.time())
            threading.Thread(target=self.update_mouse_pos).start()

            while self.running:
                self.update_screen()

                for event in pygame.event.get():
                    # Different event, but mouse pos was initiated
                    if self.mouse_pos:
                        self.handle_events(event)

                # Display invites
                cur_time = round(time.time())
                if cur_time % 20 == 0 and cur_time != old_time:
                    old_time = cur_time
                    # threading.Thread(target=self.check_invite).start()
                    threading.Thread(target=self.check_invite).start()
                pygame.display.flip()

    def check_invite(self):
        invite = self.server_communicator.get_invite(self.user["username"]).replace(
            '"', ""
        )
        if invite:
            self.display_invite(invite)

    def display_invite(self, inviter_name):
        screen_corner_x = 1500
        screen_corner_y = 600
        button_height = 300
        button_width = 200
        self.create_button(
            (screen_corner_x - button_width, screen_corner_y - button_height),
            button_width,
            button_height,
            Colors.BLACK,
            inviter_name,
            func=self.accept_invite
        )

        x_height = 20
        x_width = 20
        self.create_button(
            (screen_corner_x, screen_corner_y - button_height),
            x_width,
            x_height,
            Colors.BLACK,
            "X",
            text_size=20,
            text_color=Colors.RED,
            func=self.dismiss_invite
        )

    def accept_invite(self):
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        room = {"name": "test private room", "ip": invite_ip}
        self.connect_to_room(room)

    def dismiss_invite(self):
        """Dismisses an invite from a player"""
        # TODO Do something with a declination
        inviter_name = self.server_communicator.get_invite(self.user["username"])
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        self.socket.send(pickle.dumps(["declined"]))
        buttons = {}
        print(inviter_name)
        for button in self.buttons:
            if button.text == "X":
                # Close the connection
                self.socket.close()
                self.socket = socket.socket()
                # Free the server
                self.server_communicator.finished_server(invite_ip)
                # Remove the invite from the DB
                self.server_communicator.dismiss_invite(self.user["username"])
                # Don't add the button to the new buttons array
                continue
            elif button.text == inviter_name:
                continue
            else:
                buttons[button] = self.buttons[button]
        self.buttons = buttons
        self.update_screen()

    def update_screen(self):
        """Displays everything needed to be displayed on the screen"""
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.display_textboxes()
        self.display_buttons()
        pygame.display.flip()

    def create_menu(self):
        """Creates the main menu screen and all it's components"""
        self.screen = pygame.display.set_mode((self.width, self.height))
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        # Set up the buttons and display them
        # Very specific numbers just so they exactly fill the blocks in the background pic hahaha
        cur_button_text = "sprint"
        self.create_button(
            (self.width // 2 - 258, self.height // 3 - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
            func=self.sprint
        )

        cur_button_text = "marathon"
        self.create_button(
            (self.width // 2 - 258, self.height // 3 * 2 - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
            func=self.marathon
        )

        cur_button_text = "multiplayer"
        self.create_button(
            (self.width // 2 - 258, self.height - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
            func=self.multiplayer
        )

        cur_button_text = self.user["username"]
        self.create_button(
            (self.width - 300, self.height // 3 - 250),
            250,
            100,
            Colors.BLACK,
            cur_button_text,
            func=self.user_profile
        )

        self.display_buttons()

    def handle_events(self, event: pygame.event):
        """Responds to pygame events"""
        if event.type == pygame.QUIT:
            self.quit()
            pygame.quit()
            exit()

        # If the user typed something
        if event.type == pygame.KEYDOWN:
            for textbox in self.textboxes.keys():
                if textbox.active:
                    self.textbox_key_actions(textbox, event)
                    break

        # In case the user pressed the mouse button
        if event.type == self.BUTTON_PRESS:
            for button in self.buttons:
                # Check if the click is inside the button area (i.e. the button was clicked)
                # Otherwise skip
                if not button.inside_button(self.mouse_pos):
                    continue
                # Change the button color
                button.clicked(self.screen)
                # Get the correct response using to the button
                func, args = self.buttons[button]
                # User pressed a button with no response function
                if not func:
                    continue
                func(*args)
                break

            for textbox in self.textboxes.keys():
                # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                if textbox.inside_button(self.mouse_pos):
                    # Make the textbox writeable
                    textbox.active = True
                else:
                    textbox.active = False

    def quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False
        self.server_communicator.update_online(self.user["username"], False)

    def user_profile(self):
        print(f"you've entered {self.user['username']}'s user profile")

    def create_room_list(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 300
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK, "ROOM LIST", 70,
                           Colors.PURPLE, text_only=True)

        function_button_width = 75
        function_button_height = 75
        # Create the add room button
        self.create_button((cur_x, cur_y), function_button_width, function_button_height, Colors.BLACK, "+", 70,
                           Colors.WHITE, func=self.create_room)
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height, Colors.BLACK, "->", 55,
                           Colors.WHITE, func=self.quit)

        cur_y += title_height - function_button_height - 10

        # Create the scroll up button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK, "↑", 55, Colors.WHITE, func=self.scroll_up)

        # Create the scroll down button
        self.create_button((self.width - function_button_width, self.height - function_button_height), function_button_width,
                           function_button_height,
                           Colors.BLACK, "↓", 55, Colors.WHITE, func=self.scroll_down)

        cur_y += function_button_height + 10

        room_button_width = self.width
        room_button_height = 200
        player_button_width = 50
        player_button_height = 200
        for room in self.server_communicator.get_rooms():
            self.create_button((cur_x, cur_y), room_button_width, room_button_height, Colors.BLACK,
                               " ".join(list(room["name"])), text_color=Colors.WHITE, func=self.connect_to_room, args=(room,))
            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = last_button.get_mid_left_text_position
            self.create_button((cur_x + room_button_width - player_button_width - 20, cur_y), player_button_width, player_button_height,
                               Colors.BLACK, str(room["player_num"]), text_size=70, text_color=Colors.WHITE, text_only=True)
            cur_y += room_button_height + 10

    def scroll_up(self):
        print("You've tried to scroll up!")

    def scroll_down(self):
        print("You've tried to scroll down!")

    def create_room(self):
        print("You've tried to create a room!")

    def connect_to_room(self, room: Dict):
        sock = socket.socket()
        sock.connect((room["ip"], 44444))
        # Start the main menu
        waiting_room = WaitingRoom(self.user,
                           False, room["name"], sock, self.server_communicator,
                           self.width, self.height, 75, "resources/tetris_background.jpg"
                           )
        waiting_room.run()

    def multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        # TODO Get the rooms array from the database or something and call create_room_button on every room
        #  or whatever
        self.create_button(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE,
            "Room List",
            text_color=Colors.GREY,
            func=self.create_room_list
        )

        cur_button_text = "Challenge"
        self.display_buttons()
        self.display_textboxes()
        pygame.display.flip()

    def display_rooms(self):
        rooms = self.server_communicator.get_rooms()

    def old_multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.create_textbox(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE,
            "Opponent Name",
            text_color=Colors.GREY,
        )

        cur_button_text = "Challenge"
        self.create_button(
            (self.width // 2 - 250, (self.height // 3) * 2),
            500,
            200,
            Colors.BLACK,
            cur_button_text,
#            func=self.multiplayer_continue
        )
        self.display_buttons()
        self.display_textboxes()
        pygame.display.flip()

    def sprint(self):
        """Create the sprint screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.create_button(
            (self.width // 2 - 257, self.height // 8 - 85),
            501,
            200,
            Colors.BLACK,
            "20L",
            func=self.start_game,
            args=("sprint", 20)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 3 - 81),
            501,
            200,
            Colors.BLACK,
            "40L",
            func=self.start_game,
            args=("sprint", 40)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 5 - 86),
            501,
            200,
            Colors.BLACK,
            "100L",
            func=self.start_game,
            args=("sprint", 100)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 7 - 85),
            501,
            200,
            Colors.BLACK,
            "1000L",
            func=self.start_game,
            args=("sprint", 1000)
        )
        self.display_buttons()
        pygame.display.flip()

    def marathon(self):
        """Create the marathon screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        button_height = 200
        button_width = 200
        row_height = self.height // 2 - button_height
        row_starting_width = self.width // 10
        # First line of buttons
        for i in range(5):
            self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.BLACK,
                str(i),
                func=self.start_game,
                args=("marathon", i)
            )
        # Second line of buttons
        row_height = row_height + button_height + 100
        for i in range(5):
            self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.BLACK,
                str(i + 5),
                func=self.start_game,
                args=("marathon", i + 5)
            )
        self.display_buttons()
        pygame.display.flip()

    def start_game(self, mode, lines_or_level):
        """Start a generic game, given a mode and the optional starting lines or starting level"""
        self.running = False
        self.buttons = {}
        self.reset_textboxes()
        game = TetrisGame(500 + 200, 1000, mode, self.server_communicator, self.user["username"], 75, lines_or_level=int(lines_or_level))
        game.run()
