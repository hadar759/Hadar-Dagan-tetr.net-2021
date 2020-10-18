"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame

from pieces.tetris_piece import Piece


class IPiece(Piece):
    PIVOT_POINT = 2

    def __init__(self):
        self.sprite = pygame.image.load(r"./resources/ipiece-sprite.png")
        super().__init__(self.sprite, [[0, 4], [1, 4], [2, 4], [3, 4]])