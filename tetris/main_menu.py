import pickle
import socket
import time
from typing import Optional, Tuple, Dict

import pygame

from server_communicator import ServerCommunicator
from tetris.tetris_screen import TetrisScreen
from tetris.colors import Colors
from tetris.tetris_client import TetrisClient
from tetris.tetris_game import TetrisGame


class MainMenu(TetrisScreen):
    """The starting screen of the game"""

    GAME_PORT = 44444
    BUTTON_PRESS = pygame.MOUSEBUTTONDOWN

    def __init__(
        self,
        user: Dict,
        server_communicator: ServerCommunicator,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
        skin: int = 1,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.user = user
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
        self.display_buttons()
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

        self.display_buttons()

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
                    self.textbox_key_actions(textbox, event)
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
        self.display_buttons()
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
        self.display_buttons()
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
        self.display_buttons()
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
