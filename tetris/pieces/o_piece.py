from typing import List

import pygame

from .tetris_piece import Piece


class OPiece(Piece):
    def __init__(self, skin: int = 0, pos: List[List] = None):
        self.sprite = pygame.image.load(
            rf"tetris/tetris-resources/opiece-sprite{skin}.png"
        )
        if not pos:
            pos = [[0, 4], [0, 5], [1, 5], [1, 4]]
        super().__init__(self.sprite, pos)

    def call_rotation_functions(self, key, grid):
        """The O piece can't be rotated and thus the function is empty"""
        pass
