from typing import List

import pygame

from .tetris_piece import Piece


class IPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int = 0, pos: List[List] = None):
        self.sprite = pygame.image.load(rf"tetris/tetris-resources/ipiece-sprite{skin}.png")
        if not pos:
            pos = [[0, 4], [1, 4], [2, 4], [3, 4]]
        super().__init__(self.sprite, pos)
