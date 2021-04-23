import concurrent
import math
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Tuple

import pygame
from requests import get

from database.server_communicator import ServerCommunicator
from menus.button import Button
from tetris.colors import Colors
from menus.text_box import TextBox


class MenuScreen:
    REMOVE_EVENT = pygame.USEREVENT + 1
    BUTTON_PRESS = pygame.MOUSEBUTTONDOWN
    # CLICK_SOUND = pygame.mixer.Sound("../sounds/SFX_ButtonUp.mp3")
    CLICK_SOUND = pygame.mixer.Sound("sounds/se_sys_select.wav")
    CLICK_SOUND.set_volume(0.05)
    # HOVER_SOUND = pygame.mixer.Sound("../sounds/SFX_ButtonHover.mp3")
    HOVER_SOUND = pygame.mixer.Sound("sounds/se_sys_cursor2.wav")
    HOVER_SOUND.set_volume(0.05)
    POPUP_SOUND = pygame.mixer.Sound("sounds/se_sys_alert.wav")
    POPUP_SOUND.set_volume(0.2)

    def __init__(
        self,
        width: int,
        height: int,
        server_communicator: ServerCommunicator,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
    ):
        self.width, self.height = width, height
        self.refresh_rate = refresh_rate
        self.server_communicator = server_communicator
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background_image = (
            pygame.image.load(background_path) if background_path else None
        )
        self.background_path = background_path
        self.running = True
        self.loading = False
        self.inside_button = False
        self.hovered_btn_and_color = ()
        self.buttons: Dict[Button, callable] = {}
        self.textboxes: Dict[TextBox, str] = {}
        self.actions = {}
        self.mouse_pos: Optional[Tuple[int, int]] = None
        self.deleting = False

    def run_once(self):
        self.update_screen()

        for event in pygame.event.get():
            # Different event, but mouse pos was initiated
            if self.mouse_pos:
                self.handle_events(event)

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            self.quit()
            pygame.quit()
            quit()

        if event.type == self.REMOVE_EVENT:
            self.removing()

        if event.type == pygame.KEYUP:
            self.deleting = False

        # If the user typed something
        if event.type == pygame.KEYDOWN:
            for textbox in self.textboxes.keys():
                if textbox.active:
                    self.textbox_key_actions(textbox, event)
                    break

        # In case the user pressed the mouse button
        if event.type == self.BUTTON_PRESS and event.button == 1:
            for button in reversed(list(self.buttons)):
                # Check if the click is inside the button area (i.e. the button was clicked)
                # Otherwise skip
                if not button.inside_button(self.mouse_pos):
                    continue
                # Change the button color
                button.button_action(self.screen)
                # Get the correct response using to the button
                func, args = self.buttons[button]
                # User pressed a button with no response function
                if not func:
                    continue
                self.CLICK_SOUND.play(0)
                threading.Thread(target=self.show_loading, daemon=True).start()
                func(*args)
                self.loading = False
                break

            for textbox in self.textboxes.keys():
                # Check if the click is inside the textbox area (i.e. whether the textbox was clicked)
                if textbox.inside_button(self.mouse_pos):
                    # Make the textbox writeable
                    textbox.active = True
                else:
                    textbox.active = False

        # Find if we're hovered over a button
        for button in self.buttons:
            # Mouse over button
            if (
                button.inside_button(self.mouse_pos)
                and button.clickable
                and not button.text_only
                and not button.transparent
            ):
                # We were hovering over an adjacent button, and never left, just moved to this button
                button_changed = (
                    self.hovered_btn_and_color
                    and self.hovered_btn_and_color[0] != button
                )
                if (
                    not self.hovered_btn_and_color
                    or self.hovered_btn_and_color[0] != button
                ):
                    # Reverse the last button's color
                    if button_changed:
                        self.hovered_btn_and_color[
                            0
                        ].color = self.hovered_btn_and_color[1]
                    # Play sound
                    self.HOVER_SOUND.play(0)
                    # Save old button color
                    self.hovered_btn_and_color = (button, button.color)
                    # Update button
                    button.button_action(self.screen, alpha=5, reset=False)
                break
        # Mouse isn't hovered over any button
        else:
            if self.hovered_btn_and_color:
                self.hovered_btn_and_color[0].color = self.hovered_btn_and_color[1]
                self.hovered_btn_and_color = ()

    def quit(self):
        self.running = False

    @staticmethod
    def get_outer_ip():
        return get("https://api.ipify.org").text

    @staticmethod
    def get_inner_ip():
        return socket.gethostbyname(socket.gethostname())

    def create_button(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: Dict,
        text: str,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        transparent: bool = False,
        func: callable = None,
        text_only: bool = False,
        args: Tuple = (),
        border_size: int = 10,
        clickable: bool = True,
        info_text: str = "",
        info_size: int = 27,
    ):
        """Creates a new button and appends it to the button dict"""
        button = Button(
            starting_pixel,
            width,
            height,
            color,
            text,
            text_size,
            text_color,
            transparent,
            text_only,
            border_size,
            clickable,
        )
        self.buttons[button] = (func, args)

        if info_text:
            info_button_width = 50
            info_button_height = 50
            info_button = Button(
                (starting_pixel[0] + width - info_button_width, starting_pixel[1]),
                info_button_width,
                info_button_height,
                Colors.BLACK_BUTTON,
                "ⓘ",
                35,
                text_only=True,
            )
            self.buttons[info_button] = (
                self.create_popup_button,
                (info_text, info_size, Colors.BLUE),
            )

        return button

    def create_textbox(
        self,
        starting_pixel: Tuple[int, int],
        width: int,
        height: int,
        color: Dict,
        text: str,
        text_size: int = 45,
        text_color: Tuple[int, int, int] = Colors.WHITE,
        transparent: bool = False,
        text_only: bool = False,
        is_pass: bool = False,
    ) -> TextBox:
        """Creates a new textbox and appends it to the textbox dict"""
        box = TextBox(
            starting_pixel,
            width,
            height,
            color,
            text,
            text_size,
            text_color,
            transparent,
            text_only,
            is_pass,
        )
        self.textboxes[box] = ""
        return box

    def create_popup_button(self, text, size=38, color=Colors.RED):
        if color == Colors.RED:
            self.POPUP_SOUND.play(0)
        button_width = self.width // 2
        button_height = self.height // 3
        # Place the button in the middle of the screen
        mid_x_pos = self.width // 2 - (button_width // 2)

        self.create_button(
            (mid_x_pos, self.height // 2 - button_height),
            button_width,
            button_height,
            Colors.BLACK_BUTTON,
            text,
            size,
            text_color=color,
            func=self.buttons.popitem,
        )

    def removing(self):
        for textbox in self.textboxes:
            if textbox.active and self.deleting:
                # Delete from the textbox
                self.textbox_key_actions(textbox, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))

    def textbox_key_actions(self, textbox: TextBox, event: pygame.event.EventType):
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
            pygame.time.set_timer(self.REMOVE_EVENT, 300 if not self.deleting else 30)
            self.deleting = True

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
            if not button.transparent:
                if not button.text_only:
                    button.color_button(self.screen)
                button.show_text_in_button(self.screen)

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
            if not textbox.transparent:
                if not textbox.text_only:
                    textbox.color_button(self.screen)
                self.textboxes[textbox] = textbox.show_text_in_textbox(
                    self.textboxes[textbox], self.screen
                )

    def show_text_in_buttons(self):
        """Display the button's text for each of the buttons we have"""
        for button in self.buttons.keys():
            button.show_text_in_button(self.screen)

    def reset_textboxes(self):
        for textbox in self.textboxes:
            self.textboxes[textbox] = ""
            textbox.rendered_text = textbox.render_button_text(
                textbox.text, textbox.text_size, textbox.text_color
            )

    def update_screen(self, flip=True):
        """Displays everything needed to be displayed on the screen"""
        # Display the background image in case there is one
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        self.display_textboxes()
        self.display_buttons()
        self.drawings()
        if flip:
            pygame.display.flip()

    def drawings(self):
        pass

    def update_mouse_pos(self):
        while self.running:
            self.mouse_pos = pygame.mouse.get_pos()

    def show_loading(self):
        self.loading = True
        # Variables for circle drawing
        offset = 15
        radius = 200
        cycle_len = 6
        width = 15

        base_x = self.width // 2 - radius // 3
        base_y = self.height // 2 - radius // 3

        time.sleep(1)
        runs = 0
        last_updated = -999

        # Draw the circles as long as we're loading
        while self.loading and self.running:

            if (
                runs % cycle_len == cycle_len - 1 or runs % cycle_len == 0
            ) and runs != last_updated:
                self.update_screen(flip=False)
                self.fade(flip=False)

            fill = runs % cycle_len == cycle_len - 2

            self.draw_3d_circle(
                base_x, base_y, radius, width, draw_top_right=True, fill=fill
            )

            if runs % cycle_len > 0:
                self.draw_3d_circle(
                    base_x,
                    base_y + offset,
                    radius,
                    width,
                    draw_bottom_right=True,
                    fill=fill,
                )

            if runs % cycle_len > 1:
                self.draw_3d_circle(
                    base_x - offset,
                    base_y + offset,
                    radius,
                    width,
                    draw_bottom_left=True,
                    fill=fill,
                )

            if runs % cycle_len > 2:
                self.draw_3d_circle(
                    base_x - offset,
                    base_y,
                    radius,
                    width,
                    draw_top_left=True,
                    fill=fill,
                )

            pygame.display.flip()

            runs += 1
            time.sleep(1)

    def draw_3d_circle(
        self,
        base_x,
        base_y,
        radius,
        width,
        draw_top_right=False,
        draw_bottom_right=False,
        draw_bottom_left=False,
        draw_top_left=False,
        fill=False,
    ):
        pygame.draw.circle(
            self.screen,
            Colors.WHITE_BUTTON["button"],
            (base_x, base_y),
            radius,
            width,
            draw_top_right=draw_top_right,
            draw_bottom_right=draw_bottom_right,
            draw_bottom_left=draw_bottom_left,
            draw_top_left=draw_top_left,
        )
        pygame.draw.circle(
            self.screen,
            Colors.WHITE_BUTTON["upper"],
            (base_x, base_y),
            radius + width // 3,
            width // 3,
            draw_top_right=draw_top_right,
            draw_bottom_right=draw_bottom_right,
            draw_bottom_left=draw_bottom_left,
            draw_top_left=draw_top_left,
        )
        width = 0 if fill else width
        pygame.draw.circle(
            self.screen,
            Colors.WHITE_BUTTON["bottom"],
            (base_x, base_y),
            radius - width // 3 * 2,
            width // 3,
            draw_top_right=draw_top_right,
            draw_bottom_right=draw_bottom_right,
            draw_bottom_left=draw_bottom_left,
            draw_top_left=draw_top_left,
        )

    def fade(self, alpha=100, flip=True):
        """Fade the screen"""
        fade = pygame.Surface((self.screen.get_rect()[2], self.screen.get_rect()[3]))
        fade.fill((0, 0, 0))
        fade.set_alpha(alpha)
        self.screen.blit(fade, (0, 0))
        if flip:
            pygame.display.update()

    def cache_stats(self, username):
        start_time = time.time()
        cache = {}
        with ThreadPoolExecutor() as executor:
            futures = []

            cur_future = executor.submit(self.server_communicator.get_apm_leaderboard)
            futures.append(cur_future)
            cache[cur_future] = "apm_leaderboard"

            cur_future = executor.submit(
                self.server_communicator.get_marathon_leaderboard
            )
            futures.append(cur_future)
            cache[cur_future] = "marathon_leaderboard"

            cur_future = executor.submit(
                self.server_communicator.get_sprint_leaderboard, 20
            )
            futures.append(cur_future)
            cache[cur_future] = "20l_leaderboard"

            cur_future = executor.submit(
                self.server_communicator.get_sprint_leaderboard, 40
            )
            futures.append(cur_future)
            cache[cur_future] = "40l_leaderboard"

            cur_future = executor.submit(
                self.server_communicator.get_sprint_leaderboard, 100
            )
            futures.append(cur_future)
            cache[cur_future] = "100l_leaderboard"

            cur_future = executor.submit(
                self.server_communicator.get_sprint_leaderboard, 1000
            )
            futures.append(cur_future)
            cache[cur_future] = "1000l_leaderboard"

            cur_future = executor.submit(self.server_communicator.get_rooms)
            futures.append(cur_future)
            cache[cur_future] = "rooms"

            cur_future = executor.submit(
                self.server_communicator.get_user_profile, username
            )
            futures.append(cur_future)
            cache[cur_future] = "user"

        new_cache = {}

        for future in concurrent.futures.as_completed(futures):
            new_cache[cache[future]] = future.result()

        print(new_cache)
        print(f"it took: {time.time() - start_time}secs")

        return new_cache

    def change_binary_button(self, button):
        if button.text == "❌":
            button.text_color = Colors.GREEN
            button.text = "✔"
        elif button.text == "✔":
            button.text_color = Colors.RED
            button.text = "❌"
        button.rendered_text = button.render_button_text()
