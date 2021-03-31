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
        text_color: Tuple[int, int, int] = Colors.WHITE_BUTTON,
        transparent: bool = False,
        text_only: bool = False,
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
        self.transparent = transparent
        self.text_only = text_only
        # The rendered text to display inside the button
        self.rendered_text = self.render_button_text()

    def inside_button(self, pixel: Tuple[int, int]):
        """Receives a coordinate and returns whether it's inside the button"""
        return (
            self.starting_x < pixel[0] < self.starting_x + self.width
            and self.starting_y < pixel[1] < self.starting_y + self.height
        )

    def render_button_text(self, inp: str = None, font_size: int = None, text_color: Tuple = None):
        """Renders a text given it's font and size"""
        if not inp:
            inp = self.text
        if not font_size:
            font_size = self.text_size
        if not text_color:
            text_color = self.text_color
        if inp.isascii():
            return pygame.font.Font("./resources/joystix-monospace.ttf", font_size).render(
                inp, True, text_color
            )
        else:
            return pygame.font.Font("./resources/seguisym.ttf", font_size).render(
                inp, True, text_color
            )

    def calculate_center_text_position(
        self, x_space: int, y_space: int
    ) -> Tuple[int, int]:
        """Returns the center position the text should be in"""
        return max(0, x_space), max(0, y_space)

    def get_middle_text_position(self):
        """Returns the optimal position for the text"""
        return self.calculate_center_text_position(
            self.starting_x + self.width // 2 - self.rendered_text.get_rect()[2] // 2,
            self.starting_y + self.height // 2 - self.rendered_text.get_rect()[3] // 2,
        )

    def get_left_text_position(self):
        return self.starting_x, self.starting_y

    def get_mid_left_text_position(self):
        return self.starting_x, max(0, self.starting_y + self.height // 2 - self.rendered_text.get_rect()[3] // 2)

    def clicked(self, screen):
        # Do not show the button
        if self.transparent:
            return
        button_color = self.color
        # Make the button brighter
        self.color = self.get_clicked_color(button_color)

        # Do not color the button in
        if not self.text_only:
            self.color_button(screen)
        self.show_text_in_button(screen)
        # Update the button
        pygame.display.flip()
        # Return the button to it's previous condition
        self.color = button_color

    def get_clicked_color(self, button_color):
        """Returns the button color if it were to be clicked"""
        return {key: tuple([min(255, val + 15) for val in button_color[key]]) for key in button_color}

    def show_text_in_button(self, screen):
        """Shows text inside the button"""
        screen.blit(self.rendered_text, self.get_middle_text_position())

    def color_button(self, screen):
        """Colors the button in on the screen"""
        border_size = 10
        # Fill in the main button
        screen.fill(self.color["button"], ((self.starting_x + border_size, self.starting_y + border_size),
                                           (self.width - border_size, self.height - border_size)))
        # Make it 3d
        for i in range(border_size):
            # Create the upper side
            screen.fill(
                self.color["upper"],
                ((self.starting_x + i, self.starting_y + i),
                 (self.width - i * 2, 1))
            )

            # Create the left and right sides
            screen.fill(
                self.color["side"],
                ((self.starting_x + i, self.starting_y + i),
                 (1, self.height - i * 2))
            )

            screen.fill(
                self.color["side"],
                ((self.starting_x + self.width - i, self.starting_y + i),
                 (1, self.height - i * 2))
            )

            # Create the bottom
            screen.fill(
                self.color["bottom"],
                ((self.starting_x + i, self.starting_y + self.height - i),
                 (self.width - i * 2, 1))
            )