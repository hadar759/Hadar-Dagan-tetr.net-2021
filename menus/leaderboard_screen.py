import threading
from typing import Dict, Optional

from database.server_communicator import ServerCommunicator
from .list_screen import ListScreen
from tetris.colors import Colors
from menus.user_profile_screen import UserProfile


class LeaderboardScreen(ListScreen):
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

    def create_screen(self):
        self.buttons = {}
        self.textboxes = {}
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
            "LEADERBOARD",
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

        cur_y += title_height

        button_width = 504
        button_height = 200
        cur_x = self.width // 2 - 258
        button_offset = button_height + 75
        cur_button_text = "sprint"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard_menu,
        )
        cur_y += button_offset

        cur_button_text = "marathon"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.marathon_leaderboard,
        )
        cur_y += button_offset

        cur_button_text = "apm"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.apm_leaderboard,
        )

    def quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False

    def sprint_leaderboard(self, line_num):
        self.entry_list = self.cache[f"{line_num}l_leaderboard"]
        self.display_leaderboard(str(line_num) + "l")

    def marathon_leaderboard(self):
        self.entry_list = self.cache["marathon_leaderboard"]
        self.display_leaderboard("marathon")

    def apm_leaderboard(self):
        self.entry_list = self.cache["apm_leaderboard"]
        self.display_leaderboard("apm")

    def sprint_leaderboard_menu(self):
        self.buttons = {}
        self.textboxes = {}
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
            "SPRINT LEADERBOARD",
            70,
            Colors.PURPLE,
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

        cur_y += title_height - 15

        button_width = 504
        button_height = 150
        cur_x = self.width // 2 - 258
        button_offset = button_height + 60
        cur_button_text = "20l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(20,),
        )
        cur_y += button_offset

        cur_button_text = "40l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(40,),
        )
        cur_y += button_offset

        cur_button_text = "100l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(100,),
        )
        cur_y += button_offset

        cur_button_text = "1000l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(1000,),
        )

    def display_leaderboard(self, score_type):
        self.buttons = {}
        self.textboxes = {}
        self.scroll_funcs[-1] = (self.scroll_down, (score_type,))
        self.scroll_funcs[1] = (self.scroll_up, (score_type,))
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
            f"{score_type.upper()} LEADERBOARD",
            70,
            Colors.PURPLE,
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

        cur_y += title_height - function_button_height - 10

        # Create the scroll up button
        self.create_button(
            (self.width - function_button_width, cur_y),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "↑",
            55,
            Colors.WHITE,
            func=self.scroll_up,
            args=(score_type,),
        )

        # Create the scroll down button
        self.create_button(
            (self.width - function_button_width, self.height - function_button_height),
            function_button_width,
            function_button_height,
            Colors.BLACK_BUTTON,
            "↓",
            55,
            Colors.WHITE,
            func=self.scroll_down,
            args=(score_type,),
        )

        self.display_entries(cur_x, cur_y, score_type)

    def display_entries(self, cur_x, cur_y, score_type):
        entry_width = self.width
        entry_height = 169
        score_width = 50
        score_height = 190
        position_width = 150
        cur_y += 80
        self.offset = min(
            max(0, len(self.entry_list) - self.num_on_screen), self.offset
        )
        for index, user in enumerate(
            self.entry_list[self.offset : self.offset + self.num_on_screen]
        ):
            self.create_button(
                (cur_x, cur_y),
                position_width,
                entry_height,
                Colors.BLACK_BUTTON,
                f"{index + self.offset + 1}.",
                text_size=50,
                text_color=Colors.WHITE,
            )

            self.create_button(
                (cur_x + position_width, cur_y),
                entry_width,
                entry_height,
                Colors.BLACK_BUTTON,
                " " + user["username"],
                text_size=50,
                text_color=Colors.GREEN,
                func=self.user_profile,
                args=(user["username"],),
            )

            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = (
                last_button.get_mid_left_text_position
            )
            self.create_button(
                (cur_x + entry_width - score_width * 7, cur_y - 8),
                score_width,
                score_height,
                Colors.BLACK_BUTTON,
                str(user[score_type]),
                text_size=70,
                text_color=Colors.RED,
                text_only=True,
            )
            cur_y += entry_height + 10

    def user_profile(self, username):
        profile = UserProfile(
            self.user,
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
        self.cache["user"] = profile.user
        self.cache[username] = profile.profile
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

    def scroll_up(self, score_type):
        if self.offset == 0:
            # Popup already present on screen
            if list(self.buttons.values())[-1][0] != self.buttons.popitem:
                self.create_popup_button("Can't scroll up")
            return
        self.offset -= 1
        self.display_leaderboard(score_type)

    def scroll_down(self, score_type):
        offset = self.offset
        self.offset = self.offset = min(
            max(0, len(self.entry_list) - self.num_on_screen), self.offset + 1
        )
        # Offset hasn't changed, i.e. we're at the end of the room list
        if offset == self.offset:
            # Popup already present on screen
            if list(self.buttons.values())[-1][0] != self.buttons.popitem:
                self.create_popup_button("Can't scroll down more")
        else:
            self.display_leaderboard(score_type)
