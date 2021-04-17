from typing import List

import pygame


class GridGameObject:
    def __init__(self, sprite: pygame.sprite, position: List, block_size):
        self.sprite = sprite
        self.position = position
        self.block_size = block_size

    def display_object(self, screen: pygame.Surface):
        for pos in self.position:
            screen.blit(
                self.sprite, (pos[1] * self.block_size, pos[0] * self.block_size)
            )
