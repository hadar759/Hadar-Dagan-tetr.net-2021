"""
Hadar Dagan
31.5.2020
v1.0
"""
from typing import Tuple

import pygame
from colors import Colors


class Button:
    def __init__(self, starting_pixel: Tuple[int, int], width: int, height: int, color: int, text: pygame.font):
        # The first pixel of the button
        self.starting_x = starting_pixel[0]
        self.starting_y = starting_pixel[1]
        # The button's size
        self.width = width
        self.height = height

        self.color = color
        self.text = text
        # The rendered text to display inside the button
        self.rendered_text = self.render_input(45, text, Colors.WHITE)

    def inside_button(self, pixel: Tuple[int, int]):
        """Receives a coordinate and returns whether it's inside the button"""
        return (self.starting_x < pixel[0] < self.starting_x + self.width
                and self.starting_y < pixel[1] < self.starting_y + self.height)

    def render_input(self, font_size: int, inp: str, color):
        """Renders a text given it's font and size"""
        return pygame.font.Font("./resources/joystix-monospace.ttf", font_size).render(
            inp,
            True,
            color)

    def calculate_center_text_position(self, x_space: int, y_space: int) -> Tuple[int, int]:
        """Returns the center position the text should be in"""
        return max(0, x_space), max(0, y_space)

    def get_text_position(self):
        """Returns the optimal position for the text"""
        return self.calculate_center_text_position(
            self.starting_x + self.width // 2 - self.rendered_text.get_rect()[2] // 2,
            self.starting_y + self.height // 2 - self.rendered_text.get_rect()[3] // 2)