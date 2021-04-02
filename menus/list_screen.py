import threading
from typing import Dict, Optional

from database.server_communicator import ServerCommunicator
from .menu_screen import MenuScreen


class ListScreen(MenuScreen):

    def __init__(
            self,
            user: Dict,
            server_communicator: ServerCommunicator,
            entry_list,
            num_on_screen,
            width: int,
            height: int,
            refresh_rate: int = 60,
            background_path: Optional[str] = None,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.user = user
        self.server_communicator = server_communicator
        self.offset = 0
        self.entry_list = entry_list
        self.num_on_screen = num_on_screen

    def run(self):
        self.create_screen()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        while self.running:
            super().run()

    def create_screen(self):
        pass

    def display_entries(self, *args):
        pass

    def scroll_up(self, *args):
        if self.offset == 0:
            self.create_popup_button("Can't scroll up")
            return
        self.offset -= 1
        self.display_entries(*args)

    def scroll_down(self, *args):
        offset = self.offset
        self.offset = self.offset = min(
            max(0, len(self.entry_list) - self.num_on_screen), self.offset + 1
        )
        # Offset hasn't changed, i.e. we're at the end of the room list
        if offset == self.offset:
            self.create_popup_button("Can't scroll down more")
        else:
            self.display_entries(*args)

