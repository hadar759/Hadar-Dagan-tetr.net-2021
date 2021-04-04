import socket
import bcrypt
import threading
from typing import Optional

import pygame
from requests import get

from database.db_post_creator import DBPostCreator
from database.server_communicator import ServerCommunicator
from tetris.colors import Colors
from menus.main_menu import MainMenu
from menus.menu_screen import MenuScreen


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
        with open(r"../salt.txt", "r") as salt_file:
            self.salt = salt_file.read().encode()

    def run(self):
        """Main loop of the welcome screen"""
        # Set up the buttons and display them
        # Very specific numbers just so they exactly fill the blocks in the background pic hahaha

        # Login button
        self.create_button(
            (self.width // 2 - 258, self.height // 3 - 250),
            504,
            200,
            Colors.BLACK_BUTTON,
            "login",
            func=self.login,
        )

        # Register button
        self.create_button(
            (self.width // 2 - 258, self.height // 3 * 2 - 250),
            504,
            200,
            Colors.BLACK_BUTTON,
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

                    for button in reversed(self.buttons.keys()):
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
            Colors.WHITE_BUTTON,
            r"Username\Email",
            text_color=Colors.DARK_GREY,
        )

        # Password Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + button_height * 3),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Password",
            text_color=Colors.GREY,
            is_pass=True,
        )

        # Forgot your password button
        self.create_button(
            (mid_x_pos + button_width // 4, self.height // 2),
            button_width // 2,
            button_height // 2,
            Colors.BLACK_BUTTON,
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
            Colors.BLACK_BUTTON,
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

        password = bcrypt.hashpw(password.encode(), self.salt).hex()
        user = self.server_communicator.get_user(user_identifier, password)

        # Update the user's latest ip
        if user:
            self.running = False
            new_outer_ip = self.get_outer_ip()
            threading.Thread(
                target=self.server_communicator.on_connection,
                args=(
                    user["username"],
                    new_outer_ip,
                ),
                daemon=True,
            ).start()
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
            Colors.WHITE_BUTTON,
            r"Email",
            text_color=Colors.DARK_GREY,
        )

        # Username Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + round(button_height * 1.7)),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Username",
            text_color=Colors.GREY,
        )

        # Password Button
        self.create_textbox(
            (mid_x_pos, self.height // 10 + round(button_height * 1.7 * 2)),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Password",
            text_color=Colors.GREY,
            is_pass=True,
        )

        # Continue button
        self.create_button(
            (mid_x_pos + button_width // 4 - 5, self.height // 2 + button_height),
            button_width // 2,
            button_height,
            Colors.BLACK_BUTTON,
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

        if not self.is_email(email) or email == "":
            self.create_popup_button(r"Invalid Email")

        elif " " in username:
            self.create_popup_button("Invalid name")

        elif self.is_email(username):
            self.create_popup_button("Username can't contain @")

        elif password == "":
            self.create_popup_button("Please enter Password")

        elif username == "":
            self.create_popup_button("Please enter Username")

        # TODO CHANGE
        elif self.server_communicator.email_exists(email):
            self.reset_textboxes()
            self.create_popup_button("Email already exists")

        # TODO CHANGE
        elif self.server_communicator.username_exists(username):
            self.reset_textboxes()
            self.create_popup_button("Username already exists")

        # Add the valid user to the DB
        else:
            password = bcrypt.hashpw(password.encode(), self.salt).hex()
            print(password)
            user_number = self.server_communicator.estimated_document_count()
            user_post = DBPostCreator.create_user_post(
                user_number, email, username, password, self.get_outer_ip()
            )
            threading.Thread(
                target=self.server_communicator.create_user(user_post), daemon=True
            ).start()
            MainMenu(
                user_post,
                self.server_communicator,
                self.width,
                self.height,
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
