from typing import Tuple

import pygame
from tetris.button import Button
from tetris.colors import Colors


class TextBox(Button):
    def __init__(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: int,
        text: pygame.font,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        show: bool = True,
    ):
        super().__init__(
            starting_pixel, width, height, color, text, text_size, text_color, show
        )
        self.active = False


