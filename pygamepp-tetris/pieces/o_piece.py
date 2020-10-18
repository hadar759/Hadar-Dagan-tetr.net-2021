"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame

from pieces.tetris_piece import Piece


class OPiece(Piece):
    def __init__(self):
        self.sprite = pygame.image.load(r"./resources/opiece-sprite.png")
        super().__init__(self.sprite, [[0, 4], [0, 5], [1, 5], [1, 4]])

    def call_rotation_functions(self, key, grid):
        """The O piece can't be rotated and thus the function is empty"""
        pass
