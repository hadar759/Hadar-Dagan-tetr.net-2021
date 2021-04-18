import math
from typing import Tuple, Dict

import pygame
from tetris.colors import Colors


class Button:
    def __init__(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: Dict,
        text: pygame.font,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        transparent: bool = False,
        text_only: bool = False,
        border_size: int = 10,
        clickable: bool = True,
    ):
        # The first pixel of the button
        self.starting_x = starting_pixel[0]
        self.starting_y = starting_pixel[1]
        # The button's size
        self.width = width
        self.height = height

        self.color = color
        self.text = text
        self.text_size = text_size
        self.text_color = text_color
        self.border_size = border_size
        self.transparent = transparent
        self.text_only = text_only
        self.clickable = clickable
        # The rendered text to display inside the button
        self.rendered_text = self.render_button_text()

    def inside_button(self, pixel: Tuple[int, int]):
        """Receives a coordinate and returns whether it's inside the button"""
        return (
            self.starting_x < pixel[0] < self.starting_x + self.width
            and self.starting_y < pixel[1] < self.starting_y + self.height
        )

    def render_button_text(
        self, inp: str = None, font_size: int = None, text_color: Tuple = None
    ):
        """Renders a text given it's font and size"""
        if not inp:
            inp = self.text
        if not font_size:
            font_size = self.text_size
        if not text_color:
            text_color = self.text_color

        split_text = inp.split("\n")
        lines = []
        if inp.isascii():
            for line in split_text:
                lines.append(
                    pygame.font.Font(
                        "./tetris-resources/joystix-monospace.ttf", font_size
                    ).render(line, True, text_color)
                )
            return lines
        else:
            for line in split_text:
                lines.append(
                    pygame.font.Font(
                        "./tetris-resources/seguisym.ttf", font_size
                    ).render(line, True, text_color)
                )
            return lines

    def calculate_center_text_position(
        self, x_space: int, y_space: int
    ) -> Tuple[int, int]:
        """Returns the center position the text should be in"""
        return max(0, x_space), max(0, y_space)

    def get_middle_text_position(self):
        """Returns the optimal position for the text"""
        num_of_lines = len(self.rendered_text)
        x_size = self.rendered_text[0].get_rect()[2]
        y_size = self.rendered_text[0].get_rect()[3]
        y_size = y_size if num_of_lines == 1 else y_size * 1.5
        return self.calculate_center_text_position(
            self.starting_x + self.width // 2 - x_size // 2,
            self.starting_y + self.height // 2 - (y_size * num_of_lines) // 2,
        )

    def get_left_text_position(self):
        return self.starting_x, self.starting_y

    def get_mid_left_text_position(self):
        return self.starting_x, max(
            0,
            self.starting_y
            + self.height // 2
            - self.rendered_text[0].get_rect()[3] // 2,
        )

    def button_action(self, screen, alpha: int = 15, reset: bool = True):
        # Do not show the button
        if self.transparent or not self.clickable:
            return
        button_color = self.color
        # Make the button brighter
        self.color = self.get_action_color(button_color, alpha)

        # Do not color the button in
        if not self.text_only:
            self.color_button(screen)
        self.show_text_in_button(screen)
        # Update the button
        pygame.display.flip()
        if reset:
            # Return the button to it's previous condition
            self.color = button_color

    def get_action_color(self, button_color, alpha):
        """Returns the button color if it were to be clicked"""
        return {
            key: tuple([min(255, val + alpha) for val in button_color[key]])
            for key in button_color
        }

    def show_text_in_button(self, screen):
        """Shows text inside the button"""
        x, y = self.get_middle_text_position()
        for line in self.rendered_text:
            screen.blit(line, (x, y))
            y += line.get_rect()[3] + line.get_rect()[3] // 2

    def color_button(self, screen):
        """Colors the button in on the screen"""
        # Fill in the main button
        screen.fill(
            self.color["button"],
            (
                (
                    self.starting_x + self.border_size,
                    self.starting_y + self.border_size,
                ),
                (self.width - self.border_size, self.height - self.border_size),
            ),
        )
        # Make it 3d
        for i in range(self.border_size):
            # Create the upper side
            screen.fill(
                self.color["upper"],
                ((self.starting_x + i, self.starting_y + i), (self.width - i * 2, 1)),
            )

            # Create the left and right sides
            screen.fill(
                self.color["side"],
                ((self.starting_x + i, self.starting_y + i), (1, self.height - i * 2)),
            )

            screen.fill(
                self.color["side"],
                (
                    (self.starting_x + self.width - i, self.starting_y + i),
                    (1, self.height - i * 2),
                ),
            )

            # Create the bottom
            screen.fill(
                self.color["bottom"],
                (
                    (self.starting_x + i, self.starting_y + self.height - i),
                    (self.width - i * 2, 1),
                ),
            )
