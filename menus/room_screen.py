import socket
import threading
import time
from typing import Dict, Optional

import pygame

from game_server import GameServer
from database.server_communicator import ServerCommunicator
from .waiting_room import WaitingRoom
from .list_screen import ListScreen
from tetris.colors import Colors


class RoomsScreen(ListScreen):
    def __init__(
        self,
        user: Dict,
        server_communicator: ServerCommunicator,
        cache,
        num_on_screen,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
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
        self.entry_list = cache["rooms"]

    def create_screen(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 300
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button(
            (cur_x, cur_y),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "ROOM LIST",
            70,
            Colors.PURPLE,
            text_only=True,
        )

        # Display the number of currently running rooms
        self.create_button(
            (cur_x, cur_y + 100),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            f"Num of rooms: {len(self.entry_list)}",
            40,
            Colors.WHITE,
            text_only=True,
        )

        function_button_width = 75
        function_button_height = 75
        # Create the add room button
        self.create_button(
            (cur_x, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "+",
            70,
            Colors.WHITE,
            func=self.create_room,
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

        self.create_button(
            (cur_x, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "⟳",
            70,
            Colors.WHITE,
            func=self.refresh_rooms,
        )

        cur_y += function_button_height + 10

        self.buttons[scroll_up_btn] = (self.buttons[scroll_up_btn][0], (cur_x, cur_y))
        self.buttons[scroll_down_btn] = (
            self.buttons[scroll_down_btn][0],
            (cur_x, cur_y),
        )

        self.display_entries(cur_x, cur_y)

    def refresh_rooms(self):
        self.offset = 0
        self.cache["rooms"] = self.server_communicator.get_rooms()
        self.entry_list = self.cache["rooms"]
        self.loading = False
        self.create_screen()

    def display_entries(self, cur_x, cur_y):
        room_button_width = self.width
        room_button_height = 190
        player_button_width = 50
        player_button_height = 200
        self.offset = min(
            max(0, len(self.entry_list) - self.num_on_screen), self.offset
        )
        for room in self.entry_list[self.offset : self.offset + self.num_on_screen]:
            self.create_button(
                (cur_x, cur_y),
                room_button_width,
                room_button_height,
                Colors.BLACK_BUTTON,
                " ".join(list(room["name"])),
                text_color=Colors.WHITE,
                func=self.connect_to_room,
                args=(room,),
            )
            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = (
                last_button.get_mid_left_text_position
            )
            self.create_button(
                (cur_x + room_button_width - player_button_width - 20, cur_y),
                player_button_width,
                player_button_height,
                Colors.BLACK_BUTTON,
                str(room["player_num"]),
                text_size=70,
                text_color=Colors.WHITE,
                text_only=True,
            )
            cur_y += room_button_height + 10

    def create_room(self):
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0

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
            func=self.quit,
        )

        # Create the screen title
        self.create_button(
            (cur_x, cur_y),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "CREATE A ROOM",
            70,
            Colors.PURPLE,
            text_only=True,
        )
        cur_y += title_height

        textbox_width = 1000
        label_width = 300
        textbox_height = 130
        cur_x = 100
        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "Room name:",
            text_only=True,
        )
        name_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[name_box] = f"{self.user['username']}'s room"
        cur_y += textbox_height + 20

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "Min apm:",
            text_only=True,
        )
        name_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[name_box] = "0"
        cur_y += textbox_height + 20

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "Max apm:",
            text_only=True,
        )
        name_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[name_box] = "999"
        cur_y += textbox_height + 20

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "Private:",
            text_only=True,
        )
        button = self.create_button(
            (cur_x + label_width + 100, cur_y + 40),
            50,
            50,
            Colors.BLACK_BUTTON,
            "❌",
            45,
            Colors.RED,
        )
        self.buttons[button] = (self.change_binary_button, (button,))
        cur_y += textbox_height + 20

        continue_width = label_width + 200
        self.create_button(
            (self.width // 2 - label_width // 2, cur_y),
            continue_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "CONTINUE",
            text_color=Colors.WHITE,
            func=self.create_continue,
        )

    def create_continue(self):
        textbox_values = list(self.textboxes.values())
        room_name = textbox_values[0]
        if len(room_name) > 23:
            self.textboxes = {}
            self.buttons = {}
            self.create_room()
            self.create_popup_button("Room name too long")
            return
        min_apm = textbox_values[1]
        max_apm = textbox_values[2]
        private = not list(self.buttons.keys())[-2].text == "❌"
        if not min_apm or not max_apm or not min_apm.isdigit() or not max_apm.isdigit():
            self.textboxes = {}
            self.buttons = {}
            self.create_room()
            self.create_popup_button("Invalid settings")
            return
        min_apm = int(min_apm)
        max_apm = int(max_apm)
        pygame.mixer.pause()
        self.running = False
        room_server = GameServer(
            self.get_outer_ip(),
            self.get_inner_ip(),
            False,
            room_name,
            min_apm,
            max_apm,
            private,
            self.user["username"],
        )
        pygame.mixer.unpause()
        threading.Thread(target=room_server.run).start()
        self.connect_to_room(
            {
                "outer_ip": room_server.outer_ip,
                "inner_ip": room_server.inner_ip,
                "name": room_server.room_name,
                "default": False,
            }
        )
        self.running = True

    def connect_to_room(self, room: Dict):
        sock = socket.socket()
        port = 44444
        sock.connect((room["outer_ip"] if room["default"] else room["inner_ip"], port))
        # Start the main menu
        waiting_room = WaitingRoom(
            self.user,
            False,
            room["name"],
            self.cache,
            sock,
            self.server_communicator,
            self.width,
            self.height,
            75,
            "tetris/tetris-resources/tetris_background.jpg",
        )
        self.running = False
        waiting_room.run()
        self.running = True
        self.cache = waiting_room.cache
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        self.create_screen()
