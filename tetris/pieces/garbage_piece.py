import pygame
from pygamepp.grid_game_object import GridGameObject


class GarbagePiece(GridGameObject):
    RIGHT_BORDER = 9
    LEFT_BORDER = 0
    LOWER_BORDER = 19

    def __init__(self, height: int, hole: int, skin: int = 0):
        position = []
        for i in range(self.LEFT_BORDER, self.RIGHT_BORDER + 1):
            if i != hole:
                position.append([height, i])
        sprite = pygame.image.load(rf"./tetris-resources/garbage_piece_sprite{skin}.png")
        super().__init__(sprite, position, 50)
