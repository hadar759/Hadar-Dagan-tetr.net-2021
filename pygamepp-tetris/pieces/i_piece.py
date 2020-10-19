import pygame

from .tetris_piece import Piece


class IPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self, skin: int):
        self.sprite = pygame.image.load(rf"./resources/ipiece-sprite{skin}.png")
        super().__init__(self.sprite, [[0, 4], [1, 4], [2, 4], [3, 4]])