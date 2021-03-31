import pickle
import socket
import threading
import time
from typing import Optional, Tuple, Dict

import pygame
from requests import get

from server_communicator import ServerCommunicator
from tetris.menu_screen import MenuScreen
from tetris.colors import Colors
from tetris.tetris_client import TetrisClient
from game_server import GameServer
from tetris.tetris_game import TetrisGame
from tetris.waiting_room import WaitingRoom


class MainMenu(MenuScreen):
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
        self.buttons = {}
        self.user = user
        self.skin = skin
        self.text_cursor_ticks = pygame.time.get_ticks()
        self.server_communicator = server_communicator
        self.socket = socket.socket()
        self.room_offset = 0
        self.public_room_list = []
        self.leaderboard_offset = 0

    def run(self):
        """Main loop of the main menu"""
        while True:
            self.create_menu()
            self.running = True
            old_time = round(time.time())
            threading.Thread(target=self.update_mouse_pos, daemon=True).start()

            while self.running:
                self.update_screen()

                for event in pygame.event.get():
                    # Different event, but mouse pos was initiated
                    if self.mouse_pos:
                        self.handle_events(event)

                # Display invites
                cur_time = round(time.time())
                if cur_time % 20 == 0 and cur_time != old_time:
                    old_time = cur_time
                    # threading.Thread(target=self.check_invite).start()
                    threading.Thread(target=self.check_invite, daemon=True).start()
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
            Colors.BLACK_BUTTON,
            inviter_name,
            func=self.accept_invite
        )

        x_height = 20
        x_width = 20
        self.create_button(
            (screen_corner_x, screen_corner_y - button_height),
            x_width,
            x_height,
            Colors.BLACK_BUTTON,
            "X",
            text_size=20,
            text_color=Colors.RED,
            func=self.dismiss_invite
        )

    def accept_invite(self):
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        room = {"name": "test private room", "ip": invite_ip}
        self.connect_to_room(room)

    def dismiss_invite(self):
        """Dismisses an invite from a player"""
        # TODO Do something with a declination
        inviter_name = self.server_communicator.get_invite(self.user["username"])
        invite_ip = self.server_communicator.get_invite_ip(self.user["username"])
        self.socket.send(pickle.dumps(["declined"]))
        buttons = {}
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
                buttons[button] = self.buttons[button]
        self.buttons = buttons
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
        button_width = 504
        button_height = 150
        cur_x = self.width // 2 - 258
        cur_y = self.height // 4 - button_height
        button_offset = button_height + 75
        cur_button_text = "sprint"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.YELLOW_BUTTON,
            cur_button_text,
            func=self.sprint
        )
        cur_y += button_offset

        cur_button_text = "marathon"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.DEEP_BLUE_BUTTON,
            cur_button_text,
            func=self.marathon
        )
        cur_y += button_offset

        cur_button_text = "multiplayer"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.PINKISH_BUTTON,
            cur_button_text,
            func=self.create_room_list
        )
        cur_y += button_offset

        cur_button_text = "leaderboard"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.create_leaderboard
        )




        cur_button_text = self.user["username"]
        self.create_button(
            (self.width - 300, self.height // 3 - 250),
            250,
            100,
            Colors.BLACK_BUTTON,
            cur_button_text,
            func=self.user_profile,
            args = (self.user["username"],)
        )

        self.display_buttons()

    def handle_events(self, event: pygame.event):
        """Responds to pygame events"""
        if event.type == pygame.QUIT:
            self.quit()
            pygame.quit()
            quit()

        # If the user typed something
        if event.type == pygame.KEYDOWN:
            for textbox in self.textboxes.keys():
                if textbox.active:
                    self.textbox_key_actions(textbox, event)
                    break

        # In case the user pressed the mouse button
        if event.type == self.BUTTON_PRESS:
            for button in reversed(self.buttons):
                # Check if the click is inside the button area (i.e. the button was clicked)
                # Otherwise skip
                if not button.inside_button(self.mouse_pos):
                    continue
                # Change the button color
                button.clicked(self.screen)
                # Get the correct response using to the button
                func, args = self.buttons[button]
                # User pressed a button with no response function
                if not func:
                    continue
                func(*args)
                break

            for textbox in self.textboxes.keys():
                # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                if textbox.inside_button(self.mouse_pos):
                    # Make the textbox writeable
                    textbox.active = True
                else:
                    textbox.active = False

    def quit(self):
        self.buttons = {}
        self.textboxes = {}
        self.running = False
        self.server_communicator.update_online(self.user["username"], False)

    def user_profile(self, username):
        print(f"you've entered {username}'s user profile")

    def create_leaderboard(self):
        self.buttons = {}
        self.textboxes = {}
        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, "LEADERBOARD", 70,
                           Colors.WHITE, text_only=True)

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        cur_y += title_height

        button_width = 504
        button_height = 200
        cur_x = self.width // 2 - 258
        button_offset = button_height + 75
        cur_button_text = "sprint"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard_menu
        )
        cur_y += button_offset

        cur_button_text = "marathon"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.marathon_leaderboard
        )
        cur_y += button_offset

        cur_button_text = "apm"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.apm_leaderboard
        )

    def sprint_leaderboard_menu(self):
        self.buttons = {}
        self.textboxes = {}
        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, "SPRINT LEADERBOARD", 70,
                           Colors.PURPLE, text_only=True)

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        cur_y += title_height - 15

        button_width = 504
        button_height = 150
        cur_x = self.width // 2 - 258
        button_offset = button_height + 60
        cur_button_text = "20l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(20,)
        )
        cur_y += button_offset

        cur_button_text = "40l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(40,)
        )
        cur_y += button_offset

        cur_button_text = "100l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(100,)
        )
        cur_y += button_offset

        cur_button_text = "1000l"
        self.create_button(
            (cur_x, cur_y),
            button_width,
            button_height,
            Colors.GREEN_BUTTON,
            cur_button_text,
            func=self.sprint_leaderboard,
            args=(1000,)
        )

    def sprint_leaderboard(self, line_num):
        sprint_leaderboard = self.server_communicator.get_sprint_leaderboard(line_num)
        self.display_leaderboard(sprint_leaderboard, str(line_num) + "l")

    def marathon_leaderboard(self):
        marathon_leaderboard = self.server_communicator.get_marathon_leaderboard()
        self.display_leaderboard(marathon_leaderboard, "marathon")

    def apm_leaderboard(self):
        apm_leaderboard = self.server_communicator.get_apm_leaderboard()
        self.display_leaderboard(apm_leaderboard, "apm")

    def display_leaderboard(self, user_arr, score_type):
        self.leaderboard_offset = 0

        self.buttons = {}
        self.textboxes = {}
        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, f"{score_type.upper()} LEADERBOARD", 70,
                           Colors.PURPLE, text_only=True)

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        cur_y += title_height - function_button_height - 10

        # Create the scroll up button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "↑", 55, Colors.WHITE, func=self.scroll_leaderboard_up,
                           args=(user_arr, cur_x, cur_y, score_type,))

        # Create the scroll down button
        self.create_button((self.width - function_button_width, self.height - function_button_height),
                           function_button_width,
                           function_button_height,
                           Colors.BLACK_BUTTON, "↓", 55, Colors.WHITE, func=self.scroll_leaderboard_down,
                           args=(user_arr, cur_x, cur_y, score_type,))

        self.display_leaderboard_entries(user_arr, cur_x, cur_y, score_type)

    def display_leaderboard_entries(self, user_arr, cur_x, cur_y, score_type):
        entry_width = self.width
        entry_height = 169
        score_width = 50
        score_height = 190
        position_width = 150
        cur_y += 80
        self.leaderboard_offset = min(len(user_arr) - 4, self.leaderboard_offset)
        for index, user in enumerate(user_arr[self.leaderboard_offset:self.leaderboard_offset + 4]):
            print(user)
            self.create_button((cur_x, cur_y), position_width, entry_height, Colors.BLACK_BUTTON,
                               f"{index + self.leaderboard_offset + 1}.", text_size=50, text_color=Colors.WHITE)

            self.create_button((cur_x + position_width, cur_y), entry_width, entry_height, Colors.BLACK_BUTTON,
                               " " + user["username"], text_size=50, text_color=Colors.GREEN, func=self.user_profile,
                               args=(user["username"],))

            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = last_button.get_mid_left_text_position
            self.create_button((cur_x + entry_width - score_width * 7, cur_y - 8), score_width,
                               score_height,
                               Colors.BLACK_BUTTON, str(user[score_type]), text_size=70, text_color=Colors.RED,
                               text_only=True)
            cur_y += entry_height + 10

    def scroll_leaderboard_up(self, user_arr, cur_x, cur_y, score_type):
        print(self.leaderboard_offset)
        if self.leaderboard_offset == 0:
            self.create_popup_button("Can't scroll up")
            return
        self.leaderboard_offset -= 1
        self.display_leaderboard_entries(user_arr, cur_x, cur_y, score_type)

    def scroll_leaderboard_down(self, user_arr, cur_x, cur_y, score_type):
        offset = self.leaderboard_offset
        self.leaderboard_offset = self.leaderboard_offset = min(len(user_arr) - 4, self.leaderboard_offset + 1)
        # Offset hasn't changed, i.e. we're at the end of the room list
        if offset == self.leaderboard_offset:
            self.create_popup_button("Can't scroll down more")
        else:
            self.display_leaderboard_entries(user_arr, cur_x, cur_y, score_type)


    def create_room_list(self):
        self.public_room_list = self.server_communicator.get_rooms()
        self.display_room_list_screen()

    def display_room_list_screen(self):
        # Reset the screen
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 300
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, "ROOM LIST", 70,
                           Colors.PURPLE, text_only=True)

        function_button_width = 75
        function_button_height = 75
        # Create the add room button
        self.create_button((cur_x, cur_y), function_button_width, function_button_height, Colors.BLACK_BUTTON, "+", 70,
                           Colors.WHITE, func=self.create_room)
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height, Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        cur_y += title_height - function_button_height - 10

        # Create the scroll up button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "↑", 55, Colors.WHITE, func=self.scroll_rooms_up)

        # Create the scroll down button
        self.create_button((self.width - function_button_width, self.height - function_button_height), function_button_width,
                           function_button_height,
                           Colors.BLACK_BUTTON, "↓", 55, Colors.WHITE, func=self.scroll_rooms_down)

        cur_y += 10

        self.create_button((cur_x, cur_y), function_button_width, function_button_height, Colors.BLACK_BUTTON,
                           "⟳", 70, Colors.WHITE, func=self.refresh_rooms)

        cur_y += function_button_height + 10

        self.display_rooms(cur_x, cur_y)

    def refresh_rooms(self):
        self.room_offset = 0
        self.public_room_list = self.server_communicator.get_rooms()
        self.display_room_list_screen()

    def scroll_rooms_up(self):
        if self.room_offset == 0:
            self.create_popup_button("Can't scroll up")
            return
        self.room_offset -= 1
        self.display_room_list_screen()

    def scroll_rooms_down(self):
        offset = self.room_offset
        self.room_offset = min(len(self.public_room_list) - 3, self.room_offset + 1)
        # Offset hasn't changed, i.e. we're at the end of the room list
        if offset == self.room_offset:
            self.create_popup_button("Can't scroll down more")
        else:
            self.display_room_list_screen()

    def create_room(self):
        self.buttons = {}
        self.textboxes = {}

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, cur_y), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, "CREATE A ROOM", 70,
                           Colors.PURPLE, text_only=True)
        cur_y += title_height

        textbox_width = 1000
        label_width = 300
        textbox_height = 130
        cur_x = 100
        self.create_button((cur_x, cur_y), label_width, textbox_height, Colors.BLACK_BUTTON, "Room name:", text_only=True)
        name_box = self.create_textbox((cur_x + label_width + 100, cur_y), textbox_width,
                                       textbox_height, Colors.BLACK_BUTTON, "")
        self.textboxes[name_box] = f"{self.user['username']}'s room"
        cur_y += textbox_height + 20

        self.create_button((cur_x, cur_y), label_width, textbox_height, Colors.BLACK_BUTTON, "Min apm:", text_only=True)
        name_box = self.create_textbox((cur_x + label_width + 100, cur_y), textbox_width,
                                       textbox_height, Colors.BLACK_BUTTON, "")
        self.textboxes[name_box] = "0"
        cur_y += textbox_height + 20

        self.create_button((cur_x, cur_y), label_width, textbox_height, Colors.BLACK_BUTTON, "Max apm:", text_only=True)
        name_box = self.create_textbox((cur_x + label_width + 100, cur_y), textbox_width,
                                       textbox_height, Colors.BLACK_BUTTON, "")
        self.textboxes[name_box] = "999"
        cur_y += textbox_height + 20

        self.create_button((cur_x, cur_y), label_width, textbox_height, Colors.BLACK_BUTTON, "Private:", text_only=True)
        button = self.create_button((cur_x + label_width + 100, cur_y + 40), 50, 50, Colors.BLACK_BUTTON, "❌", 45, Colors.RED)
        self.buttons[button] = (self.change_binary_button, (button,))
        cur_y += textbox_height + 20

        continue_width = label_width + 200
        self.create_button((self.width // 2 - label_width // 2, cur_y), continue_width, textbox_height, Colors.BLACK_BUTTON,
                           "CONTINUE", text_color=Colors.WHITE, func=self.create_continue)

    def create_continue(self):
        textbox_values = list(self.textboxes.values())
        room_name = textbox_values[0]
        if len(room_name) > 23:
            self.textboxes = {}
            self.buttons = {}
            self.create_room()
            self.create_popup_button("Room name too long")
            return
        min_apm = textbox_values[1]
        max_apm = textbox_values[2]
        private = not list(self.buttons.keys())[-2].text == "❌"
        if not min_apm or not max_apm or not min_apm.isdigit() or not max_apm.isdigit():
            self.textboxes = {}
            self.buttons = {}
            self.create_room()
            self.create_popup_button("Invalid settings")
            return
        min_apm = int(min_apm)
        max_apm = int(max_apm)
        self.running = False
        room_server = GameServer(self.get_inner_ip(), False, room_name, min_apm, max_apm, private, self.user["username"])
        threading.Thread(target=room_server.run).start()
        self.connect_to_room({"ip": room_server.server_ip, "name": room_server.room_name})
        self.running = True


    @staticmethod
    def get_outer_ip():
        return get("https://api.ipify.org").text

    @staticmethod
    def get_inner_ip():
        return socket.gethostbyname(socket.gethostname())

    def change_binary_button(self, button):
        if button.text == "❌":
            button.text_color = Colors.GREEN
            button.text = "✔"
        elif button.text == "✔":
            button.text_color = Colors.RED
            button.text = "❌"
        button.rendered_text = button.render_button_text()

    def connect_to_room(self, room: Dict):
        self.running = False
        sock = socket.socket()
        sock.connect((room["ip"], 44444))
        # Start the main menu
        waiting_room = WaitingRoom(self.user,
                           False, room["name"], sock, self.server_communicator,
                           self.width, self.height, 75, "resources/tetris_background.jpg"
                           )
        waiting_room.run()
        self.running = True
        threading.Thread(target=self.update_mouse_pos, daemon=True).start()
        self.display_room_list_screen()

    def multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        self.create_button(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE_BUTTON,
            "Room List",
            text_color=Colors.GREY,
            func=self.create_room_list
        )

        self.display_buttons()
        self.display_textboxes()
        pygame.display.flip()

    def display_rooms(self, cur_x, cur_y):
        room_button_width = self.width
        room_button_height = 190
        player_button_width = 50
        player_button_height = 200
        self.room_offset = min(len(self.public_room_list) - 3, self.room_offset)
        for room in self.public_room_list[self.room_offset:self.room_offset + 3]:
            print(room["name"])
            self.create_button((cur_x, cur_y), room_button_width, room_button_height, Colors.BLACK_BUTTON,
                               " ".join(list(room["name"])), text_color=Colors.WHITE, func=self.connect_to_room,
                               args=(room,))
            last_button = list(self.buttons.keys())[-1]
            last_button.get_middle_text_position = last_button.get_mid_left_text_position
            self.create_button((cur_x + room_button_width - player_button_width - 20, cur_y), player_button_width,
                               player_button_height,
                               Colors.BLACK_BUTTON, str(room["player_num"]), text_size=70, text_color=Colors.WHITE,
                               text_only=True)
            cur_y += room_button_height + 10

    def old_multiplayer(self):
        """Create the multiplayer screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.create_textbox(
            (self.width // 2 - 250, self.height // 2 - 200),
            500,
            200,
            Colors.WHITE_BUTTON,
            "Opponent Name",
            text_color=Colors.GREY,
        )

        cur_button_text = "Challenge"
        self.create_button(
            (self.width // 2 - 250, (self.height // 3) * 2),
            500,
            200,
            Colors.BLACK_BUTTON,
            cur_button_text,
#            func=self.multiplayer_continue
        )
        self.display_buttons()
        self.display_textboxes()
        pygame.display.flip()

    def sprint(self):
        """Create the sprint screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, 0), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        self.create_button(
            (self.width // 2 - 257, self.height // 8 - 85),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "20L",
            func=self.start_game,
            args=("sprint", 20)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 3 - 81),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "40L",
            func=self.start_game,
            args=("sprint", 40)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 5 - 86),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "100L",
            func=self.start_game,
            args=("sprint", 100)
        )
        self.create_button(
            (self.width // 2 - 257, self.height // 8 * 7 - 85),
            501,
            200,
            Colors.YELLOW_BUTTON,
            "1000L",
            func=self.start_game,
            args=("sprint", 1000)
        )
        self.display_buttons()
        pygame.display.flip()

    def marathon(self):
        """Create the marathon screen - set up the correct buttons"""
        self.buttons = {}
        self.reset_textboxes()
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))

        function_button_width = 75
        function_button_height = 75
        # Create the back button
        self.create_button((self.width - function_button_width, 0), function_button_width, function_button_height,
                           Colors.BLACK_BUTTON, "->", 55,
                           Colors.WHITE, func=self.quit)

        title_width = self.width
        title_height = 200
        cur_x = 0
        cur_y = 0
        # Create the screen title
        self.create_button((cur_x, cur_y), title_width, title_height, Colors.BLACK_BUTTON, "CHOOSE A STARTING LEVEL", 70,
                           Colors.WHITE, text_only=True)

        button_height = 200
        button_width = 200
        row_height = self.height // 2 - button_height
        row_starting_width = self.width // 10
        # First line of buttons
        for i in range(5):
            btn = self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.DEEP_BLUE_BUTTON,
                str(i),
                func=self.start_game,
                args=("marathon", i)
            )
            if i % 2 == 0:
                btn.color = btn.get_clicked_color(btn.color)
        # Second line of buttons
        row_height = row_height + button_height + 100
        for i in range(5):
            btn = self.create_button(
                (row_starting_width * (3 + (i - 1) * 2) - 100, row_height),
                button_width,
                button_height,
                Colors.DEEP_BLUE_BUTTON,
                str(i + 5),
                func=self.start_game,
                args=("marathon", i + 5)
            )
            if i % 2 == 1:
                btn.color = btn.get_clicked_color(btn.color)

        self.display_buttons()
        pygame.display.flip()

    def start_game(self, mode, lines_or_level):
        """Start a generic game, given a mode and the optional starting lines or starting level"""
        self.running = False
        self.buttons = {}
        self.reset_textboxes()
        game = TetrisGame(500 + 200, 1000, mode, self.server_communicator, self.user["username"], 75, lines_or_level=int(lines_or_level))
        game.run()
