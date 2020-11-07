import pygame

from .tetris_piece import Piece


class JPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int = 0):
        self.sprite = pygame.image.load(rf"./resources/jpiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 3], [1, 3], [1, 4], [1, 5]])
