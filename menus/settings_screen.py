import threading
from typing import Dict, Optional

from database.server_communicator import ServerCommunicator
from menus.menu_screen import MenuScreen
from tetris import Colors


class SettingsScreen(MenuScreen):
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

    def run(self):
        self.create_screen()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        while self.running:
            self.run_once()

    def create_screen(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}
        user = self.cache["user"]

        title_width = self.width
        title_height = 250
        cur_x = 0
        cur_y = 0
        # TODO design and create the settings screen
        # Create the screen title
        self.create_button(
            (cur_x, cur_y - 30),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "SETTINGS",
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

        textbox_width = 200
        label_width = 300
        textbox_height = 130
        cur_x = self.width // 2 - round(label_width * 1.5)

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "SKIN",
            text_only=True,
        )
        field_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[field_box] = str(user["skin"])
        cur_y += textbox_height + 30

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "DAS:",
            text_only=True,
        )
        field_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[field_box] = str(user["DAS"])
        cur_y += textbox_height + 30

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "ARR:",
            text_only=True,
        )
        field_box = self.create_textbox(
            (cur_x + label_width + 100, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "",
        )
        self.textboxes[field_box] = str(user["ARR"] // 10)
        cur_y += textbox_height + 30

        self.create_button(
            (cur_x, cur_y),
            label_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "Ghost:",
            text_only=True,
        )
        button = self.create_button(
            (cur_x + label_width + 150, cur_y + 40),
            50,
            50,
            Colors.BLACK_BUTTON,
            "✔",
            45,
            Colors.GREEN,
        )
        self.buttons[button] = (self.change_binary_button, (button,))
        cur_y += textbox_height + 30

        continue_width = label_width + 200
        self.create_button(
            (self.width // 2 - label_width * 3 // 4, cur_y),
            continue_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "SAVE",
            text_color=Colors.WHITE,
            func=self.save_settings,
        )

    def save_settings(self):
        skin = list(self.textboxes.values())[0]
        das_speed = list(self.textboxes.values())[1]
        arr_speed = list(self.textboxes.values())[2]
        ghost = not list(self.buttons.keys())[-2].text == "❌"
        invalid = False
        popups = []
        if not das_speed.isdigit() or not arr_speed.isdigit() or not skin.isdigit():
            self.create_screen()
            self.create_popup_button("ARR, DAS and skin values should be numeric")
            return
        if not 0 < int(das_speed) < 999:
            invalid = True
            popups.append("DAS value should be between 0 and 999")
        if not 0 < int(arr_speed) < 10:
            invalid = True
            popups.append("ARR value should be between 0 and 10")
        if not 0 <= int(skin) < 10:
            invalid = True
            popups.append("Please enter valid skin number")
        if not invalid:
            # Change the settings
            user = self.cache["user"]
            user["DAS"] = int(das_speed)
            user["ARR"] = int(arr_speed) * 10
            user["skin"] = int(skin)
            user["ghost"] = ghost
            # Update the cache
            self.cache["user"] = user
            # Update the server
            threading.Thread(
                target=self.server_communicator.update_settings,
                args=(
                    user["username"],
                    int(das_speed),
                    int(arr_speed) * 10,
                    int(skin),
                    ghost,
                ),
            ).start()
            self.quit()
            return
        # In case some entries weren't valid and we haven't quit
        self.create_screen()
        # Display all relevant popups on the screen
        for popup in popups:
            self.create_popup_button(popup)
