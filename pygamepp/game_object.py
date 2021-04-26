import pygame


class GameObject:
    def __init__(self, sprite: pygame.sprite, position):
        self.sprite = sprite

        self.position = position

    def display_object(self, screen):
        screen.blit(self.sprite, self.position)
