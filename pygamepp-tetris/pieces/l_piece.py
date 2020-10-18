"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame
from pieces.tetris_piece import Piece


class LPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self):
        self.sprite = pygame.image.load(r"./resources/lpiece-sprite.png")
        super().__init__(self.sprite, [[0, 5], [1, 5], [1, 4], [1, 3]])
