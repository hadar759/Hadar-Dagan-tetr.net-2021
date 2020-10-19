import pygame

from .tetris_piece import Piece


class TPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int):
        self.sprite = pygame.image.load(rf"./resources/tpiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 4], [1, 3], [1, 4], [1, 5]])
