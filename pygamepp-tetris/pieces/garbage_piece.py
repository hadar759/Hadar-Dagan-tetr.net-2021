"""
Hadar Dagan
31.5.2020
v1.0
"""
import pygame
from pygamepp.grid_game_object import GridGameObject


class GarbagePiece(GridGameObject):
    RIGHT_BORDER = 9
    LEFT_BORDER = 0
    LOWER_BORDER = 19

    def __init__(self, height: int, hole: int):
        position = []
        for i in range(self.LEFT_BORDER, self.RIGHT_BORDER + 1):
            if i != hole:
                position.append([height, i])
        sprite = pygame.image.load(r"./resources/garbage_piece_sprite.png")
        super().__init__(sprite, position, 50)
