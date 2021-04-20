import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import random
import re
import socket
import time

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

    BACKGROUND_MUSIC = {"theme": pygame.mixer.Sound("sounds/05. Results.mp3")}
    for sound in BACKGROUND_MUSIC.values():
        sound.set_volume(0.05)

    def __init__(
        self,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        super().__init__(
            width,
            height,
            # ServerCommunicator("127.0.0.1", "8000"),
            ServerCommunicator("tetr-net.loca.lt", "80"),
            refresh_rate,
            background_path,
        )
        with open(r"resources/salt.txt", "r") as salt_file:
            self.salt = salt_file.read().encode()

    def run(self):
        """Main loop of the welcome screen"""
        # Play background music
        self.BACKGROUND_MUSIC["theme"].play(10)
        # Sync music with screen lol
        time.sleep(1)
        # Display the welcome screen
        self.create_first_screen()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()

        while self.running:
            self.run_once()

    def create_first_screen(self):
        """Create the first screen of the game"""
        self.buttons = {}
        self.textboxes = {}
        # TODO create a "WELCOME TO TETR.NET" with the project's symbol above it or something
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

    def create_return_button(self, func):
        ret_width = 75
        ret_height = 75
        self.create_button(
            (self.width - ret_width, 0),
            ret_width,
            ret_height,
            Colors.BLACK_BUTTON,
            "->",
            func=func,
        )

    def login(self):
        """Create the login screen - set up the correct buttons"""
        self.buttons = {}
        self.textboxes = {}
        self.screen.blit(self.background_image, (0, 0))

        button_width = self.width // 2
        button_height = self.height // 10
        # Place the button in the middle of the screen
        mid_x_pos = self.width // 2 - (button_width // 2)

        self.create_return_button(self.create_first_screen)

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

        self.create_button(
            (
                mid_x_pos + button_width // 4 - 5,
                self.height // 2 + button_height // 2 - 20,
            ),
            button_width // 2,
            button_height // 2,
            Colors.BLACK_BUTTON,
            "Forgot my password",
            text_color=Colors.RED,
            func=self.forgot_my_password,
            text_only=False,
            text_size=25,
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

    def forgot_my_password(self):
        """Prompt the user to enter their email, to which the password will be reset"""
        self.buttons = {}
        self.textboxes = {}

        self.create_return_button(self.login)

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button(
            (cur_x + 10, cur_y),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "Reset password",
            70,
            Colors.WHITE,
            text_only=True,
        )
        cur_y += title_height * 2
        cur_x = self.width // 2

        button_width = self.width // 2
        button_height = 100
        self.create_textbox(
            (cur_x - button_width // 2, cur_y - button_height),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Email",
            text_color=Colors.BLACK,
        )
        cur_y += button_height + 50

        self.create_button(
            (cur_x - button_width // 4, cur_y - button_height),
            button_width // 2,
            button_height * 2,
            Colors.BLACK_BUTTON,
            "Continue",
            func=self.check_reset_email,
        )

    def check_reset_email(self):
        """Checks whether the given email for reset is correct"""
        user_email = list(self.textboxes.values())[0]
        valid_email = self.is_email(user_email)
        if not valid_email or not self.server_communicator.email_exists(user_email):
            box_text = "Email"
            if not valid_email:
                self.create_popup_button("Email not valid")
            else:
                self.create_popup_button("User doesn't exist")

        else:
            box_text = "Reset Code"
            self.buttons[list(self.buttons.keys())[-1]] = self.check_code, (
                user_email,
                self.reset_password,
                (user_email,),
            )
            self.server_communicator.reset_password(user_email)

        # Reset the textbox
        self.textboxes = {key: "" for key in self.textboxes}
        for box in self.textboxes:
            box.text = box_text
            box.rendered_text = box.render_button_text()

    def check_code(self, user_email, func, args):
        """Checks whether the entered code is valid and proceeds accordingly"""
        code: str = list(self.textboxes.values())[0]
        if not code.isdigit():
            self.textboxes = {key: "" for key in self.textboxes}
            self.create_popup_button("Enter valid code")

        elif self.server_communicator.check_code(user_email, code):
            func(*args)

        else:
            self.create_popup_button(r"Wrong code\More than 15 minutes passed")

    def reset_password(self, user_email):
        """Prompt the user to enter the password to reset to"""
        self.buttons = {}
        self.textboxes = {}

        self.create_return_button(self.login)

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button(
            (cur_x + 10, cur_y),
            title_width,
            title_height,
            Colors.BLACK_BUTTON,
            "Reset password",
            70,
            Colors.WHITE,
            text_only=True,
        )
        cur_y += title_height * 1.8
        cur_x = self.width // 2

        button_width = self.width // 2
        button_height = 100
        self.create_textbox(
            (cur_x - button_width // 2, cur_y - button_height),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Password",
            is_pass=True,
            text_color=Colors.BLACK,
        )
        cur_y += button_height + 100

        self.create_textbox(
            (cur_x - button_width // 2, cur_y - button_height),
            button_width,
            button_height,
            Colors.WHITE_BUTTON,
            "Reenter password",
            is_pass=True,
            text_color=Colors.BLACK,
        )
        cur_y += button_height + 100

        self.create_button(
            (cur_x - button_width // 4, cur_y - button_height),
            button_width // 2,
            button_height * 2,
            Colors.BLACK_BUTTON,
            "Continue",
            func=self.reset_password_continue,
            args=(user_email,),
        )

    def reset_password_continue(self, user_email):
        """Receive the password from the user and updates it"""
        textbox_values = list(self.textboxes.values())
        password = textbox_values[0]
        re_password = textbox_values[1]

        if password != re_password:
            self.reset_password(user_email)
            self.create_popup_button("Passwords do not match")

        elif not self.server_communicator.is_password_new(
            user_email, bcrypt.hashpw(password.encode(), self.salt).hex()
        ):
            self.reset_password(user_email)
            self.create_popup_button(
                "Must use a different password then the current one"
            )

        else:
            # Encrypt the password
            password = bcrypt.hashpw(password.encode(), self.salt).hex()
            self.server_communicator.update_password(user_email, password)
            self.login()
            self.create_popup_button("Password successfully updated", color=Colors.BLUE)

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

        # Encrypt the password and get the user dict from the server
        password = bcrypt.hashpw(password.encode(), self.salt).hex()
        user = self.server_communicator.get_user(user_identifier, password)

        # Update the user's latest ip
        if user:
            new_outer_ip = self.get_outer_ip()
            # Update routine user stats (online, ip etc...)
            threading.Thread(
                target=self.server_communicator.on_connection,
                args=(
                    user["username"],
                    new_outer_ip,
                ),
                daemon=True,
            ).start()
            # Cache stats
            cache = self.cache_stats(user["username"])
            # Close the welcome screen
            self.running = False
            # Stop all music
            for sound in self.BACKGROUND_MUSIC.values():
                sound.stop()
            MainMenu(
                cache["user"],
                cache,
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
        regex = r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$"
        return re.search(regex, inp) is not None

    def register_screen(self):
        """Create the register screen - set up the correct buttons"""
        self.buttons = {}
        self.textboxes = {}
        self.screen.blit(self.background_image, (0, 0))

        self.create_return_button(self.create_first_screen)

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
            self.server_communicator.user_create_code(email)

            self.buttons = {}
            self.textboxes = {}

            self.create_return_button(self.register_screen)

            title_width = self.width
            title_height = 200
            cur_x = 0
            cur_y = 0
            # Create the screen title
            self.create_button(
                (cur_x + 10, cur_y),
                title_width,
                title_height,
                Colors.BLACK_BUTTON,
                "Verify User",
                70,
                Colors.WHITE,
                text_only=True,
            )
            cur_y += title_height * 2
            cur_x = self.width // 2

            button_width = self.width // 2
            button_height = 100
            self.create_textbox(
                (cur_x - button_width // 2, cur_y - button_height),
                button_width,
                button_height,
                Colors.WHITE_BUTTON,
                "Code",
                text_color=Colors.BLACK,
            )
            cur_y += button_height + 50

            self.create_button(
                (cur_x - button_width // 4, cur_y - button_height),
                button_width // 2,
                button_height * 2,
                Colors.BLACK_BUTTON,
                "Create user",
                func=self.check_code,
                args=(email, self.create_user, (email, username, password)),
            )

    def create_user(self, email, username, password):
        """Creates a new user from their credentials and signs them into the system"""
        # Encrypt the password and setup the user dict
        password = bcrypt.hashpw(password.encode(), self.salt).hex()
        user_post = DBPostCreator.create_user_post(
            email, username, password, self.get_outer_ip()
        )
        # Register the user in the server
        threading.Thread(
            target=self.server_communicator.create_user(user_post), daemon=True
        ).start()
        # Cache stats
        cache = self.cache_stats(username)
        # Close the welcome screen
        self.running = False
        # Stop all music
        for sound in self.BACKGROUND_MUSIC.values():
            sound.stop()

        MainMenu(
            user_post,
            cache,
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
