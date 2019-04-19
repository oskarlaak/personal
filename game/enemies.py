import pygame
import sys


def get_enemy_info():
    class Enemy:
        type = 'Normal'

        def __init__(self, hp, speed, shooting_range, dist_multiplier, memory, patience, pain_chance):
            self.hp = hp
            self.speed = speed
            self.shooting_range = shooting_range  # Max shooting range
            self.dist_multiplier = dist_multiplier  # Will be multiplied with player distance before hitscan
            self.memory = memory  # Time in ticks enemy knows player's pos after player has disappeared from enemy's POV
            self.patience = patience  # Max time in ticks enemy will remain without action
            self.pain_chance = pain_chance  # From 0 to 1, how likely player will be shown hurt when shot

    class Boss:
        type = 'Boss'

        def __init__(self, hp, speed, dist_multiplier, shot_columns):
            self.hp = hp
            self.speed = speed
            self.dist_multiplier = dist_multiplier
            self.shot_columns = shot_columns

    try:
        guard = pygame.image.load('../textures/enemies/guard.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/ss.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/officer.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            guard:   Enemy(100, 0.04, 10, 1.0,  90, 120, 0.90),
            ss:      Enemy(100, 0.05, 20, 0.6, 150, 120, 0.75),
            officer: Enemy(100, 0.06, 15, 0.7, 150,  90, 0.75)
        }
        return enemy_info