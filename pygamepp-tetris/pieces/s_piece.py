"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame

from pieces.tetris_piece import Piece


class SPiece(Piece):
    PIVOT_POINT = 1

    def __init__(self):
        self.sprite = pygame.image.load(r"./resources/spiece-sprite.png")
        super().__init__(self.sprite, [[1, 3], [1, 4], [0, 4], [0, 5]])