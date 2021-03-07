import pickle
import socket
import time
from typing import Optional, Tuple, Dict
from requests import get, post
import threading

import concurrent.futures
import pygame

from server_communicator import ServerCommunicator
from tetris.tetris_game import TetrisGame
from tetris.button import Button
from tetris.colors import Colors
from tetris.tetris_client import TetrisClient
from tetris.tetris_server import TetrisServer
from tetris.text_box import TextBox


class MainMenu:
    """The starting screen of the game"""

    GAME_PORT = 44444
    BUTTON_PRESS = pygame.MOUSEBUTTONDOWN

    def __init__(
        self,
        width: int,
        height: int,
        user: Dict,
        server_communicator: ServerCommunicator,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
        skin: int = 1,
    ):
        self.width, self.height = width, height
        self.user = user
        self.refresh_rate = refresh_rate
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background_image = (
            pygame.image.load(background_path) if background_path else None
        )
        self.buttons = []
        self.textboxes: Dict[TextBox] = {}
        self.actions = {}
        self.skin = skin
        self.running = True
        self.text_cursor_ticks = pygame.time.get_ticks()
        self.server_communicator = server_communicator
        self.socket = socket.socket()

    def run(self):
        """Main loop of the main menu"""
        while True:
            self.create_menu()
            self.running = True
            pygame.display.flip()
            run_count = 0

            while self.running:
                self.update_screen()
                mouse_pos = pygame.mouse.get_pos()
                for event in pygame.event.get():
                    self.handle_events(event, mouse_pos)
                if round(time.time()) % 10 == 0:
                    # threading.Thread(target=self.check_invite).start()
                    self.check_invite()
                run_count += 1
                pygame.display.flip()

    def check_invite(self):
        invite = self.server_communicator.get_invite(self.user["username"]).replace(
            '"', ""
        )
        if invite:
            self.display_invite(invite)

    def display_invite(self, inviter_name):
        screen_corner_x = 1500
        screen_corner_y = 600
        button_height = 300
        button_width = 200
        self.create_button(
            (screen_corner_x - button_width, screen_corner_y - button_height),
            button_width,
            button_height,
            Colors.BLACK,
            inviter_name,
        )
        self.actions["".join(letter for letter in inviter_name if letter.isalpha())] = (
            self.accept_invite,
        )
        x_height = 20
        x_width = 20
        self.create_button(
            (screen_corner_x, screen_corner_y - button_height),
            x_width,
            x_height,
            Colors.BLACK,
            "X",
            text_size=20,
            text_color=Colors.RED,
        )
        self.actions["X"] = (self.dismiss_invite,)

    def accept_invite(self):
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        self.socket.connect((invite_ip, self.GAME_PORT))
        self.socket.send(pickle.dumps(["accepted"]))
        data = pickle.loads(self.socket.recv(1024))[0]
        if data == "declined":
            return
        self.start_client_game(invite_ip, float(data))
        self.dismiss_invite()

    def dismiss_invite(self):
        """Dismisses an invite from a player"""
        inviter_name = self.server_communicator.get_invite(self.user["username"])
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        print(invite_ip)
        self.socket.connect((invite_ip, self.GAME_PORT))
        self.socket.send(pickle.dumps(["declined"]))
        buttons = []
        actions = {}
        print(inviter_name)
        for button in self.buttons:
            if button.text == "X":
                # Close the connection
                self.socket.close()
                self.socket = socket.socket()
                # Free the server
                self.server_communicator.finished_server(invite_ip)
                # Remove the invite from the DB
                self.server_communicator.dismiss_invite(self.user["username"])
                # Don't add the button to the new buttons array
                continue
            elif button.text == inviter_name:
                continue
            else:
                buttons.append(button)
                actions[button.text] = self.actions[button.text]
        print(buttons)
        print(actions)
        self.buttons = buttons
        self.actions = actions
        self.update_screen()

    def update_screen(self):
        """Displays everything needed to be displayed on the screen"""
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.display_textboxes()
        self.display_all_buttons()
        pygame.display.flip()

    def create_menu(self):
        """Creates the main menu screen and all it's components"""
        self.screen = pygame.display.set_mode((self.width, self.height))
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        # Set up the buttons and display them
        # Very specific numbers just so they exactly fill the blocks in the background pic hahaha
        cur_button_text = "sprint"
        self.create_button(
            (self.width // 2 - 258, self.height // 3 - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
        )
        self.actions[cur_button_text] = (self.sprint,)

        cur_button_text = "marathon"
        self.create_button(
            (self.width // 2 - 258, self.height // 3 * 2 - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
        )
        self.actions[cur_button_text] = (self.marathon,)

        cur_button_text = "multiplayer"
        self.create_button(
            (self.width // 2 - 258, self.height - 250),
            504,
            200,
            Colors.BLACK,
            cur_button_text,
        )
        self.actions[cur_button_text] = (self.multiplayer,)

        cur_button_text = self.user["username"]
        self.create_button(
            (self.width - 300, self.height // 3 - 250),
            250,
            100,
            Colors.BLACK,
            cur_button_text,
        )
        self.actions[cur_button_text] = (self.user_profile,)

        self.actions[""] = self.start_game, "marathon"
        self.actions["L"] = self.start_game, "sprint"

        self.display_all_buttons()

    def handle_events(self, event: pygame.event, mouse_pos: Tuple[int, int]):
        """Responds to pygame events"""
        if event.type == pygame.QUIT:
            self.running = False
            self.server_communicator.update_online(self.user["username"], False)
            pygame.quit()
            exit()

        # If the user typed something
        if event.type == pygame.KEYDOWN:
            for textbox in self.textboxes.keys():
                if textbox.active:
                    self.key_actions(textbox, event)
                    break

        # In case the user pressed the mouse button
        if event.type == self.BUTTON_PRESS:
            for button in self.buttons:
                # Check if the click is inside the button area (i.e. the button was clicked)
                # Otherwise skip
                if not button.inside_button(mouse_pos):
                    continue
                text_in_button = ""
                numbers_in_button = ""
                # Parse the text inside the button
                for char in button.text:
                    if char.isdigit():
                        numbers_in_button += char
                    elif not char.isspace():
                        text_in_button += char
                # Get the correct response using to the button
                func = self.actions.get(text_in_button)
                # User pressed a button with no response function
                if not func:
                    continue
                # The function takes no variables
                if len(func) == 1:
                    func[0]()
                # The function takes variables
                else:
                    func[0](*func[1:], numbers_in_button)

            for textbox in self.textboxes.keys():
                # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                if textbox.inside_button(mouse_pos):
                    # Make the textbox writeable
                    textbox.active = True
                else:
                    textbox.active = False

    def user_profile(self):
        print(f"you've entered {self.user['username']}'s user profile")

    def multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = []
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.create_textbox(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE,
            "Opponent Name",
            text_color=Colors.GREY,
        )

        cur_button_text = "Challenge"
        self.create_button(
            (self.width // 2 - 250, (self.height // 3) * 2),
            500,
            200,
            Colors.BLACK,
            cur_button_text,
        )
        self.actions[cur_button_text] = (self.multiplayer_continue,)
        self.display_all_buttons()
        self.display_textboxes()
        pygame.display.flip()

    def sprint(self):
        """Create the sprint screen - set up the correct buttons"""
        self.buttons = []
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.create_button(
            (self.width // 2 - 257, self.height // 8 - 85),
            501,
            200,
            Colors.BLACK,
            "20L",
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 3 - 81),
            501,
            200,
            Colors.BLACK,
            "40L",
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 5 - 86),
            501,
            200,
            Colors.BLACK,
            "100L",
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 7 - 85),
            501,
            200,
            Colors.BLACK,
            "1000L",
        )
        self.display_all_buttons()
        pygame.display.flip()

    def marathon(self):
        """Create the marathon screen - set up the correct buttons"""
        self.buttons = []
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        button_height = 200
        button_width = 200
        row_height = self.height // 2 - button_height
        row_starting_width = self.width // 10
        # First line of buttons
        for i in range(5):
            self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.BLACK,
                str(i),
            )
        # Second line of buttons
        row_height = row_height + button_height + 100
        for i in range(5):
            self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.BLACK,
                str(i + 5),
            )
        self.display_all_buttons()
        pygame.display.flip()

    def start_client_game(self, server_ip, bag_seed):
        client_game = TetrisGame(500 + 200, 1000, "multiplayer", 75)
        client_game.set_bag_seed(bag_seed)
        client = TetrisClient(client_game, server_ip, self.socket)
        client.run()

    def start_game(self, mode, lines_or_level):
        """Start a generic game, given a mode and the optional starting lines or starting level"""
        self.running = False
        self.buttons = []
        self.reset_textboxes()
        game = TetrisGame(500 + 200, 1000, mode, 75, lines_or_level=int(lines_or_level))
        game.run()

    def multiplayer_continue(self):
        foe_name = list(self.textboxes.values())[0]

        # Entered invalid foe name
        if foe_name == self.user[
            "username"
        ] or not self.server_communicator.username_exists(foe_name):
            self.create_popup_button(r"Invalid Username Entered")
            self.reset_textboxes()

        elif self.server_communicator.is_online(foe_name):
            # Get a server to play on
            server_ip = self.server_communicator.get_free_server().replace('"', "")
            # Error message
            if "server" in server_ip:
                self.create_popup_button(server_ip)
                self.reset_textboxes()
                return
            self.server_communicator.invite_user(
                self.user["username"], foe_name, server_ip
            )
            self.socket.connect((server_ip, self.GAME_PORT))
            # Accept the game on your end
            data = pickle.loads(self.socket.recv(1024))[0]
            if data != "declined":
                self.start_client_game(server_ip, float(data))
            else:
                self.socket.close()
                self.socket = socket.socket()
                self.create_popup_button("Invite declined")

        else:
            self.create_popup_button("Opponent not online")
            self.reset_textboxes()

    @staticmethod
    def get_outer_ip():
        return get("https://api.ipify.org").text

    @staticmethod
    def get_local_ip():
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

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
    ):
        """Creates a new button and appends it to the button dict"""
        self.buttons.append(
            Button(
                starting_pixel, width, height, color, text, text_size, text_color, show
            )
        )

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
        )
        # TODO change this shitty solution
        self.actions["".join(char for char in text.split() if char != " ")] = (
            self.buttons.pop,
        )
        # self.actions[text] = self.buttons.pop,

    def display_all_buttons(self):
        """Displays all buttons on the screen"""
        for button in self.buttons:
            self.show_button(button)
            self.show_text_in_button(button)

    def show_button(self, button):
        """Display a given button on the screen"""
        x = button.starting_x
        y = button.starting_y
        self.screen.fill(button.color, ((x, y), (button.width, button.height)))

    def show_text_in_button(self, button):
        """Display a given button's text"""
        self.screen.blit(button.rendered_text, button.get_text_position())

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

    @staticmethod
    def get_next_in_dict(dict: Dict, given_key):
        key_index = -999

        for index, key in enumerate(dict.keys()):
            if key == given_key:
                key_index = index

            if index == key_index + 1:
                return key
