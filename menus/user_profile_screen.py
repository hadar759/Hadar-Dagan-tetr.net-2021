import threading
from typing import Optional, Dict

import pygame

from database.server_communicator import ServerCommunicator
from menus.menu_screen import MenuScreen
from tetris.colors import Colors


class UserProfile(MenuScreen):
    BUTTON_PRESS = pygame.MOUSEBUTTONDOWN

    def __init__(
        self,
        user: Dict,
        wanted_profile: str,
        server_communicator: ServerCommunicator,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
        user_profile: Optional[dict] = None,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.user = user
        self.server_communicator = server_communicator
        if not user_profile:
            self.profile = self.server_communicator.get_user_profile(wanted_profile)
            self.wanted_profile = wanted_profile
        else:
            self.profile = user_profile

    def run(self):
        self.create_user_profile()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

        while self.running:
            self.run_once()

    def quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False
        self.server_communicator.update_online(self.user["username"], False)

    def create_user_profile(self):
        self.user = self.server_communicator.get_user_profile(self.user["username"])
        username = self.wanted_profile
        if username != self.user["username"]:
            user = self.server_communicator.get_user_profile(username)
        else:
            user = self.user
        print(user)
        print(f"you've entered {username}'s user profile")
        self.buttons = {}
        self.textboxes = {}
        name_width = 400
        name_height = 200
        cur_x = 0
        cur_y = 0
        self.name_button = self.create_button(
            (cur_x, cur_y),
            name_width,
            name_height,
            Colors.BLACK_BUTTON,
            username,
            80,
            clickable=False,
            text_only=True,
        )
        if username in self.user["friends"]:
            button_color = Colors.RED_BUTTON
            button_text = "Remove friend"
            button_font_size = 38

        elif username in self.user["requests_sent"]:
            # Make this grey
            button_color = Colors.BLACK_BUTTON
            button_text = "Unsend request"
            button_font_size = 37

        elif username in self.user["requests_received"]:
            button_color = Colors.GREEN_READY_BUTTON
            button_text = "Accept request"
            button_font_size = 35

        else:
            button_color = Colors.GREEN_BUTTON
            button_text = "Add friend"
            button_font_size = 47

        if user != self.user:
            btn = self.create_button(
                (cur_x + name_width + 200, cur_y + 60),
                name_width + 30,
                name_height - 100,
                button_color,
                button_text,
                button_font_size,
            )

            self.buttons.pop(btn)
            self.buttons[btn] = (
                self.friend_actions,
                (
                    btn,
                    username,
                ),
            )

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button(
            (self.width - function_button_width, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "->",
            55,
            Colors.WHITE,
            func=self.better_quit,
        )

        cur_y += name_height

        stat_width = 300
        stat_height = 100
        self.create_button(
            (cur_x, cur_y),
            stat_width,
            stat_height,
            Colors.BLACK_BUTTON,
            f"Games: {user['games']}",
            text_only=True,
        )

        cur_y += stat_height

        self.create_button(
            (cur_x - 10, cur_y),
            stat_width,
            stat_height,
            Colors.BLACK_BUTTON,
            f"Wins: {user['wins']}",
            text_only=True,
        )

        cur_y += stat_height

        self.create_button(
            (cur_x, cur_y),
            stat_width,
            stat_height,
            Colors.BLACK_BUTTON,
            f"apm: {user['apm']}",
            text_only=True,
        )

        cur_y += stat_height

        self.create_button(
            (cur_x, cur_y),
            stat_width,
            stat_height,
            Colors.BLACK_BUTTON,
            f"Marathon: {user['marathon']}",
            text_only=True,
        )

        cur_y = name_height
        cur_x = name_width * 2

        self.create_button(
            (cur_x, cur_y),
            stat_width,
            stat_height,
            Colors.BLACK_BUTTON,
            f"Sprint",
            text_color=Colors.DARK_YELLOW,
            text_only=True,
        )
        cur_y += stat_height

        lengths = ["20L", "40L", "100L", "1000L"]
        time_width = stat_width
        time_height = 75

        for index, entry in enumerate(user["sprint"]):
            if entry == "0":
                entry = "-"
            self.create_button(
                (cur_x, cur_y),
                time_width,
                time_height,
                Colors.BLACK_BUTTON,
                f"{lengths[index]}: {entry}",
                40,
                Colors.DARK_YELLOW,
                text_only=True,
            )
            cur_y += time_height

    def friend_actions(self, button, username):
        if button.text == "Add friend":
            # Make this grey
            button.color = Colors.BLACK_BUTTON

            button.text = "Request sent"
            button.text_size = 40
            button.rendered_text = button.render_button_text()

            func = self.server_communicator.send_friend_request
            args = (
                self.user["username"],
                username,
            )

        elif button.text == "Accept request":
            button.color = Colors.RED_BUTTON

            button.text = "Remove friend"
            button.text_size = 38
            button.rendered_text = button.render_button_text()

            func = self.server_communicator.accept_friend_request
            args = (
                username,
                self.user["username"],
            )

        else:
            button.color = Colors.GREEN_BUTTON

            button.text = "Add friend"
            button.text_size = 47
            button.rendered_text = button.render_button_text()
            button.color_button(self.screen)

            func = self.server_communicator.remove_friend
            args = (
                self.user["username"],
                username,
            )

        threading.Thread(target=func, args=args).start()
        self.display_buttons()
        pygame.display.flip()

    def better_quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False
        self.name_button = None

    def drawings(self):
        cur_x = 0
        cur_y = 0
        self.screen.fill(
            Colors.WHITE,
            (
                (cur_x + 5, cur_y + self.name_button.height - 50),
                (self.name_button.width + 115, 10),
            ),
        )

        cur_y = self.name_button.height
        cur_x = self.name_button.width * 2
        self.screen.fill(
            Colors.DARK_YELLOW,
            ((cur_x + 30, cur_y + self.name_button.height - 120), (240, 10)),
        )
