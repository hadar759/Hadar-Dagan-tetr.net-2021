from typing import Tuple

import pygame
from menus.button import Button
from tetris.colors import Colors


class TextBox(Button):
    def __init__(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: dict,
        text: pygame.font,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        transparent: bool = False,
        text_only: bool = False,
        is_pass: bool = False,
    ):
        super().__init__(
            starting_pixel,
            width,
            height,
            color,
            text,
            text_size,
            text_color,
            transparent,
            text_only,
        )
        self.text_cursor_ticks = pygame.time.get_ticks()
        self.active = False
        self.is_pass = is_pass

    def show_text_in_textbox(
        self,
        inputted_text: str,
        screen: pygame.Surface,
        offset: int,
        offset_change: bool = False,
    ):
        """Shows the fitting text in a textbox"""
        if self.is_pass and inputted_text != self.text:
            displayed_text = "•" * len(inputted_text)
        else:
            displayed_text = inputted_text
        if self.active:
            # User entered no input - only display a cursor and nothing more
            if inputted_text == self.text:
                displayed_text = self.add_text_cursor("", 0, offset_change)
            # Otherwise just add the cursor to the end of the user's input
            else:
                displayed_text = self.add_text_cursor(
                    displayed_text, offset, offset_change
                )

        # Textbox isn't active. Resets it in case we activated it and then left.
        elif inputted_text == "":
            return self.text

        self.rendered_text = self.render_button_text(
            displayed_text, self.text_size, self.text_color
        )
        screen.blit(self.rendered_text[0], self.get_middle_text_position())
        return inputted_text

    def add_text_cursor(self, text: str, offset: int, offset_change: bool):
        """Adds a blinking text cursor to the end of a text"""
        cur_ticks = pygame.time.get_ticks()
        ticks_between_blinks = 700

        # If less than 700 ticks passed display cursor
        if (
            not offset_change
            and cur_ticks - self.text_cursor_ticks < ticks_between_blinks
        ):
            text = self.add_cursor_to_text(text, offset)

        # If the offset changed or more than 1400 ticks passed, reset the count so the cursor will be displayed again
        elif (
            offset_change
            or cur_ticks - self.text_cursor_ticks > ticks_between_blinks * 2
        ):
            # In case the offset just changed, give 500 more ticks for the cursor to be displayed
            self.text_cursor_ticks = cur_ticks + offset_change * 500

        return text

    @staticmethod
    def add_cursor_to_text(text, offset):
        return text[:offset] + "|" + text[offset:]

    def switch_pass(self):
        self.is_pass = not self.is_pass
