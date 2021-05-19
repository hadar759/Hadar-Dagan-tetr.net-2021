import threading
from typing import Dict, Optional

import pygame.event

from database.server_communicator import ServerCommunicator
from .menu_screen import MenuScreen


class ListScreen(MenuScreen):
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
            width, height, server_communicator, refresh_rate, background_path
        )
        self.user = user
        self.offset = 0
        self.cache = cache
        self.entry_list = []
        self.num_on_screen = num_on_screen
        self.scroll_funcs = {-1: (self.scroll_down, ()), 1: (self.scroll_up, ())}

    def run(self):
        self.create_screen()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        while self.running:
            self.run_once(self.handle_events)

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL:
            try:
                scroll_func, args = self.scroll_funcs.get(event.y)
                # Last button isn't a scroll button
                scroll_func(*args)
            except Exception as e:
                print(e)
        super().handle_events(event)

    def create_screen(self):
        pass

    def display_entries(self, *args):
        pass

    def scroll_up(self, *args):
        if self.offset == 0:
            # Popup already present on screen
            if list(self.buttons.values())[-1][0] != self.buttons.popitem:
                self.create_popup_button("Can't scroll up")
            return
        self.offset -= 1
        if not args:
            self.create_screen()

    def scroll_down(self, *args):
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
            if not args:
                self.create_screen()
            else:
                self.display_entries(*args)
