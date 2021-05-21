import socket
import threading
from typing import Dict, Optional

from room_server import RoomServer
from database.server_communicator import ServerCommunicator
from .user_profile_screen import UserProfile
from .waiting_room import WaitingRoom
from .list_screen import ListScreen
from tetris.colors import Colors


class FriendsScreen(ListScreen):
    def __init__(
        self,
        user: Dict,
        server_communicator: ServerCommunicator,
        cache,
        num_on_screen,
        type: str,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        # TODO fix the problem with scrolling
        super().__init__(
            user,
            server_communicator,
            cache,
            num_on_screen,
            width,
            height,
            refresh_rate,
            background_path,
        )
        self.type = type
        self.entry_list = user[type]

    def create_screen(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 300
        cur_x = 0
        cur_y = 0
        if "friends" in self.type:
            title_text = self.type.upper()
        else:
            title_text = f"FRIEND {self.type.replace('_', ' ').upper()}"
        # Create the screen title
        self.create_button(
            (cur_x, cur_y + 10),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            title_text,
            70,
            Colors.GREEN,
            text_only=True,
        )

        # Display the number of currently running rooms
        self.create_button(
            (cur_x, cur_y + 100),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            f"Num of {self.type.split('_')[0]}: {len(self.entry_list)}",
            40,
            Colors.WHITE,
            text_only=True,
        )

        # TODO CREATE A TEXTBOX TO THE LEFT OF IT, WHERE YOU CAN SEND FRIEND REQUESTS

        box_width = 300
        box_height = 100
        self.create_textbox(
            (cur_x, cur_y + 10),
            box_width,
            box_height,
            Colors.WHITE_BUTTON,
            "Player name",
            30,
            Colors.BLACK,
        )

        if "friends" not in self.type:
            if self.type.split("_")[-1] == "received":
                btn_text = "Sent"
            else:
                btn_text = "Received"

            self.create_button(
                (self.width - box_width - 100, cur_y + 10),
                box_width,
                box_height,
                Colors.BLACK_BUTTON,
                btn_text,
                40,
                Colors.GREEN,
                func=self.switch_type,
                args=(btn_text.lower(),),
            )

        function_button_width = 75
        function_button_height = 75
        # Create the add room button
        self.create_button(
            (cur_x + box_width + 5, cur_y + (box_height + 10 - 50) // 2),
            50,
            50,
            Colors.GREEN_READY_BUTTON,
            "+",
            55,
            Colors.WHITE,
            func=self.add_friend,
        )
        # Create the back button
        self.create_button(
            (self.width - function_button_width, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "->",
            55,
            Colors.WHITE,
            func=self.quit,
        )

        cur_y += title_height - function_button_height - 10

        # Create the scroll up button
        scroll_up_btn = self.create_button(
            (self.width - function_button_width, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "↑",
            55,
            Colors.WHITE,
            func=self.scroll_up,
        )

        # Create the scroll down button
        scroll_down_btn = self.create_button(
            (self.width - function_button_width, self.height - function_button_height),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "↓",
            55,
            Colors.WHITE,
            func=self.scroll_down,
        )

        cur_y += 10

        if self.type != "requests_sent":
            self.create_button(
                (cur_x, cur_y),
                function_button_width,
                function_button_height,
                Colors.BLACK_BUTTON,
                "⟳",
                70,
                Colors.WHITE,
                func=self.refresh_list,
            )

        cur_y += function_button_height + 10

        self.buttons[scroll_up_btn] = (self.buttons[scroll_up_btn][0], (cur_x, cur_y))
        self.buttons[scroll_down_btn] = (
            self.buttons[scroll_down_btn][0],
            (cur_x, cur_y),
        )

        self.display_entries(cur_x, cur_y)

    def switch_type(self, type):
        self.type = f"requests_{type}"
        self.entry_list = self.user[self.type]
        self.create_screen()

    def add_friend(self):
        friend_name = list(self.textboxes.values())[0]

        # Entered invalid foe name
        if friend_name == self.user[
            "username"
        ] or not self.server_communicator.username_exists(friend_name):
            self.create_popup_button(r"Invalid Username Entered")

        elif friend_name in self.user["friends"]:
            self.create_popup_button("Already friends")

        elif friend_name in self.user["requests_sent"]:
            self.create_popup_button("Request already sent")

        else:
            threading.Thread(
                target=self.server_communicator.send_friend_request,
                args=(
                    self.user["username"],
                    friend_name,
                ),
            ).start()
            self.user["requests_sent"].append(friend_name)
            self.cache["user"] = self.user
            print("add friend")
            print(self.cache)
            print(self.user)
            self.create_screen()

        self.textboxes[(list(self.textboxes.keys()))[0]] = ""

    def refresh_list(self):
        self.offset = 0
        self.user = self.server_communicator.get_user_profile(self.user["username"])
        self.cache["user"] = self.user
        self.entry_list = self.user[self.type]
        self.loading = False
        self.create_screen()

    def display_entries(self, cur_x, cur_y):
        user_button_width = self.width // 4 - 50
        user_button_height = 100
        self.offset = min(
            max(0, len(self.entry_list) - self.num_on_screen), self.offset
        )
        for index, friend in enumerate(
            self.entry_list[self.offset : self.offset + self.num_on_screen]
        ):
            self.create_button(
                (cur_x, cur_y),
                user_button_width,
                user_button_height,
                Colors.GREEN_READY_BUTTON,
                friend,
                text_color=Colors.WHITE,
                func=self.user_profile,
                args=(friend,),
            )
            last_button = list(self.buttons.keys())[-1]
            # A row was finished
            if index != 0 and index % 4 == 0:
                cur_x = 0
                cur_y += user_button_height + 10
            else:
                cur_x += user_button_width + 10

    def user_profile(self, username):
        profile = UserProfile(
            self.cache["user"],
            username,
            self.server_communicator,
            self.width,
            self.height,
            self.refresh_rate,
            self.background_path,
            user_profile=self.cache.get(username),
        )
        self.running = False
        profile.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        self.cache[username] = profile.profile
        self.cache["user"] = profile.user
        print(profile.user)
        self.create_screen()

    def change_binary_button(self, button):
        if button.text == "❌":
            button.text_color = Colors.GREEN
            button.text = "✔"
        elif button.text == "✔":
            button.text_color = Colors.RED
            button.text = "❌"
        button.rendered_text = button.render_button_text()
