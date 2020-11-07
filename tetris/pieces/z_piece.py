import pygame

from .tetris_piece import Piece


class ZPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int = 0):
        self.sprite = pygame.image.load(rf"./resources/zpiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 3], [0, 4], [1, 4], [1, 5]])
