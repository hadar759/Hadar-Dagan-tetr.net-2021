"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame

from pieces.tetris_piece import Piece


class JPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self):
        self.sprite = pygame.image.load(r"./resources/jpiece-sprite.png")
        super().__init__(self.sprite, [[0, 3], [1, 3], [1, 4], [1, 5]])
