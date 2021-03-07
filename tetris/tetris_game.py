"""
Hadar Dagan
31.5.2020
v1.0
"""
import pickle
import threading
from socket import socket
from typing import Tuple, Optional, Dict, List
import random

from concurrent.futures import Executor
import pygame
from pygame import USEREVENT
from pygamepp.game import Game
from pygamepp.game_object import GameObject

from tetris.pieces import *
from tetris.pieces.tetris_piece import Piece
from tetris.tetris_grid import TetrisGrid
from tetris.colors import Colors


class TetrisGame(Game):
    # Will be displayed when users lose
    LOSE_TEXT = pygame.font.Font("./resources/joystix-monospace.ttf", 60).render(
        "YOU LOSE", True, Colors.WHITE
    )
    # Will be displayed when users win
    WIN_TEXT = pygame.font.Font("./resources/joystix-monospace.ttf", 60).render(
        "YOU WIN", True, Colors.WHITE
    )
    # Will be displayed before the score
    SCORE_TEXT = pygame.font.Font("./resources/joystix-monospace.ttf", 19).render(
        "SCORE:", True, Colors.WHITE
    )
    # Will be displayed before the time
    TIME_TEXT = pygame.font.Font("./resources/joystix-monospace.ttf", 19).render(
        "TIME:", True, Colors.WHITE
    )

    GRAVITY_EVENT = USEREVENT + 1
    DAS_EVENT = USEREVENT + 2
    ARR_EVENT = USEREVENT + 3
    MANUAL_DROP = USEREVENT + 4
    LOCK_DELAY = USEREVENT + 5
    DATA_EVENT = USEREVENT + 6
    LOWER_BORDER = 19
    # The first - base - amount of time it takes for a piece to drop one block (in ms)
    GRAVITY_BASE_TIME = 800
    BLOCK_SIZE = 50
    BASE_SCREEN_SIZE = 700
    BORDER = 100
    SCREEN_START = BASE_SCREEN_SIZE + BORDER

    def __init__(
        self,
        width: int,
        height: int,
        mode: str,
        refresh_rate: int = 60,
        background_path: Optional[str] = None,
        lines_or_level: Optional[int] = None,
        server_socket: Optional[socket] = None,
    ):
        super().__init__(width + 1000, height, refresh_rate, background_path)
        self.mode = mode
        # The current piece the player is controlling
        self.cur_piece: Piece = None
        # The ghost piece of the current piece
        self.ghost_piece: Piece = None
        # The current time it takes a piece to drop one block
        self.gravity_time = self.GRAVITY_BASE_TIME
        # Game stats
        self.lines_cleared = 0
        self.level = 0
        self.score = 0
        # Whether the current piece should be frozen
        self.should_freeze = False
        # How many 'gravity_time's the current piece touched the ground without being frozen
        self.times_touching_ground = 0
        # A bag containing the next 7 pieces - according to tetris guideline
        self.cur_seven_bag = []
        self.game_grid = TetrisGrid()
        self.grids = [self.game_grid]
        # Every variable that has to do with moving the piece
        self.move_variables: Dict[str, bool] = {
            "right_das": False,
            "left_das": False,
            "arr": False,
            "key_down": False,
            "hard_drop": False,
            "manual_drop": False,
        }
        self.skin = 0
        self.pieces_and_next_sprites = {
            "<class 'tetris.pieces.i_piece.IPiece'>": pygame.image.load(
                f"resources/ipiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.j_piece.JPiece'>": pygame.image.load(
                f"resources/jpiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.o_piece.OPiece'>": pygame.image.load(
                f"resources/opiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.l_piece.LPiece'>": pygame.image.load(
                f"resources/lpiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.t_piece.TPiece'>": pygame.image.load(
                f"resources/tpiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.s_piece.SPiece'>": pygame.image.load(
                f"resources/spiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.z_piece.ZPiece'>": pygame.image.load(
                f"resources/zpiece-full-sprite{self.skin}.png"
            ),
            "<class 'tetris.pieces.garbage_piece.GarbagePiece'>": pygame.image.load(
                rf"./resources/garbage_piece_sprite{self.skin}.png"
            ),
        }
        self.pieces = {
            "I": pygame.image.load(f"resources/ipiece-sprite{self.skin}.png"),
            "J": pygame.image.load(f"resources/jpiece-sprite{self.skin}.png"),
            "O": pygame.image.load(f"resources/opiece-sprite{self.skin}.png"),
            "L": pygame.image.load(f"resources/lpiece-sprite{self.skin}.png"),
            "T": pygame.image.load(f"resources/tpiece-sprite{self.skin}.png"),
            "S": pygame.image.load(f"resources/spiece-sprite{self.skin}.png"),
            "Z": pygame.image.load(f"resources/zpiece-sprite{self.skin}.png"),
            "G": pygame.image.load(f"resources/garbage_piece_sprite{self.skin}.png"),
        }

        if self.mode == "sprint":
            # Sprint specific variables
            self.starting_time = pygame.time.get_ticks()
            self.lines_to_finish = lines_or_level
            self.line_text = pygame.font.Font(
                "./resources/joystix-monospace.ttf", 19
            ).render("LEFT:", True, Colors.WHITE)
        if self.mode == "marathon":
            # Marathon specific variables
            self.level = lines_or_level
            self.gravity_time -= self.level * 83
            self.line_text = pygame.font.Font(
                "./resources/joystix-monospace.ttf", 19
            ).render("LINES:", True, Colors.WHITE)
        if self.mode == "multiplayer":
            # Multiplayer specific variables
            self.server_socket = server_socket
            self.lines_to_be_sent = 0
            self.lines_received = 0
            self.opp_screen = []
            self.grids.append(TetrisGrid(x_offset=self.SCREEN_START))

    def run(self):
        # Every event that has to do with moving the piece
        self.create_timer(self.GRAVITY_EVENT, self.gravity_time)
        self.set_event_handler(self.GRAVITY_EVENT, self.gravitate)
        self.create_timer(self.MANUAL_DROP, 20)
        self.set_event_handler(self.MANUAL_DROP, self.manual_drop)
        self.set_event_handler(self.DAS_EVENT, self.start_DAS)
        self.set_event_handler(self.ARR_EVENT, self.start_ARR)
        self.set_event_handler(self.LOCK_DELAY, self.freeze_piece)
        self.set_event_handler(pygame.KEYUP, self.key_up)
        self.set_event_handler(pygame.KEYDOWN, self.key_pressed)
        if self.mode == "multiplayer":
            self.create_timer(self.DATA_EVENT, 2000)
            self.set_event_handler(self.DATA_EVENT, self.handle_connection)
        self.running = True

        # Display the grid borders
        self.game_grid.display_borders(self.screen)

        super().run()

    def start_of_loop(self):
        """Every action that is to be done at the start of the loop - before event handling"""
        # Make sure we always have a current piece on the screen
        if self.cur_piece is None:
            self.generate_new_piece()
            # Clear the screen from the old next pieces
            self.reset_grids()

    @staticmethod
    def set_bag_seed(bag_seed):
        """Set the bag seed for the game, so both multiplayer games will have the same seed"""
        random.seed(bag_seed)

    def reset_grids(self):
        self.screen.fill(Colors.BLACK)
        for grid in self.grids:
            grid.display_borders(self.screen)

    def handle_connection(self):
        data = [self.get_my_screen(), self.lines_to_be_sent]
        # Send the screen & lines to be sent to the opponent
        print(len(pickle.dumps(data)))
        self.server_socket.send(pickle.dumps(data))
        self.lines_to_be_sent = 0

        # Receive the screen and line data from the opponent
        data_received = pickle.loads(self.server_socket.recv(25600))
        # Get the opponent screen
        screen_received = data_received[0]
        # Get the amount of lines to be received from the opponent
        lines_received = data_received[1]
        # In case the opponent topped out (lost)
        if screen_received == "Win":
            self.game_over(True)
        elif screen_received == "Lose":
            self.game_over(False)

        self.update_opp_screen(screen_received)
        self.lines_received += int(lines_received)

    def update_opp_screen(self, screen: List):
        """Updates the opponent's screen"""
        # TODO implement screen drawing
        block_size = self.BLOCK_SIZE
        cur_opp_screen = []
        # go over every block of the opponent's screen
        for row_index in range(len(screen)):
            for column_index in range(len(screen[0])):
                piece = screen[row_index][column_index]
                # No piece there
                if piece == "N":
                    continue
                piece_sprite = self.pieces[piece]
                # Create a game object representing the piece
                piece_obj = GameObject(
                    piece_sprite,
                    (
                        self.SCREEN_START + block_size * column_index,
                        block_size * row_index,
                    ),
                )
                cur_opp_screen.append(piece_obj)
        self.opp_screen = cur_opp_screen

    def get_my_screen(self):
        # 20 rows of 10 empty places - i.e. a default screen
        screen_list = []
        for row in range(20):
            screen_list.append([])
            for column in range(10):
                screen_list[row].append("N")

        # Populate the screen
        for obj in self.game_objects:
            if obj == self.cur_piece or obj == self.ghost_piece:
                continue
            for pos in obj.position:
                piece_str = str(type(obj)).split(".")
                piece_name = piece_str[-1][0]
                screen_list[pos[0]][pos[1]] = piece_name

        return screen_list

    def show_next_pieces(self):
        """Show 5 of the next pieces"""
        step = 200
        for i in range(5):
            cur_next_piece = self.cur_seven_bag[i]
            self.screen.blit(
                self.pieces_and_next_sprites[str(cur_next_piece)], (500, 100 + step * i)
            )

    def initialize_ghost_piece(self):
        """Create a ghost piece of the current piece""" ""
        # Remove the last ghost piece
        if self.ghost_piece in self.game_objects:
            self.game_objects.remove(self.ghost_piece)

        # Copy the current piece's type
        self.ghost_piece = type(self.cur_piece)()
        self.ghost_piece.sprite.set_alpha(255)
        self.update_ghost_position()
        self.game_objects.append(self.ghost_piece)

    def update_ghost_position(self):
        """Changes the ghost position in accordance to the current piece position"""
        if self.cur_piece:
            self.ghost_piece.position = self.cur_piece.get_lowest_position(
                self.game_grid
            )

    def end_of_loop(self):
        """Every action that is to be done at the end of the loop - after event handling"""
        if self.cur_piece:
            self.should_freeze = self.should_freeze_piece()

        elif self.mode == "multiplayer":
            # Deduct the lines received from the lines we have to send, or the other way around
            if self.lines_received > 0:
                if self.lines_received > self.lines_to_be_sent:
                    self.lines_received -= self.lines_to_be_sent
                    self.lines_to_be_sent = 0
                elif self.lines_to_be_sent > 0:
                    self.lines_to_be_sent -= self.lines_received
                    self.lines_received = 0

            # Add the garbage to the screen
            self.add_garbage()

        self.clear_lines()

        if self.mode == "marathon":
            # Marathon specific functions
            self.marathon()
            self.show_score()
            self.show_lines()

        elif self.mode == "sprint":
            # Sprint specific functions
            self.show_time()
            self.show_lines()
            if self.lines_cleared >= self.lines_to_finish:
                # If the player had cleared the amount of lines needed, he has won
                self.game_over(True)

        elif self.mode == "multiplayer":
            self.display_opp_screen()

        self.show_next_pieces()

    def display_opp_screen(self):
        """Displays the opponent's screen on the board"""
        for obj in self.opp_screen:
            obj.display_object(self.screen)

    def add_garbage(self):
        """Adds garbage to the board"""
        # Selects a random column to be the garbage's hole
        hole = random.randint(0, 10)
        # If there is no garbage to receive
        if self.lines_received == 0:
            return

        # Since we are about to move all the blocks on the screen up, we'll first unoccupy their
        # current position
        for line in self.game_grid.blocks:
            for block in line:
                block.occupied = False

        # Move every piece on the screen (except the current piece and ghost piece) the needed
        # amount of blocks up
        for piece in self.game_objects:
            if piece == self.cur_piece or piece == self.ghost_piece:
                continue
            new_pos = []
            for pos in piece.position:
                pos[0] -= self.lines_received
                if pos[0] < 0:
                    self.game_over(False)
                new_pos.append(pos)
            piece.position = new_pos

        # Create the garbage pieces and add them to the game
        for line in range(self.lines_received):
            garbage_piece = GarbagePiece(self.LOWER_BORDER - line, hole)
            self.game_objects.append(garbage_piece)

        # Reoccupy the blocks' positions
        for piece in self.game_objects:
            for pos in piece.position:
                self.game_grid.occupy_block(pos)

        # Reset the screen after the player has received garbage
        if self.lines_received > 0:
            self.reset_grids()
        # Reset the amount of lines that need to be received
        self.lines_received = 0

    def marathon(self):
        """Update the gravity time according to the current level"""
        total_time_decrease = 0
        # Tetris guideline is in frames - thus the numbers in ms will look weird
        for i in range(self.level):
            if i < 9:
                total_time_decrease += 83
            if i == 9:
                total_time_decrease += 33
            if 9 < i < 29:
                total_time_decrease += 17

        temp_gravity_time = self.GRAVITY_BASE_TIME - total_time_decrease

        # In case the player has advanced a level - i.e. the gravity time has changed
        if self.gravity_time != temp_gravity_time:
            self.gravity_time = temp_gravity_time
            self.create_timer(self.GRAVITY_EVENT, self.gravity_time)

    def generate_new_piece(self):
        """Generate a new current piece and update every variable that has to do with it"""
        self.reset_move_variables()
        self.generate_seven_bag()
        self.cur_piece = self.cur_seven_bag.pop(0)()
        self.game_objects.append(self.cur_piece)
        self.initialize_ghost_piece()

    def reset_move_variables(self):
        for key in self.move_variables:
            self.move_variables[key] = False

    def generate_seven_bag(self):
        """Generates a new, or updates the current seven bag, according to the tetris guideline"""
        seven_piece_set = [IPiece, TPiece, ZPiece, SPiece, LPiece, JPiece, OPiece]
        # A 7 bag can't contain more than 2 S pieces or Z pieces
        if self.cur_seven_bag.count(SPiece) == 2:
            seven_piece_set.remove(SPiece)
        if self.cur_seven_bag.count(ZPiece) == 2:
            seven_piece_set.remove(ZPiece)

        # Add pieces to the 7 bag until it's in the desired length
        while len(self.cur_seven_bag) < 7:
            self.cur_seven_bag.append(random.choice(seven_piece_set))

    def get_current_time_since_start(self):
        """Returns the amount of time in seconds since the game started"""
        return (pygame.time.get_ticks() - self.starting_time) // 1000

    def show_score(self):
        """Displays the current score on the screen"""
        text = self.render_input(20, str(self.score))
        self.screen.blit(self.SCORE_TEXT, (500, 10))
        self.screen.blit(text, (500 + self.SCORE_TEXT.get_rect()[2], 10))

    def show_time(self):
        """Displays the current amount of time since the start on the screen"""
        seconds = self.render_input(20, str(self.get_current_time_since_start()))
        self.screen.fill(
            0x000000,
            [
                (500 + self.line_text.get_rect()[2], 10),
                (500 + self.line_text.get_rect()[2] + 300, 40),
            ],
        )
        self.screen.blit(self.TIME_TEXT, (500, 10))
        self.screen.blit(seconds, (500 + self.line_text.get_rect()[2], 10))

    def show_lines(self):
        """Displays the amount of lines cleared on the screen"""
        lines = self.lines_cleared
        # In case we are in sprint mode - we'll display the amount of lines left till victory
        if self.mode == "sprint":
            lines = self.lines_to_finish - lines
        text = self.render_input(20, str(lines))
        self.screen.blit(self.line_text, (500, 50))
        self.screen.blit(text, (500 + self.line_text.get_rect()[2], 50))

    def hard_drop(self):
        """Hard drop a piece - move it very fast all the way to the ground"""
        # If the piece should already be frozen
        if self.should_freeze:
            self.freeze_piece()
            return
        drop = True
        # Gravitate the piece very fast until it hits the ground
        while drop:
            self.gravitate()
            self.score += 2
            if self.should_freeze_piece():
                self.freeze_piece()
                drop = False
        # Check if any lines need to be cleared
        self.clear_lines()

    def gravitate(self):
        """Gravitate the current piece one block down"""
        # If the piece doesn't need to be frozen and it's not None (i.e. we have a current piece) -
        # gravitate it down
        if not self.should_freeze and self.cur_piece:
            self.reset_grids()
            self.cur_piece.gravitate(self.game_grid)
        # In order to give the player time to react and move the piece, the piece needs to gravitate
        # down while touching the ground at least once before it's frozen
        else:
            if self.times_touching_ground > 0:
                self.freeze_piece()
                self.clear_lines()
                self.should_freeze = False
                self.times_touching_ground = 0
            else:
                self.times_touching_ground += 1

    def key_pressed(self, event: pygame.event):
        """Handle a key press and call the relevant functions"""
        if event.key == pygame.K_SPACE:
            self.hard_drop()

        elif self.cur_piece:
            if event.key == pygame.K_DOWN:
                self.key_down()
            elif event.key == pygame.K_RIGHT:
                self.key_right()
            elif event.key == pygame.K_LEFT:
                self.key_left()
            elif event.key == pygame.K_z:
                self.key_z()
            elif event.key == pygame.K_x:
                self.key_x()
            self.update_ghost_position()

    def key_down(self):
        """If the down arrow is pressed, turn on the manual drop"""
        self.move_variables["manual_drop"] = True

    def manual_drop(self):
        """Drop the piece manually one block down"""
        if self.move_variables["manual_drop"]:
            self.score += 1
            if not self.should_freeze:
                self.gravitate()

    def key_up(self):
        """In case a key is released change the relevant move variables"""
        if self.last_pressed_key == pygame.K_DOWN:
            self.move_variables["manual_drop"] = False
        # When we've released a move button, check if we've activated the other direction's das
        # before completely stopping all move variables.
        elif (
            self.last_pressed_key == pygame.K_RIGHT
            and not self.move_variables["left_das"]
            or self.last_pressed_key == pygame.K_LEFT
            and not self.move_variables["right_das"]
        ):
            for key in self.move_variables:
                self.move_variables[key] = False

    def start_ARR(self):
        """Start the ARR timer and turn on the ARR variable"""
        # ARR - tetris term
        if self.move_variables["key_down"]:
            self.move_variables["arr"] = True
            self.create_timer(self.DAS_EVENT, 30, True)

    def start_DAS(self):
        """Start the DAS"""
        # DAS - tetris term
        # If the arr timer already ended and there is a current piece to move
        if self.move_variables["arr"] and self.cur_piece:
            # Move the piece to the right every 5 milliseconds
            if self.move_variables["right_das"]:
                self.reset_grids()
                self.cur_piece.move(pygame.K_RIGHT, self.game_grid)
                self.create_timer(self.DAS_EVENT, 5, True)
            # Move the piece to the left every 5 milliseconds
            elif self.move_variables["left_das"]:
                self.reset_grids()
                self.cur_piece.move(pygame.K_LEFT, self.game_grid)
                self.create_timer(self.DAS_EVENT, 5, True)
        self.update_ghost_position()

    def key_right(self):
        """Move the piece one block to the right and start the ARR timer"""
        self.reset_grids()
        self.reset_move_variables()
        self.create_timer(self.ARR_EVENT, 100, True)
        self.move_variables["key_down"] = True
        self.move_variables["right_das"] = True
        self.cur_piece.move(pygame.K_RIGHT, self.game_grid)

    def key_left(self):
        """Move the piece to the left and start the ARR timer"""
        self.reset_grids()
        self.reset_move_variables()
        self.create_timer(self.ARR_EVENT, 100, True)
        self.move_variables["key_down"] = True
        self.move_variables["left_das"] = True
        self.cur_piece.move(pygame.K_LEFT, self.game_grid)

    def key_z(self):
        """Rotate the piece counter-clockwise"""
        self.reset_grids()
        self.cur_piece.call_rotation_functions(pygame.K_z, self.game_grid)

    def key_x(self):
        """Rotate the piece clockwise"""
        self.reset_grids()
        self.cur_piece.call_rotation_functions(pygame.K_x, self.game_grid)

    def start_lock_delay(self):
        # Lock delay - the time it takes the piece to freeze
        if self.should_freeze_piece():
            self.create_timer(self.LOCK_DELAY, self.gravity_time * 2, True)

    def freeze_piece(self):
        """Freezes the current piece"""
        self.game_grid.freeze_piece(self.cur_piece)
        self.cur_piece = None
        self.should_freeze = False

    def should_freeze_piece(self):
        """Returns whether the current piece can, and should, be frozen"""
        for pos in self.cur_piece.position:
            if pos[0] >= self.LOWER_BORDER:
                return True

            elif (
                self.game_grid.blocks[pos[0] + 1][pos[1]].occupied
                or self.game_grid.blocks[pos[0]][pos[1]].occupied
            ):
                if pos[0] <= 0:
                    self.game_over(False)
                return True
        return False

    def game_over(self, win: bool):
        """End the game"""
        if self.mode == "multiplayer":
            if not win:
                # send the opponent the message that you've lost
                self.server_socket.send(
                    pickle.dumps(
                        [
                            "W",
                        ]
                    )
                )

        if self.mode == "sprint":
            # Calculate the end time
            final_time = self.get_current_time_since_start()

        # Cinematic effects
        pygame.time.wait(1000)
        self.fade(7)

        # Display the winning text (can't win in marathon)
        if self.mode != "marathon" and win:
            self.screen.blit(
                self.WIN_TEXT,
                self.calculate_center_name_position(
                    self.screen.get_rect()[2] // 2 - self.WIN_TEXT.get_rect()[2] // 2,
                    self.screen.get_rect()[3] // 2 - self.WIN_TEXT.get_rect()[3] // 2,
                ),
            )
        # Display the losing text
        else:
            self.screen.blit(
                self.LOSE_TEXT,
                self.calculate_center_name_position(
                    self.screen.get_rect()[2] // 2 - self.LOSE_TEXT.get_rect()[2] // 2,
                    self.screen.get_rect()[3] // 2 - self.LOSE_TEXT.get_rect()[3] // 2,
                ),
            )
        pygame.display.flip()

        # Cinematic effects
        pygame.time.wait(2500)
        self.fade(7)

        # Stop the game, and load the end screen
        self.running = False
        self.background_image = pygame.image.load("resources/end-screen.png")
        self.screen = pygame.display.set_mode(
            (self.background_image.get_size()[0], self.background_image.get_size()[1])
        )
        self.screen.blit(self.background_image, (0, 0))

        # Display mode specific end stats
        if self.mode == "marathon":
            self.screen.blit(self.render_input(50, "SCORE:"), (300, 75))
            self.screen.blit(self.render_input(50, str(self.score)), (550, 75))
            self.screen.blit(self.render_input(50, f"LEVEL:{self.level}"), (300, 150))
        elif self.mode == "sprint":
            rendered_time_text = self.render_input(50, "TIME:")
            self.screen.blit(rendered_time_text, (300, 75))
            rendered_time = self.render_input(50, str(final_time))
            self.screen.blit(rendered_time, (515, 75))
            self.screen.blit(
                self.render_input(50, "Seconds"),
                (530 + rendered_time.get_rect()[2], 75),
            )

        pygame.display.flip()
        # Show the ending screen for 5 seconds
        pygame.time.wait(5000)

        self.running = False

    @staticmethod
    def render_input(font_size: int, inp):
        """Render a text given it's font and size"""
        return pygame.font.Font("./resources/joystix-monospace.ttf", font_size).render(
            inp, True, Colors.WHITE
        )

    def fade(self, delay):
        """Fade the screen"""
        fade = pygame.Surface((self.screen.get_rect()[2], self.screen.get_rect()[3]))
        fade.fill((0, 0, 0))
        for alpha in range(0, 100):
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            pygame.display.update()
            pygame.time.delay(delay)

    @staticmethod
    def calculate_center_name_position(x_space: int, y_space: int) -> Tuple[int, int]:
        """Returns the center position the text should be in"""
        return max(0, x_space), max(0, y_space)

    def clear_lines(self):
        """Clear the lines needed to be cleared"""
        num_of_lines_cleared = 0
        for index, line in enumerate(self.game_grid.blocks):
            should_clear = True
            for block in line:
                # If a block in a line isn't occupied the line shouldn't be cleared
                if not block.occupied:
                    should_clear = False
            if should_clear:
                num_of_lines_cleared += 1
                # Actually clear the line
                self.clear_line(index)

        # If there are any lines to be cleared, reset the screen
        if num_of_lines_cleared != 0:
            self.reset_grids()

        # Update the marathon level if needed
        if self.lines_cleared // 10 < (self.lines_cleared + num_of_lines_cleared) // 10:
            self.level += 1

        # Update the score according to the amount of lines cleared
        self.lines_cleared += num_of_lines_cleared
        if num_of_lines_cleared == 1:
            self.score += 40 * (self.level + 1)
        elif num_of_lines_cleared == 2:
            self.score += 100 * (self.level + 1)
        elif num_of_lines_cleared == 3:
            self.score += 300 * (self.level + 1)
        elif num_of_lines_cleared == 4:
            self.score += 1200 * (self.level + 1)

        # Update the amount of lines needed to be sent according to the amount of lines cleared
        if self.mode == "multiplayer":
            if num_of_lines_cleared == 2:
                self.lines_to_be_sent = 1
            elif num_of_lines_cleared == 3:
                self.lines_to_be_sent = 2
            elif num_of_lines_cleared >= 4:
                self.lines_to_be_sent = 4 + (num_of_lines_cleared - 4) // 2

    def clear_line(self, line_num):
        """Clear a single line"""
        for piece in self.game_objects:
            # The new generated position of the current piece
            new_pos = []
            for pos in piece.position:
                # Unoccupy the block's position
                self.game_grid.blocks[pos[0]][pos[1]].occupied = False
                if pos[0] != line_num:
                    # Move every block above the line one space down
                    if pos[0] < line_num:
                        pos[0] += 1
                    new_pos.append(pos)
            # Update the piece's position
            piece.position = new_pos
            for pos in piece.position:
                self.game_grid.occupy_block(pos)
