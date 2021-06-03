import threading
from typing import Dict, Optional

import pygame

from database.server_communicator import ServerCommunicator
from menus.button import Button
from menus.menu_screen import MenuScreen
from tetris import Colors


class ControlsScreen(MenuScreen):
    SKIN_SETS = [
        pygame.image.load(rf"tetris/tetris-resources/skin_set{i}.png")
        for i in range(11)
    ]

    def __init__(
        self,
        server_communicator: ServerCommunicator,
        cache: Dict,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        super().__init__(
            width, height, server_communicator, refresh_rate, background_path
        )
        self.cache = cache
        self.controls = self.cache["user"]["controls"]
        self.bind_control = ""

    def run(self):
        self.create_screen()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        while self.running:
            self.run_once()

    def handle_events(self, event):
        super().handle_events(event)
        if event.type == pygame.KEYDOWN and self.bind_control:
            self.controls[self.bind_control] = event.key
            self.cache["user"]["controls"] = self.controls
            self.bind_control = ""
            self.create_screen()

    def create_screen(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 250
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button(
            (cur_x, cur_y - 30),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "CONTROLS",
            70,
            Colors.WHITE,
            text_only=True,
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
            func=self.quit,
        )

        cur_y += title_height - 50

        textbox_width = 400
        label_width = 300
        textbox_height = 130
        cur_x = self.width // 2 - round(label_width * 3)

        for index, key in enumerate(self.controls):
            if key == "flip_ccw":
                continue

            self.create_button(
                (cur_x + round(1.5 * label_width) * (index % 2 != 0), cur_y),
                label_width,
                textbox_height,
                Colors.BLACK_BUTTON,
                key.replace("_", " "),
                text_only=True,
            )
            key_button = self.create_button(
                (
                    cur_x
                    + label_width
                    + 100
                    + round(1.5 * label_width) * (index % 2 != 0),
                    cur_y,
                ),
                textbox_width,
                textbox_height,
                Colors.BLACK_BUTTON,
                pygame.key.name(self.controls[key]),
            )
            self.buttons[key_button] = (self.bind_button, (key_button,))

            if index % 2 != 0:
                cur_y += textbox_height + 30
                cur_x -= round(label_width * 1.3)

            else:
                cur_x += round(label_width * 1.3)

        key = "flip_ccw"

        self.create_button(
            (cur_x + label_width + 140, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            key.replace("_", " "),
            text_only=True,
        )

        key_button = self.create_button(
            (
                cur_x + label_width + 240 + label_width,
                cur_y,
            ),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            pygame.key.name(self.controls[key]),
        )
        self.buttons[key_button] = (self.bind_button, (key_button,))

        cur_y += textbox_height + 30

        continue_width = label_width + 200
        self.create_button(
            (self.width // 2 - label_width * 3 // 4, cur_y),
            continue_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "SAVE",
            text_color=Colors.WHITE,
            func=self.save_controls,
        )

    def bind_button(self, button: Button):
        self.create_popup_button(f"Press a button to bind to {button.text}")
        self.bind_control = list(self.controls.keys())[
            list(self.controls.values()).index(pygame.key.key_code(button.text))
        ]

    def save_controls(self):
        threading.Thread(
            target=self.server_communicator.update_controls,
            args=(self.cache["user"]["username"], self.controls),
        ).start()
        self.quit()
