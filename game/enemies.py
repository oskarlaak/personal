import pygame
import sys


def get_enemy_info():
    class Enemy:
        type = 'Normal'

        def __init__(self, hp, speed, wandering_radius, shooting_range, accuracy,
                     damage_multiplier, memory, patience, pain_chance, shot_columns):
            self.hp = hp
            self.speed = speed
            self.wandering_radius = wandering_radius
            self.shooting_range = shooting_range  # Max shooting range
            self.accuracy = accuracy  # 0 will never hit, 1 is normal, can go higher
            self.damage_multiplier = damage_multiplier
            self.memory = memory  # Time in ticks enemy knows player's pos after player has disappeared from enemy's POV
            self.patience = patience  # Max time in ticks enemy will remain without action
            self.pain_chance = pain_chance  # From 0 tro 1, how likely player will be shown hurt when shot
            self.shot_columns = shot_columns

    class Boss:
        type = 'Boss'

        def __init__(self, hp, speed, accuracy, damage_multiplier, shot_columns):
            self.hp = hp
            self.speed = speed
            self.accuracy = accuracy
            self.damage_multiplier = damage_multiplier
            self.shot_columns = shot_columns

    try:
        # Bosses
        generalfettgesicht = pygame.image.load('../textures/enemies/generalfettgesicht.png').convert_alpha()
        gretelgrosse = pygame.image.load('../textures/enemies/gretelgrosse.png').convert_alpha()
        hansgrosse = pygame.image.load('../textures/enemies/hansgrosse.png').convert_alpha()
        hitler = pygame.image.load('../textures/enemies/hitler.png').convert_alpha()
        ottogiftmacher = pygame.image.load('../textures/enemies/ottogiftmacher.png').convert_alpha()
        # Normal enemies
        guard = pygame.image.load('../textures/enemies/guard.png').convert_alpha()
        guarddog = pygame.image.load('../textures/enemies/guarddog.png').convert_alpha()
        mutant = pygame.image.load('../textures/enemies/mutant.png').convert_alpha()
        officer = pygame.image.load('../textures/enemies/officer.png').convert_alpha()
        ss = pygame.image.load('../textures/enemies/ss.png').convert_alpha()

    except pygame.error as loading_error:
        sys.exit(loading_error)

    else:
        enemy_info = {
            ottogiftmacher:     Boss(300, 0.09, 2.00, 2.00, [4]),
            generalfettgesicht: Boss(400, 0.08, 1.00, 1.00, [2, 4, 5, 6, 7]),

            gretelgrosse:       Boss(250, 0.06, 0.50, 1.00, [2, 3, 4, 5, 6, 7]),
            hansgrosse:         Boss(450, 0.09, 1.00, 1.00, [2, 3, 4, 5, 6, 7]),
            hitler:             Boss(666, 0.07, 1.00, 1.50, [3, 4, 5, 6, 7]),

            guard:    Enemy(20, 0.07, 2,  7, 1.00, 1.00, 300,  60, 1.00, [4]),
            guarddog: Enemy( 5, 0.08, 4,  1, 9.99, 1.40, 100,   0, 0.00, [3]),
            officer:  Enemy(40, 0.08, 2, 10, 1.10, 1.00, 500,  90, 0.85, [2, 4]),
            ss:       Enemy(50, 0.06, 3, 15, 1.05, 1.10, 500, 180, 0.50, [3, 4, 5]),
            mutant:   Enemy(30, 0.07, 9, 10, 1.00, 0.60, 400, 180, 0.75, [1, 3])
        }
        return enemy_info