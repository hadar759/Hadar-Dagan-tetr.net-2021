"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame
from pygamepp.grid import Grid

from tetris.colors import Colors
from tetris.pieces.tetris_piece import Piece


class TetrisGrid(Grid):
    def __init__(self, x_offset=0, y_offset=0):
        super().__init__(20, 10, 50)
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.block_size = 50

    def display_borders(self, screen: pygame.Surface):
        """Displays the border of every block in the grid"""
        for row in self.blocks:
            for block in row:
                x = self.x_offset + block.x
                y = self.y_offset + block.y

                self.draw_horizontal_line(x, y, screen)

                self.draw_vertical_line(
                    x + self.block_size, y + self.block_size, screen
                )

                # Draw the right line only if it's the first column,
                # performance sake as to not draw it many times over.
                if row[0] == block:
                    self.draw_vertical_line(x, y, screen)

    def draw_horizontal_line(self, x, y, screen):
        """Draws a horizontal block separator"""
        first_coords = [x, y]
        second_coords = [first_coords[0] + 10, first_coords[1]]
        pygame.draw.line(screen, Colors.GREY, first_coords, second_coords)

        first_coords, second_coords = second_coords, [
            first_coords[0] + self.block_size - 10,
            first_coords[1],
        ]
        pygame.draw.line(screen, Colors.DARK_GREY, first_coords, second_coords)

        first_coords = second_coords
        second_coords = [first_coords[0] + 10, first_coords[1]]
        pygame.draw.line(screen, Colors.GREY, first_coords, second_coords)

    def draw_vertical_line(self, x, y, screen):
        """Draws a vertical block separator"""
        first_coords = [x, y]
        second_coords = [first_coords[0], first_coords[1] + 10]
        pygame.draw.line(screen, Colors.GREY, first_coords, second_coords)

        first_coords, second_coords = second_coords, [
            first_coords[0],
            first_coords[1] + self.block_size - 10,
        ]
        pygame.draw.line(screen, Colors.DARK_GREY, first_coords, second_coords)

        first_coords = second_coords
        second_coords = [first_coords[0], first_coords[1] + 10]
        pygame.draw.line(screen, Colors.GREY, first_coords, second_coords)

    def reset_screen(self, screen: pygame.Surface):
        """Shows a screen containing only a grid of blocks"""
        screen.fill(Colors.BLACK)
        self.display_borders(screen)

    def freeze_piece(self, piece: Piece):
        """Freezes a piece on the grid"""
        for pos in piece.position:
            self.blocks[pos[0]][pos[1]].occupied = True
