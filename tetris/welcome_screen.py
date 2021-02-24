import json
from typing import Optional, Tuple, Dict, List

import pygame
import socket
import pymongo
from pymongo.collection import Collection
from pymongo import MongoClient
from tetris.main_menu import MainMenu
from tetris.button import Button
from tetris.colors import Colors
from tetris.text_box import TextBox
from requests import get, post
from server_communicator import ServerCommunicator


class WelcomeScreen:
    """The starting screen of the game"""

    def __init__(
        self,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        self.width, self.height = width, height
        self.refresh_rate = refresh_rate
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background_image = (
            pygame.image.load(background_path) if background_path else None
        )
        self.background_path = background_path
        self.buttons: Dict[Button, callable] = {}
        self.textboxes: Dict[TextBox, str] = {}

        self.text_cursor_ticks = pygame.time.get_ticks()
        self.server_communicator = ServerCommunicator("127.0.0.1", "8000")

    def run(self):
        """Main loop of the main menu"""
        # Set up the buttons and display them
        # Very specific numbers just so they exactly fill the blocks in the background pic hahaha

        # Login button
        self.create_button(
            (self.width // 2 - 258, self.height // 3 - 250),
            504,
            200,
            Colors.BLACK,
            "login",
            func=self.login,
        )

        # Register button
        self.create_button(
            (self.width // 2 - 258, self.height // 3 * 2 - 250),
            504,
            200,
            Colors.BLACK,
            "register",
            func=self.register,
        )

        run = True

        while run:
            self.update_screen()
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                # In case the user pressed the mouse button
                if event.type == pygame.MOUSEBUTTONDOWN:

                    for textbox in self.textboxes.keys():
                        # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                        if textbox.inside_button(mouse_pos):
                            # Make the textbox writeable
                            textbox.active = True
                        else:
                            textbox.active = False

                    for button in self.buttons.keys():
                        # Check if the click is inside the button area (i.e. whether the button was clicked)
                        if button.inside_button(mouse_pos):
                            self.buttons[button]()
                            break

                # If the user typed something
                if event.type == pygame.KEYDOWN:
                    for textbox in self.textboxes.keys():
                        if textbox.active:
                            self.key_actions(textbox, event)
                            break

    def login(self):
        """Create the login screen - set up the correct buttons"""
        self.buttons = {}
        self.screen.blit(self.background_image, (0, 0))

        button_width = self.width // 2
        button_height = self.height // 10
        # Place the button in the middle of the screen
        mid_x_pos = self.width // 2 - (button_width // 2)

        # Username\Email Button
        self.create_textbox(
            (mid_x_pos, self.height // 5),
            button_width,
            button_height,
            Colors.WHITE,
            r"Username\Email",
            text_color=Colors.DARK_GREY,
        )

        # Password Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + button_height * 3),
            button_width,
            button_height,
            Colors.WHITE,
            "Password",
            text_color=Colors.GREY,
        )

        # Forgot your password button
        self.create_button(
            (mid_x_pos + button_width // 4, self.height // 2),
            button_width // 2,
            button_height // 2,
            Colors.BLACK,
            "Forgot your password?",
            18,
            Colors.BLUE,
            False,
        )

        # Continue button
        self.create_button(
            (mid_x_pos + button_width // 4 - 5, self.height // 2 + button_height),
            button_width // 2,
            button_height,
            Colors.BLACK,
            "CONTINUE",
            text_color=Colors.WHITE,
            func=self.login_continue,
        )

        self.update_screen()

    def login_continue(self):
        """Process the login info given"""
        user_inputs = tuple(self.textboxes.values())
        user_identifier = user_inputs[0]
        password = user_inputs[1]
        valid_user = True

        self.reset_textboxes()

        if user_identifier == "":
            self.create_popup_button(r"Please enter Username\Email")
            valid_user = False

        if password == "":
            self.create_popup_button(r"Please enter a Password")
            valid_user = False

        if not valid_user:
            return

        # TODO CHANGE
        user_exists = self.server_communicator.user_identifier_exists(user_identifier)

        # Given user doesn't exist in the database
        if not user_exists:
            self.create_popup_button(r"Username\Email doesn't exist")

        else:
            user = self.server_communicator.get_user(user_identifier, password)
            # Update the user's latest ip
            if user:
                new_outer_ip = self.get_outer_ip()
                self.server_communicator.update_outer_ip(
                    user_identifier, password, new_outer_ip
                )
                self.server_communicator.update_online(user_identifier, True)
                MainMenu(
                    self.width,
                    self.height,
                    user,
                    self.server_communicator,
                    self.refresh_rate,
                    self.background_path,
                ).run()
                pygame.quit()

            # User exists but the password doesn't match
            else:
                self.create_popup_button(r"Wrong Password")

    def create_popup_button(self, text):
        button_width = self.width // 2
        button_height = self.height // 3
        # Place the button in the middle of the screen
        mid_x_pos = self.width // 2 - (button_width // 2)

        self.create_button(
            (mid_x_pos, self.height // 2 - button_height),
            button_width,
            button_height,
            Colors.BLACK,
            text,
            38,
            text_color=Colors.RED,
            func=self.buttons.popitem,
        )

    @staticmethod
    def is_email(inp: str):
        """Returns whether a given string is an email address"""
        return "@" in inp

    def register(self):
        """Create the register screen - set up the correct buttons"""
        self.buttons = {}
        self.screen.blit(self.background_image, (0, 0))

        button_width = self.width // 2
        button_height = self.height // 10
        mid_x_pos = self.width // 2 - (button_width // 2)

        # Email Button
        self.create_textbox(
            (mid_x_pos, self.height // 10),
            button_width,
            button_height,
            Colors.WHITE,
            r"Email",
            text_color=Colors.DARK_GREY,
        )

        # Username Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + button_height * 1.7),
            button_width,
            button_height,
            Colors.WHITE,
            "Username",
            text_color=Colors.GREY,
        )

        # Password Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + button_height * 1.7 * 2),
            button_width,
            button_height,
            Colors.WHITE,
            "Password",
            text_color=Colors.GREY,
        )

        # Continue button
        self.create_button(
            (mid_x_pos + button_width // 4 - 5, self.height // 2 + button_height),
            button_width // 2,
            button_height,
            Colors.BLACK,
            "CONTINUE",
            text_color=Colors.WHITE,
            func=self.register_continue,
        )

        self.update_screen()

    def register_continue(self):
        user_inputs = tuple(self.textboxes.values())
        email = user_inputs[0]
        username = user_inputs[1]
        password = user_inputs[2]
        valid_user = True

        if not self.is_email(email) or email == "":
            self.create_popup_button(r"Invalid Email")
            valid_user = False

        if self.is_email(username):
            self.create_popup_button("Username can't contain @")
            valid_user = False

        if password == "":
            self.create_popup_button("Please enter Password")
            valid_user = False

        if username == "":
            self.create_popup_button("Please enter Username")
            valid_user = False

        # TODO CHANGE
        if self.server_communicator.email_exists(email):
            self.reset_textboxes()
            self.create_popup_button("Email already exists")
            valid_user = False

        # TODO CHANGE
        elif self.server_communicator.username_exists(username):
            self.reset_textboxes()
            self.create_popup_button("Username already exists")
            valid_user = False

        # Add the valid user to the DB
        if valid_user:
            user_number = self.server_communicator.estimated_document_count()
            user_post = self.create_db_post(
                user_number, email, username, password, self.get_outer_ip()
            )
            self.server_communicator.create_user(user_post)
            MainMenu(
                self.width,
                self.height,
                user_post,
                self.server_communicator,
                self.refresh_rate,
                self.background_path,
            ).run()
            pygame.quit()

    @staticmethod
    def get_outer_ip():
        return get("https://api.ipify.org").text

    @staticmethod
    def get_local_ip():
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    @staticmethod
    def create_db_post(
        user_number: int, email: str, username: str, password: str, ip: str
    ) -> dict:
        """Returns a db post with the given parameters"""
        return {
            "_id": user_number,
            "email": email,
            "username": username,
            "password": password,
            "ip": ip,
            "invite": "",
            "invite_ip": "",
            "online": True,
        }

    def create_button(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: int,
        text: str,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        show: bool = True,
        func: callable = lambda: None,
    ):
        """Creates a new button and appends it to the button dict"""
        self.buttons[
            Button(
                starting_pixel, width, height, color, text, text_size, text_color, show
            )
        ] = func

    def create_textbox(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: int,
        text: str,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        show: bool = True,
    ):
        """Creates a new textbox and appends it to the textbox dict"""
        self.textboxes[
            TextBox(
                starting_pixel,
                width,
                height,
                color,
                text,
                text_size,
                text_color,
                show,
            )
        ] = ""

    def key_actions(self, textbox: TextBox, event: pygame.event.EventType):
        textbox_text = self.textboxes[textbox]

        # BACKSPACE/DELETE
        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
            # We haven't entered any text
            if textbox_text == textbox.text:
                return
            # Last letter
            if len(textbox_text) <= 1:
                self.textboxes[textbox] = textbox.text
            # Just regular deleting
            else:
                self.textboxes[textbox] = textbox_text[:-1]

        # ENTER
        elif event.key == 13 or event.key == pygame.K_TAB:
            # Move to the next textbox
            self.textboxes[textbox] = self.textboxes[textbox].rstrip()
            textbox.active = False
            next_textbox = self.get_next_in_dict(self.textboxes, textbox)
            try:
                next_textbox.active = True
            # In case there aren't any more textboxes
            except AttributeError:
                pass

        # TEXT
        else:
            if self.textboxes[textbox] == textbox.text:
                self.textboxes[textbox] = ""
            self.textboxes[textbox] += event.unicode

    def display_buttons(self):
        """Display all buttons on the screen"""
        for button in self.buttons.keys():
            if button.show:
                x = button.starting_x
                y = button.starting_y
                self.screen.fill(button.color, ((x, y), (button.width, button.height)))
                self.show_text_in_button(button)

    @staticmethod
    def get_next_in_dict(dict: Dict, given_key):
        key_index = -999

        for index, key in enumerate(dict.keys()):
            if key == given_key:
                key_index = index

            if index == key_index + 1:
                return key

    def display_textboxes(self):
        """Display all buttons on the screen"""
        for textbox in self.textboxes.keys():
            if textbox.show:
                x = textbox.starting_x
                y = textbox.starting_y
                self.screen.fill(
                    textbox.color, ((x, y), (textbox.width, textbox.height))
                )
                self.show_text_in_textbox(textbox)

    def show_text_in_buttons(self):
        """Display the button's text for each of the buttons we have"""
        for button in self.buttons.keys():
            self.screen.blit(button.rendered_text, button.get_text_position())

    def show_text_in_button(self, button):
        self.screen.blit(button.rendered_text, button.get_text_position())

    def show_text_in_textbox(self, textbox):
        """Shows the fitting text in a textbox"""
        inputted_text = self.textboxes[textbox]

        if textbox.active:
            # User entered no input - only display a cursor and nothing more
            if inputted_text == textbox.text:
                inputted_text = self.add_text_cursor("")
            # Otherwise just add the cursor to the end of the user's input
            else:
                inputted_text = self.add_text_cursor(inputted_text)

        # Textbox isn't active. Resets it in case we activated it and then left.
        elif inputted_text == "|" or inputted_text == "":
            self.textboxes[textbox] = textbox.text

        textbox.rendered_text = textbox.render_input(
            textbox.text_size, inputted_text, textbox.text_color
        )
        self.screen.blit(textbox.rendered_text, textbox.get_text_position())

    def add_text_cursor(self, text):
        """Adds a blinking text cursor to the end of a text"""
        cur_ticks = pygame.time.get_ticks()
        ticks_between_blinks = 700

        # If less than 700 ticks passed display cursor
        if cur_ticks - self.text_cursor_ticks < ticks_between_blinks:
            text += "|"

        # If more than 1400 ticks passed, reset the count so the cursor will be displayed again
        elif cur_ticks - self.text_cursor_ticks > ticks_between_blinks * 2:
            self.text_cursor_ticks = cur_ticks

        return text

    def reset_textboxes(self):
        for textbox in self.textboxes:
            self.textboxes[textbox] = ""
            textbox.rendered_text = textbox.render_input(
                textbox.text_size, textbox.text, textbox.text_color
            )

    def update_screen(self):
        """Displays everything needed to be displayed on the screen"""
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.display_textboxes()
        self.display_buttons()
        pygame.display.flip()
