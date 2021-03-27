import threading
import time
from typing import Optional, Tuple, Dict

import pygame
import socket

from tetris.menu_screen import MenuScreen
from tetris.main_menu import MainMenu
from tetris.button import Button
from tetris.colors import Colors
from tetris.text_box import TextBox
from requests import get
from server_communicator import ServerCommunicator


class WelcomeScreen(MenuScreen):
    """The starting screen of the game"""

    def __init__(
        self,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.server_communicator = ServerCommunicator("127.0.0.1", "8000")

    def run(self):
        """Main loop of the welcome screen"""
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
            func=self.register_screen,
        )

        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

        while self.running:
            self.update_screen()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.running = False
                    quit()

                if not self.mouse_pos:
                    continue

                # In case the user pressed the mouse button
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for textbox in self.textboxes.keys():
                        # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                        if textbox.inside_button(self.mouse_pos):
                            # Make the textbox writeable
                            textbox.active = True
                        else:
                            textbox.active = False

                    for button in self.buttons.keys():
                        # Check if the click is inside the button area (i.e. whether the button was clicked)
                        if button.inside_button(self.mouse_pos):
                            button.clicked(self.screen)
                            # Execute the function which the button controls
                            self.buttons[button][0]()
                            break

                # If the user typed something
                if event.type == pygame.KEYDOWN:
                    for textbox in self.textboxes.keys():
                        if textbox.active:
                            self.textbox_key_actions(textbox, event)
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
            True,
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

        if user_identifier == "":
            self.create_popup_button(r"Please enter Username\Email")
            valid_user = False

        if password == "":
            self.create_popup_button(r"Please enter a Password")
            valid_user = False

        if not valid_user:
            return

        user = self.server_communicator.get_user(user_identifier, password)

        # Update the user's latest ip
        if user:
            self.running = False
            new_outer_ip = self.get_outer_ip()
            threading.Thread(target=self.server_communicator.on_connection, args=(user["username"], new_outer_ip,), daemon=True).start()
            MainMenu(
                user,
                self.server_communicator,
                self.width,
                self.height,
                self.refresh_rate,
                self.background_path,
            ).run()
            pygame.quit()
            self.running = True
        else:
            self.reset_textboxes()
            self.create_popup_button("Invalid credentials")

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

    def register_screen(self):
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
            threading.Thread(target=self.server_communicator.create_user(user_post), daemon=True).start()
            MainMenu(
                user_post,
                self.server_communicator,
                self.width,
                self.height,
                self.refresh_rate,
                self.background_path
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
            "type": "user",
            "email": email,
            "username": username,
            "password": password,
            "ip": ip,
            "invite": "",
            "invite_ip": "",
            "online": True,
            "40l": "0",
            "marathon": 0,
            "apm_games": [],
            "apm": 0.0,
            "wins": 0,
            "games": 0
        }
