"""
Hadar Dagan
31.5.2020
v1.0
"""
import copy
from typing import List, Tuple

import pygame
from pygamepp.grid_game_object import GridGameObject
from pygamepp.grid import Grid


class Piece(GridGameObject):
    COUNTER_CLOCKWISE_TRANSFORMATION_MATRIX = ((0, -1), (1, 0))
    CLOCKWISE_TRANSFORMATION_MATRIX = ((0, 1), (-1, 0))
    RIGHT_BORDER = 9
    LEFT_BORDER = 0
    LOWER_BORDER = 19
    PIVOT_POINT: int

    def __init__(self, sprite: pygame.sprite, position: List):
        super().__init__(sprite, position, 50)

    def call_rotation_functions(self, key, grid):
        """Call the correct rotation functions according to the pressed key"""
        if key == pygame.K_x:
            self.rotate(grid, self.CLOCKWISE_TRANSFORMATION_MATRIX)
        elif key == pygame.K_z:
            self.rotate(grid, self.COUNTER_CLOCKWISE_TRANSFORMATION_MATRIX)

    def move(self, key, grid: Grid):
        """Try and move the piece according to the pressed key"""
        position_change = 0
        illegal_move = False

        if key == pygame.K_LEFT:
            position_change = -1
            for pos in self.position:
                if (pos[1] == self.LEFT_BORDER or
                        grid.blocks[pos[0]][pos[1] + position_change].occupied):
                    illegal_move = True

        if key == pygame.K_RIGHT:
            position_change = 1
            for pos in self.position:
                if (pos[1] == self.RIGHT_BORDER or
                        grid.blocks[pos[0]][pos[1] + position_change].occupied):
                    illegal_move = True

        # If the move cannot be executed
        if not illegal_move:
            for i in range(len(self.position)):
                self.position[i][1] += position_change

    def rotate(self, grid, rotation_matrix, times_failed=0):
        """Rotate the piece"""
        illegal_rotation = False
        old_positions = self.position[:]
        too_low = False
        pivot_point = self.position[self.PIVOT_POINT]
        for i in range(len(self.position)):
            self.position[i] = self.rotated_piece_position(self.position[i],
                                                           pivot_point,
                                                           rotation_matrix)
            # In case the piece will be underground after the rotation
            if self.position[i][0] > self.LOWER_BORDER:
                too_low = True

            # In case the piece will be out of bounds, or be inside another piece
            elif (self.position[i][1] < self.LEFT_BORDER
                    or self.position[i][1] > self.RIGHT_BORDER
                    or grid.blocks[self.position[i][0]][self.position[i][1]].occupied):
                illegal_rotation = True

        if too_low:
            self.position = old_positions
            # Move each block of the piece up by 1 row
            for pos in self.position:
                pos[0] -= 1
            self.rotate(grid, rotation_matrix)

        # Standard TGM wall kick rotation
        if illegal_rotation:
            self.position = old_positions
            if times_failed == 0:
                # Try to move the piece left and then rotate
                self.move(pygame.K_LEFT, grid)
                self.rotate(grid, rotation_matrix, times_failed + 1)
            elif times_failed == 1:
                # Try to move the piece right and then rotate
                self.move(pygame.K_RIGHT, grid)
                self.rotate(grid, rotation_matrix, times_failed + 1)
            elif times_failed == 2:
                # ONLY FOR THE I PIECE - triggers in case it hits the left wall and needs to be
                # pushed right again because of the pivot point position
                self.move(pygame.K_RIGHT, grid)
                self.rotate(grid, rotation_matrix, times_failed + 1)
            elif times_failed == 3:
                # ONLY FOR THE I PIECE - triggers in case it hits the right wall and needs
                # to be pushed left twice because of the pivot point position
                self.move(pygame.K_LEFT, grid)
                self.move(pygame.K_LEFT, grid)
                self.rotate(grid, rotation_matrix, times_failed + 1)

    def gravitate(self, grid: Grid):
        """Gravitate the piece"""
        self.position = self.move_down(grid, self.position)

    def move_down(self, grid: Grid, position: List[List[int]]):
        """Try and move the piece one block down"""
        illegal_move = False
        old_position = copy.deepcopy(position)
        changed_position = copy.deepcopy(position)
        for pos in changed_position:
            pos[0] += 1
            if not grid.is_a_legal_move(pos):
                illegal_move = True
        if illegal_move:
            return old_position
        return changed_position

    def get_lowest_position(self, grid: Grid):
        """Returns the lowest position the piece can get to if it retains it's current
        position on the x axis"""
        old_position = copy.deepcopy(self.position)
        changed_position = self.move_down(grid, self.position)
        while old_position != changed_position:
            old_position = changed_position
            changed_position = self.move_down(grid, changed_position)
        return changed_position

    def rotated_piece_position(self, point: List[int], pivot_point: List[int],
                               rotation_matrix: Tuple[Tuple[int, int], Tuple[int, int]]) -> List[int]:
        """Returns the final position of the rotated piece"""
        relative_vector = self.get_relative_vector(point, pivot_point)
        transformed_vector = self.get_transformed_vector(rotation_matrix, relative_vector)
        return [pivot_point[0] + transformed_vector[0], pivot_point[1] + transformed_vector[1]]

    @staticmethod
    def get_transformed_vector(rotation_matrix: Tuple[Tuple[int, int], Tuple[int, int]],
                               relative_vector: Tuple[int, int]) -> Tuple[int, int]:
        """Rotates the piece using vectors"""
        transformed_x = rotation_matrix[0][0] * relative_vector[0] + rotation_matrix[0][1] * relative_vector[1]
        transformed_y = rotation_matrix[1][0] * relative_vector[0] + rotation_matrix[1][1] * relative_vector[1]
        return transformed_x, transformed_y

    @staticmethod
    def get_relative_vector(point, pivot_point) -> Tuple[int, int]:
        """Returns the relevant vector using the piece's position and it's pivot point"""
        relative_x = point[0] - pivot_point[0]
        relative_y = point[1] - pivot_point[1]
        return relative_x, relative_y
