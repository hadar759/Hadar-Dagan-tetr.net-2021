import pygame

from .tetris_piece import Piece


class OPiece(Piece):
    def __init__(self, skin: int):
        self.sprite = pygame.image.load(rf"./resources/opiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 4], [0, 5], [1, 5], [1, 4]])

    def call_rotation_functions(self, key, grid):
        """The O piece can't be rotated and thus the function is empty"""
        pass
