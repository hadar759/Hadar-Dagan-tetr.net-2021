import pygame
from .tetris_piece import Piece


class LPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int = 0):
        self.sprite = pygame.image.load(rf"./resources/lpiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 5], [1, 5], [1, 4], [1, 3]])
