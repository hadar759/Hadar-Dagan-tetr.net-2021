import math
import pickle
import socket
import threading
from typing import Optional, Dict

import pygame

from menus.menu_screen import MenuScreen
from tetris.tetris_client import TetrisClient
from tetris.tetris_game import TetrisGame
from tetris.colors import Colors
from menus.text_box import TextBox
from database.server_communicator import ServerCommunicator
from menus.user_profile_screen import UserProfile


class WaitingRoom(MenuScreen):
    """The starting screen of the game"""

    LETTER_SIZE = 15
    GAME_PORT = 44444

    def __init__(
        self,
        user: Dict,
        is_admin: bool,
        room_name: str,
        server_socket: socket.socket,
        server_communicator: ServerCommunicator,
        width: int,
        height: int,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        super().__init__(width, height, refresh_rate, background_path)
        self.players = {}
        self.is_admin = is_admin
        self.room_name = room_name
        self.sock = server_socket
        self.user = user
        self.server_communicator = server_communicator

        self.running = True
        self.last_message = False
        self.text_cursor_ticks = pygame.time.get_ticks()
        self.message = ""
        self.start_args = ()
        self.ready_players = []
        self.msg_textbox = None
        self.invite_btn = None

    def run(self):
        self.create_room()
        self.establish_connection()
        threading.Thread(target=self.recv_chat, daemon=True).start()
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        while self.running:
            # Start the game, and restart the waiting room once it ends
            if self.start_args:
                self.running = False
                self.start_client_game(*self.start_args)
                self.running = True
                self.start_args = ()
                self.handle_buttons_when_ready()
                for user in self.ready_players:
                    self.handle_buttons_when_ready(user)
                self.ready_players = []
                self.screen = pygame.display.set_mode((self.width, self.height))
                threading.Thread(target=self.recv_chat, daemon=True).start()
                threading.Thread(target=self.update_mouse_pos, daemon=True).start()

            self.run_once()

            #  TODO maybe make more buttons in the middle like game settings AND INVITE, and maybe make it
            #   more than 2 players

    def establish_connection(self):
        """Sends and receives the appropriate data from the server on connection"""
        # Receive the player list from the server
        self.players = pickle.loads(self.sock.recv(25600))
        # Send confirmation to server
        self.sock.send("received".encode())
        self.display_players()
        # Receive the ready players list from the server
        self.ready_players = pickle.loads(self.sock.recv(25600))
        # Display player readiness
        for user in self.ready_players:
            self.handle_buttons_when_ready(user)
        # Send the server our username
        self.sock.send(self.user["username"].encode())

    # TODO fix issue of crashing when admin leaves after game
    def challenge_player(self):
        self.buttons[self.invite_btn] = (None, ())
        foe_name = list(self.textboxes.values())[0]
        self.textboxes[(list(self.textboxes.keys()))[0]] = ""

        # Entered invalid foe name
        if (
            foe_name == self.user["username"]
            or foe_name in self.players
            or not self.server_communicator.username_exists(foe_name)
        ):
            self.create_popup_button(r"Invalid Username Entered")

        elif self.server_communicator.is_online(foe_name):
            server_ip = self.sock.getpeername()[0]

            threading.Thread(
                target=self.server_communicator.invite_user,
                args=(
                    self.user["username"],
                    foe_name,
                    server_ip,
                ),
            ).start()

        else:
            self.create_popup_button("Opponent not online")

        self.buttons[self.invite_btn] = (
            threading.Thread(target=self.challenge_player).start,
            (),
        )

    def start_client_game(self, server_ip, bag_seed):
        client_game = TetrisGame(
            500 + 200,
            1000,
            "multiplayer",
            self.server_communicator,
            self.user["username"],
            75,
        )
        client_game.set_bag_seed(bag_seed)
        client = TetrisClient(client_game, server_ip, self.sock)
        client.run()

    def recv_chat(self):
        while True:
            try:
                msg = self.sock.recv(1024).decode()
                print(msg)
            # Messages from last game (the tetris game which just ended)
            except UnicodeDecodeError:
                print("skipped")
                continue
            # Game started
            if msg == "started":
                self.sock.send("got info".encode())
                bag_seed = self.sock.recv(1024).decode()
                self.start_args = (self.sock.getpeername()[0], float(bag_seed))
                break
            # Someone readied
            elif msg[: len("Ready%")] == "Ready%":
                # Only the username
                msg = msg.replace("Ready%", "")
                if msg != self.user["username"]:
                    # Change the screen to show the ready from the user
                    self.pressed_ready(msg)
                    # Add the user to the ready players list
                    self.ready_players.append(msg)
                continue
            # Message is a player name - i.e. a player has just joined/disconnected
            elif ":" not in msg:
                if msg == "closed":
                    self.quit()
                    return
                # Player disconnected
                if msg[0] == "!":
                    self.players.pop(msg[1:])
                    wins_button = self.find_button_by_text("Wins")
                    self.buttons = {
                        button: self.buttons[button]
                        for button in self.buttons
                        if button.starting_x >= wins_button.starting_x + 80
                        or button.starting_y <= wins_button.starting_y
                    }
                    for button in self.buttons:
                        print(button.text, button.starting_y, button.starting_x)
                    self.display_players()
                    msg = f"{msg[1:]} has left the room"
                # Player joined
                else:
                    # Add the new player to the players list
                    self.players[msg] = 0
                    # Display the player's button
                    self.display_players()
                    msg = f"{msg} has entered the room"

            # last_button = list(self.buttons.keys())[-1]

            if not self.last_message:
                ref_button = self.find_button_by_text("Chat")
                cur_x = ref_button.starting_x + 15
            else:
                ref_button = self.last_message
                cur_x = ref_button.starting_x

            button_width = list(self.textboxes.keys())[1].width
            button_height = self.LETTER_SIZE * 2
            # Last button is a message
            cur_y = ref_button.starting_y + ref_button.height

            font_size = 20
            messages = []
            sentence = ""
            for word in msg.split(" "):
                rendered_sentence = pygame.font.Font(
                    "./tetris-resources/joystix-monospace.ttf", font_size
                ).render(sentence + word, True, Colors.WHITE)
                if rendered_sentence.get_rect()[2] > button_width:
                    messages.append(sentence)
                    sentence = ""
                sentence += word + " "
            messages.append(sentence.strip())
            for msg in messages:
                cur_y += button_height
                self.last_message = self.create_button(
                    (cur_x, cur_y),
                    button_width,
                    button_height,
                    Colors.BLACK_BUTTON,
                    msg + " ",
                    font_size,
                    text_only=True,
                )
            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = last_button.get_left_text_position

            pixels_out_of_bound = (
                last_button.starting_y + button_height - (self.height - 300)
            )
            # Message appears out of bounds
            if pixels_out_of_bound >= 0:
                messages = [
                    button
                    for button in self.buttons.keys()
                    if ":" in button.text or "has joined" in button.text
                ]
                num_to_remove = 0
                for msg in messages:
                    if msg.starting_y - messages[0].starting_y > pixels_out_of_bound:
                        break
                    num_to_remove += 1

                self.scroll_chat(num_to_remove)

    def scroll_chat(self, num_to_remove):
        """Scrolls the chat 1 message up"""
        message_index = 0
        messages_to_be_removed = []
        last_message = None
        height_difference = 0

        for button in self.buttons.keys():
            if ":" in button.text or "has" in button.text:
                # Removed enough messages, measure the amount of pixels we need to move up
                if last_message and message_index == num_to_remove:
                    height_difference = button.starting_y - last_message.starting_y

                # Instantiate the last_message variable
                if not last_message:
                    last_message = button

                # We encountered the start of a message
                message_index += 1

            # Remove the message
            if (
                message_index <= num_to_remove
                and last_message
                and not button.text.isdigit()
                and button.text_only
            ):
                messages_to_be_removed.append(button)

            # We removed enough, move the message up
            if (
                message_index > num_to_remove
                and not button.text.isdigit()
                and button.text_only
            ):
                button.starting_y = button.starting_y - height_difference

        # Remove the messages from the screen
        for message in messages_to_be_removed:
            self.buttons.pop(message)

    def textbox_key_actions(self, textbox: TextBox, event: pygame.event.EventType):
        textbox_text = self.textboxes[textbox]

        # Deletion
        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
            # We haven't entered any text
            if textbox_text == textbox.text:
                return
            # Last letter
            if len(textbox_text) <= 1:
                self.textboxes[textbox] = textbox.text
                if textbox is self.msg_textbox:
                    self.message = ""
            # Just regular deleting
            else:
                self.handle_deletion(textbox)

        # ENTER
        elif event.key == 13 and textbox is self.msg_textbox and self.message:
            # For some reason the last letter doesn't append to the message
            self.textboxes[textbox] = ""
            self.send_message()
            self.message = ""

        # Just regular text
        else:
            if self.textboxes[textbox] == textbox.text:
                self.textboxes[textbox] = ""
            self.textboxes[textbox] += event.unicode
            self.handle_text_action(textbox)

    def handle_text_action(self, textbox):
        text_length = textbox.rendered_text.get_rect()[2]
        # Text slipped out of textbox
        if text_length > textbox.width - self.LETTER_SIZE * 2:
            dif = text_length - textbox.width + self.LETTER_SIZE * 2
            # Remove all characters which slipped
            self.textboxes[textbox] = self.textboxes[textbox][dif // self.LETTER_SIZE :]
        # Textbox resetted, reset the message as well
        if (
            self.textboxes[textbox] == textbox.text
            or not self.textboxes[textbox]
            and textbox is self.msg_textbox
        ):
            self.message = ""
        elif textbox is self.msg_textbox:
            self.message += self.textboxes[textbox][-1]

    def handle_deletion(self, textbox):
        # Display the characters not on screen at the moment
        textbox_len = len(self.textboxes[textbox])
        # Not all of the text is displayed atm, display some of the older text
        if len(self.message) > textbox_len and textbox is self.msg_textbox:
            self.textboxes[textbox] = (
                self.message[-textbox_len - 1] + self.textboxes[textbox]
            )
        # Delete from message as well
        if textbox is self.msg_textbox:
            self.message = self.message[:-1]
        self.textboxes[textbox] = self.textboxes[textbox][:-1]

    def send_message(self):
        self.sock.send(f"{self.user['username']}: {self.message}".encode())

    def create_room(self):
        # Create the back arrow
        button_width = 445
        button_height = 215
        cur_x = 0
        cur_y = 0
        # Create the players label
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.BLACK_BUTTON,
            "Players",
            text_only=False,
            clickable=False,
        )
        cur_x += button_width

        # Create the room name label
        self.create_button(
            (cur_x, cur_y),
            button_width * 2 + 30,
            button_height,
            Colors.BLACK_BUTTON,
            self.room_name,
            text_only=False,
            clickable=False,
        )
        cur_x += button_width * 2

        # Create the chat label
        self.create_button(
            (cur_x + 30, cur_y),
            button_width - 90,
            button_height,
            Colors.BLACK_BUTTON,
            "Chat",
            text_only=False,
            clickable=False,
        )
        cur_x = 0
        cur_y += button_height

        # Create the name label
        self.create_button(
            (cur_x, cur_y),
            button_width // 3 * 2 + 25,
            button_height // 2 - 10,
            Colors.BLACK_BUTTON,
            "Name",
            text_size=45,
            text_only=False,
            clickable=False,
        )

        player_name_width = 330
        player_name_height = 100
        player_x = 0
        player_y = cur_y + button_height // 2 - 10
        x_offset = 0
        y_offset = -30
        player_win_width = 50
        player_win_height = 50
        self.create_player_buttons(
            player_x,
            x_offset,
            player_y,
            y_offset,
            player_name_width,
            player_name_height,
            player_win_width,
            player_win_height,
        )

        cur_x += button_width // 3 * 2

        # Create the wins label
        self.create_button(
            (cur_x, cur_y),
            button_width // 3 + 5,
            button_height // 2 - 10,
            Colors.BLACK_BUTTON,
            "Wins",
            text_size=30,
            text_only=False,
            clickable=False,
        )

        button_width = math.floor(button_width * 1.2)
        button_height = button_height - 50
        cur_x = self.width // 2 - button_width // 2
        cur_y = self.height - button_height
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.RED_BUTTON,
            "Ready?",
            text_size=45,
            func=self.pressed_ready,
        )

        challenge_width = 500
        challenge_height = 100
        cur_x = self.width // 2 - challenge_width // 2
        cur_y = self.height // 2 - challenge_height * 2
        self.create_textbox(
            (cur_x, cur_y),
            challenge_width,
            challenge_height,
            Colors.WHITE_BUTTON,
            "Opponent name",
            text_color=Colors.BLACK,
        )
        cur_y += challenge_height + 20

        self.invite_btn = self.create_button(
            (cur_x + challenge_width // 4, cur_y),
            challenge_width // 2,
            challenge_height,
            Colors.BLACK_BUTTON,
            "Invite",
            func=threading.Thread(target=self.challenge_player).start,
        )

        textbox_width = 360
        textbox_height = 50
        cur_x = self.width - textbox_width
        cur_y = self.height - textbox_height
        self.msg_textbox = self.create_textbox(
            (cur_x + 5, cur_y),
            textbox_width,
            textbox_height,
            Colors.BLACK_BUTTON,
            "message...",
            20,
            Colors.WHITE,
        )

        back_arrow_width = 70
        back_arrow_height = 70
        back_arrow_x = self.width - back_arrow_width - 2
        back_arrow_y = 0
        self.create_button(
            (back_arrow_x, back_arrow_y),
            back_arrow_width,
            back_arrow_height,
            Colors.BLACK_BUTTON,
            "->",
            text_size=40,
            func=self.quit,
        )

    def quit(self):
        self.sock.send("disconnect".encode())
        self.running = False
        self.sock.detach()

    def user_profile(self, username):
        profile = UserProfile(
            self.user,
            username,
            self.server_communicator,
            self.width,
            self.height,
            self.refresh_rate,
            self.background_path,
        )
        profile.run()

    def display_players(self):
        player_name_width = 295
        player_name_height = 100
        player_x = 0
        player_y = self.find_button_by_text("Name").starting_y + 300 // 2 - 10
        x_offset = 0
        y_offset = -42
        player_win_width = 150
        player_win_height = 107
        self.create_player_buttons(
            player_x,
            x_offset,
            player_y,
            y_offset,
            player_name_width,
            player_name_height,
            player_win_width,
            player_win_height,
        )

    def create_player_buttons(
        self,
        player_x,
        x_offset,
        player_y,
        y_offset,
        player_name_width,
        player_name_height,
        player_win_width,
        player_win_height,
    ):
        name_size = 45
        for player_name in self.players:
            # Check if a button for the player already exists
            player_button = self.find_button_by_text(player_name)

            # No button displays the player name, then create it
            if not player_button:
                if len(player_name) > 7:
                    name_size -= (len(player_name) - 7) * 3 + 1
                self.create_button(
                    (player_x + x_offset, player_y + y_offset),
                    player_name_width,
                    player_name_height,
                    Colors.RED_BUTTON,
                    player_name,
                    text_size=name_size,
                    func=self.user_profile,
                    args=(player_name,),
                )

                self.create_button(
                    (player_x + x_offset + player_name_width, player_y + y_offset),
                    player_win_width,
                    player_win_height,
                    Colors.BLACK_BUTTON,
                    str(self.players[player_name]),
                    text_size=45,
                    text_only=False,
                    clickable=False,
                )
            player_y += player_name_height

    def pressed_ready(self, username: str = ""):
        send_to_server = self.handle_buttons_when_ready(username)
        if send_to_server:
            self.sock.send(f"Ready%{self.user['username']}".encode())

    def handle_buttons_when_ready(self, username: str = ""):
        if username:
            for button in self.buttons.keys():
                if button.text == username:
                    if button.color == Colors.RED_BUTTON:
                        button.color = Colors.GREEN_READY_BUTTON
                    else:
                        button.color = Colors.RED_BUTTON
            return False

        color = ()
        for button in self.buttons.keys():
            if button.text == "Ready?":
                button.color = Colors.GREEN_READY_BUTTON
                color = button.color
                button.text = "Ready!"
                button.rendered_text = button.render_button_text()
                break
            elif button.text == "Ready!":
                button.color = Colors.RED_BUTTON
                color = button.color
                button.text = "Ready?"
                button.rendered_text = button.render_button_text()
                break

        # Paint the player button
        [
            button
            for button in self.buttons.keys()
            if button.text == self.user["username"]
        ][0].color = color

        return True

    def drawings(self):
        cur_button = self.find_button_by_text("Players")
        cur_x = cur_button.starting_x + cur_button.width
        cur_y = 0
        x_offset = 0
        pygame.draw.line(
            self.screen,
            Colors.BLACK,
            (cur_x + x_offset, cur_y),
            (cur_x + x_offset, self.height),
            width=10,
        )

        cur_button = self.find_button_by_text(self.room_name)
        cur_x += cur_button.width
        x_offset = 0
        pygame.draw.line(
            self.screen,
            Colors.BLACK,
            (cur_x + x_offset, cur_y),
            (cur_x + x_offset, self.height),
            width=10,
        )

        cur_button = self.find_button_by_text("Chat")
        cur_x = 0
        cur_y += cur_button.height
        pygame.draw.line(
            self.screen,
            Colors.BLACK,
            (cur_x, cur_y),
            (cur_x + cur_button.width + 15, cur_y),
            width=10,
        )

        cur_button = self.find_button_by_text("Players")
        cur_x = cur_button.starting_x
        cur_y = cur_button.height
        x_offset = 0
        y_offset = 0
        pygame.draw.line(
            self.screen,
            Colors.BLACK,
            (cur_x + x_offset, cur_y + y_offset),
            (self.width, cur_y + y_offset),
            width=10,
        )

        for button in [
            self.find_button_by_text("Name"),
            self.find_button_by_text("Wins"),
        ]:
            cur_button = button
            cur_x = cur_button.starting_x
            cur_y = cur_button.starting_y
            x_offset = 0
            y_offset = cur_button.height
            pygame.draw.line(
                self.screen,
                Colors.BLACK,
                (cur_x + x_offset, cur_y + y_offset),
                (cur_x + cur_button.width, cur_y + y_offset),
                width=10,
            )

        cur_x = cur_button.starting_x
        cur_y = cur_button.starting_y
        x_offset = 0
        y_offset = 0
        pygame.draw.line(
            self.screen,
            Colors.BLACK,
            (cur_x + x_offset, cur_y + y_offset),
            (cur_x + x_offset, self.height),
            width=10,
        )

        for player_name in self.players:
            cur_button = self.find_button_by_text(player_name)
            # Player just joined, button is being created
            if not cur_button:
                continue
            cur_x = 0
            cur_y = cur_button.starting_y + 100
            pygame.draw.line(
                self.screen,
                Colors.BLACK,
                (cur_x, cur_y),
                (cur_x + 460, cur_y),
                width=10,
            )

    def find_button_by_text(self, text):
        for button in self.buttons:
            if button.text == text:
                return button
        return None

    def update_mouse_pos(self):
        while self.running:
            self.mouse_pos = pygame.mouse.get_pos()
