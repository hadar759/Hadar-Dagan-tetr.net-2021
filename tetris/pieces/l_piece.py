from typing import List

import pygame
from .tetris_piece import Piece


class LPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int = 0, pos: List[List] = None):
        self.sprite = pygame.image.load(rf"./resources/lpiece-sprite{skin}.png")
        if not pos:
            pos = [[0, 5], [1, 5], [1, 4], [1, 3]]
        super().__init__(self.sprite, pos)
