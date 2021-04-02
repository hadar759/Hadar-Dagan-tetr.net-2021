import pickle
import socket
import threading
import time
from typing import Optional, Dict

import pygame

from database.server_communicator import ServerCommunicator
from menus.friend_screen import FriendsScreen
from menus.leaderboard_screen import LeaderboardScreen
from menus.menu_screen import MenuScreen
from menus.waiting_room import WaitingRoom
from tetris.colors import Colors
from menus.room_screen import RoomScreen
from tetris.tetris_game import TetrisGame
from menus.user_profile_screen import UserProfile


class MainMenu(MenuScreen):
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
            threading.Thread(target=self.update_mouse_pos, daemon=True).start()

            while self.running:
                super().run()

                # Display invites
                cur_time = round(time.time())
                if cur_time % 20 == 0 and cur_time != old_time:
                    old_time = cur_time
                    # threading.Thread(target=self.check_invite).start()
                    threading.Thread(target=self.check_invite, daemon=True).start()
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
            Colors.BLACK_BUTTON,
            inviter_name,
            func=self.accept_invite,
        )

        x_height = 20
        x_width = 20
        self.create_button(
            (screen_corner_x, screen_corner_y - button_height),
            x_width,
            x_height,
            Colors.BLACK_BUTTON,
            "X",
            text_size=20,
            text_color=Colors.RED,
            func=self.dismiss_invite,
        )

    def accept_invite(self):
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        room = {"name": "test private room", "ip": invite_ip}
        self.connect_to_room(room)

    def connect_to_room(self, room: Dict):
        self.running = False
        sock = socket.socket()
        sock.connect((room["ip"], 44444))
        # Start the main menu
        waiting_room = WaitingRoom(
            self.user,
            False,
            room["name"],
            sock,
            self.server_communicator,
            self.width,
            self.height,
            75,
            "../tetris/resources/tetris_background.jpg",
        )
        waiting_room.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

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

    def create_menu(self):
        """Creates the main menu screen and all it's components"""
        self.screen = pygame.display.set_mode((self.width, self.height))
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        # Set up the buttons and display them
        button_width = 504
        button_height = 150
        cur_x = self.width // 2 - 258
        cur_y = self.height // 4 - button_height
        button_offset = button_height + 75
        cur_button_text = "sprint"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.YELLOW_BUTTON,
            cur_button_text,
            func=self.sprint,
        )
        cur_y += button_offset

        cur_button_text = "marathon"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.DEEP_BLUE_BUTTON,
            cur_button_text,
            func=self.marathon,
        )
        cur_y += button_offset

        cur_button_text = "multiplayer"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.PINKISH_BUTTON,
            cur_button_text,
            func=self.create_room_list,
        )
        cur_y += button_offset

        cur_button_text = "leaderboard"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.create_leaderboard,
        )

        name_width = 350
        name_height = 100
        cur_button_text = self.user["username"]
        name_font_size = 45
        if len(cur_button_text) > 7:
            name_font_size -= (len(cur_button_text) - 7) * 3 + 1

        self.create_button(
            (self.width - name_width - 5, self.height // 3 - 250),
            name_width,
            name_height,
            Colors.BLACK_BUTTON,
            cur_button_text,
            name_font_size,
            func=self.user_profile,
            args=(self.user["username"],),
        )

        bruh_width = name_width // 7
        self.create_button(
            (self.width - name_width - bruh_width - 10, self.height // 3 - 250),
            bruh_width,
            name_height,
            Colors.BLACK_BUTTON,
            "✉",
            func=self.friends_screen,
            args=("friends",)
        )

        self.create_button(
            (self.width - name_width - bruh_width * 2 - 20, self.height // 3 - 250),
            bruh_width,
            name_height,
            Colors.BLACK_BUTTON,
            "♟",
            func=self.friends_screen,
            args=("requests_sent",)
        )

        self.display_buttons()

    def friends_screen(self, type):
        self.running = False
        friends_screen = FriendsScreen(self.user, self.server_communicator, self.user[type], 12, type,
                                       self.width, self.height, self.refresh_rate, self.background_path)
        friends_screen.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

    def quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False
        self.server_communicator.update_online(self.user["username"], False)

    def create_leaderboard(self):
        self.running = False
        leaderboard = LeaderboardScreen(self.user, self.server_communicator, [], 4, self.width, self.height, self.refresh_rate,
                                        self.background_path)
        leaderboard.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

    def user_profile(self, username):
        self.running = False
        profile = UserProfile(self.user, username, self.server_communicator, self.width, self.height, self.refresh_rate,
                              self.background_path)
        profile.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

    def create_room_list(self):
        self.running = False
        room_screen = RoomScreen(self.user, self.server_communicator, self.server_communicator.get_rooms(), 3,
                                 self.width, self.height, self.refresh_rate,
                                 self.background_path)
        room_screen.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

    def multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        self.create_button(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE_BUTTON,
            "Room List",
            text_color=Colors.GREY,
            func=self.create_room_list,
        )

        self.display_buttons()
        self.display_textboxes()
        pygame.display.flip()

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
            Colors.WHITE_BUTTON,
            "Opponent Name",
            text_color=Colors.GREY,
        )

        cur_button_text = "Challenge"
        self.create_button(
            (self.width // 2 - 250, (self.height // 3) * 2),
            500,
            200,
            Colors.BLACK_BUTTON,
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

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button(
            (self.width - function_button_width, 0),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "->",
            55,
            Colors.WHITE,
            func=self.quit,
        )

        self.create_button(
            (self.width // 2 - 257, self.height // 8 - 85),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "20L",
            func=self.start_game,
            args=("sprint", 20),
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 3 - 81),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "40L",
            func=self.start_game,
            args=("sprint", 40),
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 5 - 86),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "100L",
            func=self.start_game,
            args=("sprint", 100),
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 7 - 85),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "1000L",
            func=self.start_game,
            args=("sprint", 1000),
        )
        self.display_buttons()
        pygame.display.flip()

    def marathon(self):
        """Create the marathon screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button(
            (self.width - function_button_width, 0),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "->",
            55,
            Colors.WHITE,
            func=self.quit,
        )

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button(
            (cur_x, cur_y),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "CHOOSE A STARTING LEVEL",
            70,
            Colors.WHITE,
            text_only=True,
        )

        button_height = 200
        button_width = 200
        row_height = self.height // 2 - button_height
        row_starting_width = self.width // 10
        # First line of buttons
        for i in range(5):
            btn = self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.DEEP_BLUE_BUTTON,
                str(i),
                func=self.start_game,
                args=("marathon", i),
            )
            if i % 2 == 0:
                btn.color = btn.get_clicked_color(btn.color)
        # Second line of buttons
        row_height = row_height + button_height + 100
        for i in range(5):
            btn = self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.DEEP_BLUE_BUTTON,
                str(i + 5),
                func=self.start_game,
                args=("marathon", i + 5),
            )
            if i % 2 == 1:
                btn.color = btn.get_clicked_color(btn.color)

        self.display_buttons()
        pygame.display.flip()

    def start_game(self, mode, lines_or_level):
        """Start a generic game, given a mode and the optional starting lines or starting level"""
        self.running = False
        self.buttons = {}
        self.reset_textboxes()
        game = TetrisGame(
            500 + 200,
            1000,
            mode,
            self.server_communicator,
            self.user["username"],
            75,
            lines_or_level=int(lines_or_level),
        )
        game.run()
